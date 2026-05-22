"""
services/pdf_generator.py  v1.0.0
Locked template — JARVIS title_company gig.
Branded PDF generation for saved sheets. Uses reportlab.

The PDF layout matches the HubCityTitleAgent spec §11:
  HEADER: Company logo + name + contact, right side agent info
  PROPERTY: Address, client name, dates
  BODY: Itemized line items grouped by category
  TOTALS BOX: Sale price / net proceeds (seller) or purchase / cash to close (buyer)
  REISSUE CALLOUT: If reissue discount applied
  FOOTER: Disclaimer + generated-by line
"""
import io
import logging
from decimal import Decimal
from typing import Any, Dict, List, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

logger = logging.getLogger(__name__)


def _fmt_money(value: Any) -> str:
    """Format any numeric-ish value as $X,XXX.XX."""
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
    """Convert '#RRGGBB' hex to reportlab Color. Falls back on invalid input."""
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


class PdfGeneratorError(Exception):
    """PDF generation failed."""
    pass


class PdfGenerator:
    """
    Produces branded net-sheet / buyer-estimate PDFs.

    Usage:
        buf = PdfGenerator().render_sheet(sheet_dict, company_dict, agent_dict)
        # buf is a BytesIO, ready to return with Content-Type: application/pdf
    """

    def render_sheet(
        self,
        sheet: Dict[str, Any],
        company: Dict[str, Any],
        agent: Optional[Dict[str, Any]] = None,
    ) -> io.BytesIO:
        """Build a branded PDF for one saved sheet. Returns seek(0)'d BytesIO."""
        try:
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=LETTER,
                leftMargin=0.6 * inch,
                rightMargin=0.6 * inch,
                topMargin=0.6 * inch,
                bottomMargin=0.6 * inch,
            )
            brand_primary = _hex_to_rl_color(company.get("primary_color"))
            brand_secondary = _hex_to_rl_color(company.get("secondary_color"), fallback="#f59e0b")

            story: List[Any] = []
            styles = getSampleStyleSheet()
            heading = ParagraphStyle(
                "heading",
                parent=styles["Heading1"],
                textColor=brand_primary,
                spaceAfter=6,
            )
            subheading = ParagraphStyle(
                "subheading",
                parent=styles["Heading3"],
                textColor=brand_primary,
                spaceAfter=4,
            )
            normal = styles["Normal"]
            small = ParagraphStyle("small", parent=normal, fontSize=8, textColor=colors.grey)
            big_total = ParagraphStyle(
                "big_total",
                parent=styles["Heading1"],
                alignment=2,
                textColor=brand_primary,
                fontSize=20,
            )

            # HEADER
            company_name = company.get("company_name") or "Title Company"
            left_lines = [f"<b>{company_name}</b>"]
            for field in ("phone", "email", "website"):
                val = company.get(field)
                if val:
                    left_lines.append(str(val))
            left_block = Paragraph("<br/>".join(left_lines), normal)

            right_lines: List[str] = []
            if agent:
                name = agent.get("full_name") or agent.get("name")
                if name:
                    right_lines.append(f"<b>{name}</b>")
                for field in ("brokerage_name", "license_number", "phone"):
                    val = agent.get(field)
                    if val:
                        right_lines.append(str(val))
            right_block = Paragraph("<br/>".join(right_lines) or "&nbsp;", normal)

            header_tbl = Table(
                [[left_block, right_block]],
                colWidths=[3.6 * inch, 3.6 * inch],
            )
            header_tbl.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LINEBELOW", (0, 0), (-1, 0), 2, brand_primary),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ]))
            story.append(header_tbl)
            story.append(Spacer(1, 8))

            # SHEET TITLE
            sheet_type = sheet.get("sheet_type", "seller_net_sheet")
            title_text = "Seller Net Sheet" if sheet_type == "seller_net_sheet" else "Buyer Closing Estimate"
            story.append(Paragraph(title_text, heading))

            # PROPERTY BLOCK
            prop_lines = []
            if sheet.get("property_address"):
                prop_lines.append(f"<b>Property:</b> {sheet['property_address']}")
            if sheet.get("client_name"):
                prop_lines.append(f"<b>Client:</b> {sheet['client_name']}")
            if prop_lines:
                story.append(Paragraph("<br/>".join(prop_lines), normal))
                story.append(Spacer(1, 8))

            # LINE ITEMS
            output = sheet.get("output_data") or {}
            line_items = output.get("line_items") or []
            story.append(Paragraph("Itemized Costs", subheading))

            rows = [["Item", "Amount"]]
            for li in line_items:
                label = li.get("label", "")
                amount = li.get("amount")
                rows.append([label, _fmt_money(amount)])

            items_tbl = Table(rows, colWidths=[4.8 * inch, 2.0 * inch])
            items_tbl.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), brand_primary),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
            ]))
            story.append(items_tbl)
            story.append(Spacer(1, 10))

            # REISSUE CALLOUT
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

            # TOTALS
            if sheet_type == "seller_net_sheet":
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
            totals_rows.append([f"<b>{big_label}</b>", _fmt_money(big_value)])
            totals_tbl = Table(totals_rows, colWidths=[4.8 * inch, 2.0 * inch])
            totals_tbl.setStyle(TableStyle([
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("LINEABOVE", (0, -1), (-1, -1), 1.5, brand_primary),
                ("FONTSIZE", (0, -1), (-1, -1), 13),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ("TEXTCOLOR", (0, -1), (-1, -1), brand_primary),
                ("TOPPADDING", (0, -1), (-1, -1), 6),
            ]))
            story.append(totals_tbl)
            story.append(Spacer(1, 18))

            # BIG NET PROCEEDS display
            story.append(Paragraph(_fmt_money(big_value), big_total))
            story.append(Spacer(1, 18))

            # FOOTER DISCLAIMER
            disclaimer = company.get("disclaimer_text") \
                or "This is an estimate. Actual figures may vary at closing."
            story.append(Paragraph(disclaimer, small))
            story.append(Spacer(1, 4))
            story.append(Paragraph(f"Generated by {company_name}", small))

            doc.build(story)
            buffer.seek(0)
            return buffer
        except Exception as e:
            logger.error("PDF render failed: %s", e)
            raise PdfGeneratorError(f"PDF render failed: {e}") from e


def get_pdf_generator() -> PdfGenerator:
    """FastAPI dependency — stateless."""
    return PdfGenerator()
