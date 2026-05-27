"""
services/pdf_generator.py  v2.2.0
Dual-branded PDF — title company logo + agent headshot.
v2.2.0: Compact single-page layout. Signature inline after totals.
v2.1.0: Render client signature (base64 PNG) on PDF if present.
v2.0.0: Added company logo image, agent headshot image, dual-brand header.
        Fetch remote images via urllib, render with reportlab Image.
v1.0.0: Initial text-only branded PDF.
"""
import base64
import io
import logging
import tempfile
import urllib.request
from decimal import Decimal
from typing import Any, Dict, List, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

logger = logging.getLogger(__name__)


def _fmt_money(value: Any) -> str:
    if value is None:
        return "$0.00"
    try:
        d = Decimal(str(value)).quantize(Decimal("0.01"))
    except Exception:
        return str(value)
    sign = "-" if d < 0 else ""
    abs_d = abs(d)
    return f"{sign}${abs_d:,.2f}"


def _hex_to_rl_color(hex_str: Optional[str], fallback: str = "#1e3a8a") -> colors.Color:
    try:
        h = (hex_str or fallback).lstrip("#")
        if len(h) != 6:
            h = fallback.lstrip("#")
        r = int(h[0:2], 16) / 255.0
        g = int(h[2:4], 16) / 255.0
        b = int(h[4:6], 16) / 255.0
        return colors.Color(r, g, b)
    except Exception:
        return colors.HexColor(fallback)


def _fetch_image_to_temp(url: str, max_size: int = 2 * 1024 * 1024) -> Optional[str]:
    """Download image URL or decode base64 data URL to a temp file. Returns path or None."""
    if not url:
        return None
    # Handle base64 data URLs (from profile photo upload)
    if url.startswith("data:image"):
        try:
            header, b64data = url.split(",", 1)
            img_bytes = base64.b64decode(b64data)
            suffix = ".jpg"
            if "png" in header:
                suffix = ".png"
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            tmp.write(img_bytes)
            tmp.close()
            return tmp.name
        except Exception:
            return None
    if not url.startswith("http"):
        return None
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "TitleFlow/2.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read(max_size)
        if len(data) < 100:
            return None
        suffix = ".jpg"
        if data[:4] == b"\x89PNG":
            suffix = ".png"
        elif data[:4] == b"GIF8":
            suffix = ".gif"
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        tmp.write(data)
        tmp.close()
        return tmp.name
    except Exception as e:
        logger.debug("Could not fetch image %s: %s", url[:80], e)
        return None


class PdfGeneratorError(Exception):
    pass


class PdfGenerator:
    """Produces dual-branded net-sheet / buyer-estimate PDFs."""

    def render_sheet(
        self,
        sheet: Dict[str, Any],
        company: Dict[str, Any],
        agent: Optional[Dict[str, Any]] = None,
    ) -> io.BytesIO:
        try:
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=LETTER,
                leftMargin=0.5 * inch,
                rightMargin=0.5 * inch,
                topMargin=0.4 * inch,
                bottomMargin=0.4 * inch,
            )
            brand_primary = _hex_to_rl_color(company.get("primary_color"))
            brand_secondary = _hex_to_rl_color(company.get("secondary_color"), fallback="#f59e0b")

            story: List[Any] = []
            styles = getSampleStyleSheet()
            heading = ParagraphStyle(
                "heading", parent=styles["Heading1"],
                textColor=brand_primary, spaceAfter=4, fontSize=16,
            )
            subheading = ParagraphStyle(
                "subheading", parent=styles["Heading3"],
                textColor=brand_primary, spaceAfter=2, fontSize=10,
            )
            normal = styles["Normal"]
            small = ParagraphStyle("small", parent=normal, fontSize=7, textColor=colors.grey)
            big_total = ParagraphStyle(
                "big_total", parent=styles["Heading1"],
                alignment=2, textColor=brand_primary, fontSize=16,
            )

            # ── HEADER — Company (left) + Agent (right) ──
            # Company side: logo + name + contact
            company_name = company.get("company_name") or "Title Company"
            company_elements: List[Any] = []

            logo_path = _fetch_image_to_temp(company.get("logo_url"))
            if logo_path:
                try:
                    company_elements.append(Image(logo_path, width=1.2 * inch, height=0.6 * inch))
                except Exception:
                    pass

            left_lines = [f"<b>{company_name}</b>"]
            for field in ("phone", "email", "website", "address"):
                val = company.get(field)
                if val:
                    left_lines.append(str(val))
            company_elements.append(Paragraph("<br/>".join(left_lines), normal))
            left_block = company_elements

            # Agent side: headshot next to name/brokerage/phone (right-aligned)
            agent_elements: List[Any] = []
            if agent:
                headshot_path = _fetch_image_to_temp(agent.get("avatar_url"))
                headshot_img = None
                if headshot_path:
                    try:
                        headshot_img = Image(headshot_path, width=0.8 * inch, height=0.8 * inch)
                    except Exception:
                        pass

                right_lines: List[str] = []
                name = agent.get("full_name") or agent.get("name")
                if name:
                    right_lines.append(f"<b>{name}</b>")
                brokerage = agent.get("brokerage_name")
                if brokerage:
                    right_lines.append(f"<i>{brokerage}</i>")
                for field in ("license_number", "phone", "email"):
                    val = agent.get(field)
                    if val:
                        right_lines.append(str(val))
                agent_text = Paragraph(
                    "<br/>".join(right_lines),
                    ParagraphStyle("agent_info", parent=normal, alignment=2, fontSize=9)
                ) if right_lines else None

                if headshot_img and agent_text:
                    # Side by side: headshot | text
                    agent_row = Table(
                        [[headshot_img, agent_text]],
                        colWidths=[1.0 * inch, 2.2 * inch],
                    )
                    agent_row.setStyle(TableStyle([
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 0),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ]))
                    agent_elements.append(agent_row)
                elif agent_text:
                    agent_elements.append(agent_text)
                elif headshot_img:
                    agent_elements.append(headshot_img)

            # Build header as a table: left = company, right = agent
            # Stack elements vertically in each cell using nested Table
            def _stack(elements: List[Any]) -> Any:
                if not elements:
                    return Paragraph("&nbsp;", normal)
                if len(elements) == 1:
                    return elements[0]
                rows = [[e] for e in elements]
                t = Table(rows, colWidths=[3.4 * inch])
                t.setStyle(TableStyle([
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ]))
                return t

            header_tbl = Table(
                [[_stack(left_block), _stack(agent_elements)]],
                colWidths=[3.8 * inch, 3.4 * inch],
            )
            header_tbl.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                ("LINEBELOW", (0, 0), (-1, 0), 2, brand_primary),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ]))
            story.append(header_tbl)
            story.append(Spacer(1, 4))

            # ── SHEET TITLE ──
            sheet_type = sheet.get("sheet_type", "seller")
            if "seller" in sheet_type:
                title_text = "Seller Net Sheet"
            elif "buyer" in sheet_type:
                title_text = "Buyer Closing Estimate"
            else:
                title_text = "Net Sheet"
            story.append(Paragraph(title_text, heading))

            # ── PROPERTY BLOCK ──
            prop_lines = []
            if sheet.get("property_address"):
                prop_lines.append(f"<b>Property:</b> {sheet['property_address']}")
            if sheet.get("client_name"):
                prop_lines.append(f"<b>Client:</b> {sheet['client_name']}")
            inp = sheet.get("input_data") or {}
            if inp.get("closing_date"):
                prop_lines.append(f"<b>Closing Date:</b> {inp['closing_date']}")
            county_name = inp.get("county_name")
            if county_name:
                prop_lines.append(f"<b>County:</b> {county_name}")
            if prop_lines:
                story.append(Paragraph("<br/>".join(prop_lines), normal))
                story.append(Spacer(1, 4))

            # ── LINE ITEMS ──
            output = sheet.get("output_data") or {}
            line_items = output.get("line_items") or []
            story.append(Paragraph("Itemized Costs", subheading))

            rows = [["Item", "Amount"]]
            for li in line_items:
                label = li.get("label", "")
                amount = li.get("amount")
                rows.append([label, _fmt_money(amount)])

            items_tbl = Table(rows, colWidths=[5.0 * inch, 2.0 * inch])
            items_tbl.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), brand_primary),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]))
            story.append(items_tbl)
            story.append(Spacer(1, 6))

            # ── REISSUE CALLOUT ──
            reissue = output.get("reissue_savings")
            if reissue and Decimal(str(reissue)) > 0:
                story.append(Paragraph(
                    f"<b>Reissue Rate Applied:</b> your seller saves "
                    f"{_fmt_money(reissue)} due to prior title insurance on this property.",
                    ParagraphStyle(
                        "reissue", parent=normal,
                        backColor=brand_secondary, textColor=colors.white,
                        borderPadding=6, leading=14,
                    ),
                ))
                story.append(Spacer(1, 8))

            # ── TOTALS ──
            if "seller" in sheet_type:
                totals = [
                    ("Sale Price", output.get("sale_price")),
                    ("Total Closing Costs", output.get("total_closing_costs")),
                    ("Loan Payoff", output.get("loan_payoff")),
                ]
                big_label = "NET PROCEEDS"
                big_value = output.get("net_proceeds")
            else:
                totals = [
                    ("Purchase Price", output.get("purchase_price")),
                    ("Down Payment", output.get("down_payment")),
                    ("Total Closing Costs", output.get("total_closing_costs")),
                ]
                big_label = "CASH TO CLOSE"
                big_value = output.get("cash_to_close")

            totals_rows = [[label, _fmt_money(val)] for label, val in totals]
            totals_rows.append([big_label, _fmt_money(big_value)])
            totals_tbl = Table(totals_rows, colWidths=[5.0 * inch, 2.0 * inch])
            totals_tbl.setStyle(TableStyle([
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("LINEABOVE", (0, -1), (-1, -1), 1.5, brand_primary),
                ("FONTSIZE", (0, 0), (-1, -2), 10),
                ("FONTSIZE", (0, -1), (-1, -1), 13),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ("TEXTCOLOR", (0, -1), (-1, -1), brand_primary),
                ("TOPPADDING", (0, -1), (-1, -1), 4),
            ]))
            story.append(totals_tbl)
            story.append(Spacer(1, 6))

            # ── BIG NET PROCEEDS ──
            story.append(Paragraph(_fmt_money(big_value), big_total))
            story.append(Spacer(1, 8))

            # ── CLIENT SIGNATURE ──
            client_sig = sheet.get("client_signature")
            if client_sig:
                try:
                    # Strip data URL prefix if present
                    sig_data = client_sig
                    if "," in sig_data:
                        sig_data = sig_data.split(",", 1)[1]
                    sig_bytes = base64.b64decode(sig_data)
                    sig_tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
                    sig_tmp.write(sig_bytes)
                    sig_tmp.close()

                    # Signature block with line and X
                    sig_img = Image(sig_tmp.name, width=2.0 * inch, height=0.6 * inch)
                    sig_line_data = [
                        [sig_img, ''],
                        ['X _______________________________________', ''],
                    ]
                    sig_tbl = Table(sig_line_data, colWidths=[3.5 * inch, 3.5 * inch])
                    sig_tbl.setStyle(TableStyle([
                        ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
                        ('LEFTPADDING', (0, 0), (-1, -1), 0),
                        ('TOPPADDING', (0, 0), (-1, -1), 0),
                        ('BOTTOMPADDING', (0, 0), (0, 0), 0),
                        ('BOTTOMPADDING', (0, 1), (0, 1), 2),
                        ('FONTNAME', (0, 1), (0, 1), 'Helvetica'),
                        ('FONTSIZE', (0, 1), (0, 1), 10),
                    ]))
                    story.append(sig_tbl)
                    signed_at = sheet.get("signed_at")
                    if signed_at:
                        sig_date = str(signed_at)[:19] if len(str(signed_at)) > 19 else str(signed_at)
                        story.append(Paragraph(f"Signed: {sig_date} | Signer: {sheet.get('client_name', '')}", small))
                    story.append(Spacer(1, 6))
                except Exception as sig_err:
                    logger.debug("Could not render signature: %s", sig_err)
            else:
                # Unsigned: show empty signature line
                story.append(Spacer(1, 20))
                story.append(Paragraph("X _______________________________________", normal))
                story.append(Paragraph("Client Signature", small))

            # ── FOOTER ──
            disclaimer = company.get("disclaimer_text") \
                or "This is an estimate. Actual figures may vary at closing."
            story.append(Paragraph(disclaimer, small))
            story.append(Spacer(1, 4))
            agent_credit = ""
            if agent and agent.get("full_name"):
                agent_credit = f" | Prepared by {agent['full_name']}"
            story.append(Paragraph(
                f"Generated by {company_name}{agent_credit}",
                small,
            ))

            doc.build(story)
            buffer.seek(0)
            return buffer
        except Exception as e:
            logger.error("PDF render failed: %s", e)
            raise PdfGeneratorError(f"PDF render failed: {e}") from e


def get_pdf_generator() -> PdfGenerator:
    return PdfGenerator()
