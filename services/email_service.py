"""
services/email_service.py  v1.0.0
Locked template — JARVIS title_company gig.
SMTP email notifications via aiosmtplib. Graceful failure: if SMTP is not
configured (env vars missing) or send fails, we log and return False — we
never raise into the request handler.

The four email types match the HubCityTitleAgent spec §12:
  - Agent registration → admin notification
  - Admin approves agent → agent welcome
  - Title order submitted → formatted email to company.order_submission_email
  - Order status change → email to agent
"""
import logging
import os
from email.message import EmailMessage
from typing import Any, Dict, Optional

try:
    import aiosmtplib  # type: ignore
    AIOSMTPLIB_AVAILABLE = True
except ImportError:
    AIOSMTPLIB_AVAILABLE = False

logger = logging.getLogger(__name__)


class EmailError(Exception):
    """Email send failed."""
    pass


class EmailService:
    """
    Thin SMTP wrapper. Reads SMTP settings from environment variables:
      SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, FROM_EMAIL, BASE_URL

    Every public method returns bool — True on success, False on any
    error or misconfiguration. Never raises.
    """

    def __init__(self) -> None:
        self.host = os.environ.get("SMTP_HOST", "")
        self.port = int(os.environ.get("SMTP_PORT", "587") or "587")
        self.user = os.environ.get("SMTP_USER", "")
        self.password = os.environ.get("SMTP_PASSWORD", "")
        self.from_email = os.environ.get("FROM_EMAIL", "noreply@example.com")
        self.base_url = os.environ.get("BASE_URL", "http://localhost:8000")

    def _configured(self) -> bool:
        """True only if SMTP host is set."""
        return bool(self.host) and AIOSMTPLIB_AVAILABLE

    async def _send(self, to: str, subject: str, body: str) -> bool:
        """Raw async send. Returns True on success."""
        if not self._configured():
            logger.warning("SMTP not configured — skipping email to %s", to)
            return False
        if not to:
            logger.warning("Recipient email missing — skipping")
            return False
        try:
            msg = EmailMessage()
            msg["From"] = self.from_email
            msg["To"] = to
            msg["Subject"] = subject
            msg.set_content(body)
            kwargs: Dict[str, Any] = {
                "hostname": self.host,
                "port": self.port,
                "start_tls": self.port == 587,
                "use_tls": self.port == 465,
            }
            if self.user and self.password:
                kwargs["username"] = self.user
                kwargs["password"] = self.password
            await aiosmtplib.send(msg, **kwargs)
            logger.info("Email sent to %s: %s", to, subject)
            return True
        except Exception as e:
            logger.error("Email send failed to %s: %s", to, e)
            return False

    async def notify_new_agent(
        self,
        agent: Dict[str, Any],
        company: Dict[str, Any],
    ) -> bool:
        """Admin notification — a new agent has registered and is pending approval."""
        to = company.get("order_submission_email") or company.get("email") or ""
        name = agent.get("full_name") or agent.get("email") or "Unknown agent"
        subject = f"New agent pending approval: {name}"
        body = (
            f"A new agent has registered for access and is awaiting approval.\n\n"
            f"Name: {name}\n"
            f"Email: {agent.get('email', '')}\n"
            f"Brokerage: {agent.get('brokerage_name', '')}\n"
            f"License: {agent.get('license_number', '')}\n"
            f"Phone: {agent.get('phone', '')}\n"
            f"Referral source: {agent.get('referral_source', '')}\n\n"
            f"Review and approve at: {self.base_url}/admin/agents\n"
        )
        return await self._send(to, subject, body)

    async def notify_agent_approved(
        self,
        agent: Dict[str, Any],
        company: Dict[str, Any],
    ) -> bool:
        """Welcome email after admin approval."""
        to = agent.get("email") or ""
        company_name = company.get("company_name") or "the title company"
        subject = f"You're approved to use {company_name}'s closing tool"
        body = (
            f"Welcome!\n\n"
            f"Your account has been approved. You can now log in at "
            f"{self.base_url}/login and start generating net sheets and "
            f"buyer estimates branded with {company_name}.\n\n"
            f"Every sheet you save and share is a step toward your next closing.\n\n"
            f"— {company_name}\n"
        )
        return await self._send(to, subject, body)

    async def notify_order_submitted(
        self,
        order: Dict[str, Any],
        agent: Optional[Dict[str, Any]],
        company: Dict[str, Any],
    ) -> bool:
        """Title company receives a new order. Sends to order_submission_email."""
        to = company.get("order_submission_email") or company.get("email") or ""
        order_type = order.get("order_type", "purchase")
        address = order.get("property_address", "(address not provided)")
        subject = f"New {order_type} order: {address}"
        agent_block = ""
        if agent:
            agent_block = (
                f"\nAgent: {agent.get('full_name', '')} "
                f"({agent.get('brokerage_name', '')})\n"
                f"Agent email: {agent.get('email', '')}\n"
                f"Agent phone: {agent.get('phone', '')}\n"
            )
        body = (
            f"A new title order has been submitted.\n\n"
            f"Order type: {order_type}\n"
            f"Property address: {address}\n"
            f"Seller: {order.get('seller_name', '')}\n"
            f"Seller email: {order.get('seller_email', '')}\n"
            f"Buyer: {order.get('buyer_name', '')}\n"
            f"Buyer email: {order.get('buyer_email', '')}\n"
            f"Lender: {order.get('lender_name', '')}\n"
            f"Loan officer: {order.get('loan_officer_name', '')}\n"
            f"Estimated closing: {order.get('estimated_closing_date', '')}\n"
            f"Notes: {order.get('notes', '')}\n"
            f"{agent_block}"
            f"\nView in admin: {self.base_url}/admin/orders\n"
        )
        return await self._send(to, subject, body)

    async def notify_order_status_change(
        self,
        order: Dict[str, Any],
        agent: Dict[str, Any],
        company: Dict[str, Any],
    ) -> bool:
        """Agent is notified when title company changes order status."""
        to = agent.get("email") or ""
        status = order.get("status", "updated")
        address = order.get("property_address", "(address not provided)")
        subject = f"Order update: {address} — {status}"
        company_name = company.get("company_name") or "the title company"
        body = (
            f"Your title order at {address} is now: {status}\n\n"
            f"Questions? Contact {company_name} at "
            f"{company.get('phone', '')} or {company.get('email', '')}.\n\n"
            f"View in dashboard: {self.base_url}/orders\n"
        )
        return await self._send(to, subject, body)


def get_email_service() -> EmailService:
    """FastAPI dependency — stateless."""
    return EmailService()
