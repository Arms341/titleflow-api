"""
services/title_calculator.py  v2.5.0
Locked template — JARVIS title_company gig.
CORE BUSINESS LOGIC — 11 calculators, all Decimal math.

v2.5.0: Custom fees — admin-defined flat/percent fees per company.
  Stored in fee_settings.custom_fees array. Applied to seller, buyer, or both.
v2.4.0: Toggleable national features behind seller_toggles in fee_settings.
  reissue_discount: looks up reissue_discounts table, applies % off owner premium.
  title_search_fee: adds configurable title search fee to seller costs.
  All toggles default OFF for Lee (Hub City), ON for national white-label.
v2.3.0: Wire calculator to read fees from company.fee_settings (admin-configurable).
  seller_net_sheet + buyer_estimate now load fees from DB, fall back to hardcoded defaults.
  TDI 2025 premium table stays hardcoded (state law).
v2.2.0: TDI 2025 Basic Premium Rates (Commissioner's Order 2025-9125, effective July 1, 2025).
  Hardcoded 151-row lookup table + 7-tier excess formula replaces database bracket lookup.
  10% reduction from prior rates.
v2.1.0: Seller net sheet fixes per Lee:
  - No reissue rate discount on sale
  - No title search fee on sale
  - Doc prep = $150 deed + $50 release if payoff exists
v2.0.0: Added TruValue, BuyerCompensation, BuyNowVsLater, PriceVsRate,
  ExtraPayment, ScenarioCompare. Tax proration + HUD-1 fee corrections.

Calculators: seller_net_sheet, buyer_estimate, sell_vs_rent, holding_cost,
  buydown, truvalue, buyer_compensation, buy_now_vs_later, price_vs_rate,
  extra_payment, scenario_compare
"""
import json
import logging
from datetime import date as _date_type
from decimal import Decimal
from typing import List, Optional

from database import get_db
from fastapi import Depends
from models.county import County
from models.saved_sheet import SavedSheet
from schemas.calculator import (
    AmortizationPoint,
    BuydownInput, BuydownResult, BuydownYear,
    BuyerCompensationInput, BuyerCompensationResult, CompensationScenario,
    BuyerEstimateInput, BuyerEstimateResult,
    BuyNowCurrentScenario, BuyNowFutureScenario, BuyNowVsLaterInput, BuyNowVsLaterResult,
    ExtraPaymentInput, ExtraPaymentResult, PayoffSavings, PayoffScenario,
    HoldingCostInput, HoldingCostResult,
    LineItem,
    PriceVsRateCell, PriceVsRateInput, PriceVsRateResult,
    ScenarioCompareInput, ScenarioCompareResult, ScenarioOfferInput,
    SellerNetSheetInput, SellerNetSheetResult,
    SellVsRentInput, SellVsRentResult, SellVsRentYear,
    TruValueInput, TruValueResult, TruValueScenario,
)
from services.rate_table_service import RateTableService
from sqlalchemy import select
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Fee constants — from real Hub City Title HUD-1 (file 260527, 3/17/2026)
TITLE_SEARCH_FEE = Decimal("175.00")
DEED_PREP_FEE = Decimal("150.00")
RELEASE_PREP_FEE = Decimal("50.00")
DOC_PREP_FEE = Decimal("50.00")
TAX_CERT_FEE = Decimal("10.00")
E_RECORDING_FEE = Decimal("19.35")
E_RECORDING_FEE_BUYER = Decimal("6.45")
TX_POLICY_GUARANTY_FEE = Decimal("2.00")
APPRAISAL_FEE = Decimal("550.00")
CREDIT_REPORT_FEE = Decimal("35.00")
FLOOD_CERT_FEE = Decimal("20.00")
FHA_UFMIP_RATE = Decimal("0.0175")
VA_FUNDING_FEE_RATE = Decimal("0.0215")
ORIGINATION_RATE = Decimal("0.01")
DEFAULT_PER_DIEM_INTEREST_RATE = Decimal("0.065")
CENT = Decimal("0.01")
ZERO = Decimal("0")

# ── TDI 2025 Basic Premium Rates (effective July 1, 2025) ──
# Source: Commissioner's Order No. 2025-9125, Exhibit A
# 10% reduction from prior rates. Same table for Owner's + Lender's policies.
_TDI_2025_TABLE = (
    (25000,295),(25500,298),(26000,302),(26500,304),(27000,306),(27500,309),
    (28000,312),(28500,315),(29000,320),(29500,322),(30000,325),(30500,328),
    (31000,331),(31500,334),(32000,337),(32500,340),(33000,343),(33500,347),
    (34000,349),(34500,353),(35000,356),(35500,358),(36000,361),(36500,365),
    (37000,367),(37500,371),(38000,374),(38500,377),(39000,379),(39500,383),
    (40000,385),(40500,390),(41000,392),(41500,395),(42000,398),(42500,401),
    (43000,403),(43500,407),(44000,410),(44500,413),(45000,417),(45500,419),
    (46000,422),(46500,426),(47000,428),(47500,430),(48000,435),(48500,438),
    (49000,441),(49500,444),(50000,446),(50500,449),(51000,451),(51500,455),
    (52000,459),(52500,463),(53000,464),(53500,468),(54000,471),(54500,473),
    (55000,476),(55500,479),(56000,483),(56500,486),(57000,489),(57500,492),
    (58000,496),(58500,498),(59000,500),(59500,504),(60000,508),(60500,511),
    (61000,514),(61500,516),(62000,519),(62500,523),(63000,525),(63500,528),
    (64000,532),(64500,535),(65000,537),(65500,540),(66000,544),(66500,548),
    (67000,551),(67500,552),(68000,555),(68500,559),(69000,562),(69500,564),
    (70000,568),(70500,572),(71000,575),(71500,577),(72000,580),(72500,583),
    (73000,586),(73500,589),(74000,592),(74500,596),(75000,599),(75500,601),
    (76000,604),(76500,607),(77000,610),(77500,613),(78000,617),(78500,620),
    (79000,624),(79500,625),(80000,628),(80500,632),(81000,635),(81500,637),
    (82000,640),(82500,644),(83000,648),(83500,650),(84000,653),(84500,656),
    (85000,659),(85500,662),(86000,664),(86500,669),(87000,672),(87500,674),
    (88000,677),(88500,680),(89000,684),(89500,686),(90000,689),(90500,692),
    (91000,696),(91500,699),(92000,701),(92500,705),(93000,707),(93500,711),
    (94000,712),(94500,716),(95000,721),(95500,724),(96000,725),(96500,728),
    (97000,732),(97500,735),(98000,738),(98500,742),(99000,744),(99500,747),
    (100000,749),
)
# Excess tiers: (max_face, subtract, multiply_by, add)
_TDI_2025_EXCESS = (
    (1000000, 100000, Decimal("0.00474"), Decimal("749")),
    (5000000, 1000000, Decimal("0.00390"), Decimal("5018")),
    (15000000, 5000000, Decimal("0.00321"), Decimal("20606")),
    (25000000, 15000000, Decimal("0.00229"), Decimal("52736")),
    (50000000, 25000000, Decimal("0.00137"), Decimal("75596")),
    (100000000, 50000000, Decimal("0.00124"), Decimal("109796")),
    (None, 100000000, Decimal("0.00112"), Decimal("171896")),
)


def _tdi_2025_premium(face_value: Decimal) -> Decimal:
    """Calculate title insurance basic premium per TDI 2025 schedule."""
    fv = int(_to_decimal(face_value))
    if fv <= 0:
        return ZERO
    if fv < 25000:
        return Decimal("295")  # minimum premium
    if fv <= 100000:
        # Lookup: find smallest bracket >= face_value
        for max_val, premium in _TDI_2025_TABLE:
            if fv <= max_val:
                return Decimal(str(premium))
        return Decimal("749")  # $100,000 cap
    # Excess formula for > $100,000
    for max_face, subtract, multiply, add in _TDI_2025_EXCESS:
        if max_face is None or fv <= max_face:
            excess = Decimal(str(fv - subtract))
            return (excess * multiply).quantize(Decimal("1")) + add
    return ZERO


def _to_decimal(v) -> Decimal:
    if v is None:
        return ZERO
    if isinstance(v, Decimal):
        return v
    return Decimal(str(v))


def _round_cents(v: Decimal) -> Decimal:
    return _to_decimal(v).quantize(CENT)


def _monthly_payment(principal: Decimal, annual_rate_pct: Decimal, term_years: int) -> Decimal:
    """Standard amortization monthly payment."""
    p = _to_decimal(principal)
    ar = _to_decimal(annual_rate_pct) / Decimal("100")
    if ar == ZERO or term_years == 0:
        return p / Decimal(max(1, term_years * 12))
    mr = ar / Decimal("12")
    n = term_years * 12
    # (1+r)^n
    f = Decimal("1")
    opr = Decimal("1") + mr
    for _ in range(n):
        f *= opr
    d = Decimal("1") - (Decimal("1") / f)
    return p * mr / d if d != ZERO else p / Decimal(n)


class CalculatorError(Exception):
    pass


# ── Fee settings loader — reads company.fee_settings, merges with defaults ──
_FEE_DEFAULTS = {
    "deed_prep_fee": 150.00,
    "release_prep_fee": 50.00,
    "tax_cert_fee": 10.00,
    "e_recording_fee_seller": 19.35,
    "e_recording_fee_buyer": 6.45,
    "guaranty_fee": 2.00,
    "default_per_diem_rate_pct": 6.5,
    "appraisal_fee": 550.00,
    "credit_report_fee": 35.00,
    "flood_cert_fee": 20.00,
    "title_search_fee_amount": 175.00,
}


def _load_fee_settings(db: Session) -> dict:
    """Load fee_settings from company singleton, merged with hardcoded defaults.
    Returns dict with float values for each fee key.
    """
    merged = dict(_FEE_DEFAULTS)
    try:
        from models.company import Company
        row = db.execute(select(Company).limit(1)).scalars().first()
        if row and row.fee_settings:
            stored = json.loads(row.fee_settings) if isinstance(row.fee_settings, str) else row.fee_settings
            if isinstance(stored, dict):
                merged.update(stored)
    except Exception as e:
        logger.debug("Could not load fee_settings, using defaults: %s", e)
    return merged


class TitleCalculatorService:

    def __init__(self, rate_table_service: Optional[RateTableService] = None):
        self._db: Optional[Session] = None
        self._rate_service = rate_table_service

    def _rate(self, db: Session) -> RateTableService:
        if self._rate_service is None:
            self._rate_service = RateTableService()
        self._rate_service._db = db
        return self._rate_service

    def _get_county(self, county_id: int, db: Session) -> County:
        county = db.get(County, county_id)
        if county is None:
            raise CalculatorError(f"County {county_id} not found")
        return county

    # -----------------------------------------------------------------------
    # 1. Seller Net Sheet
    # -----------------------------------------------------------------------
    def seller_net_sheet(self, data: SellerNetSheetInput, db: Session = None) -> SellerNetSheetResult:
        db = db if db is not None else getattr(self, "_db", None)
        try:
            # Load admin-configurable fees (falls back to hardcoded defaults)
            fees = _load_fee_settings(db)
            fee_deed_prep = _to_decimal(fees.get("deed_prep_fee", 150.00))
            fee_release_prep = _to_decimal(fees.get("release_prep_fee", 50.00))
            fee_tax_cert = _to_decimal(fees.get("tax_cert_fee", 10.00))
            fee_e_recording = _to_decimal(fees.get("e_recording_fee_seller", 19.35))
            fee_guaranty = _to_decimal(fees.get("guaranty_fee", 2.00))
            fee_per_diem_default = _to_decimal(fees.get("default_per_diem_rate_pct", 6.5)) / Decimal("100")

            county = self._get_county(data.county_id, db)
            rate = self._rate(db)
            sale_price = _to_decimal(data.sale_price)
            loan_balance = _to_decimal(data.existing_loan_balance)
            seller_pct = _to_decimal(data.seller_agent_commission_pct)
            buyer_pct = _to_decimal(data.buyer_agent_commission_pct)
            seller_commission = sale_price * seller_pct / Decimal("100")
            buyer_commission = sale_price * buyer_pct / Decimal("100")
            total_commission = seller_commission + buyer_commission

            owner_title_base = ZERO
            if county.owner_rate_table_id is not None:
                owner_title_base = _tdi_2025_premium(sale_price)
            owner_title_premium = owner_title_base

            # ── Toggleable national features ──
            seller_toggles = fees.get("seller_toggles", {})

            # Reissue discount (if toggled on and prior policy info provided)
            reissue_savings = ZERO
            if seller_toggles.get("reissue_discount", False) and data.prior_title_insurance and data.years_since_prior_policy:
                try:
                    from models.reissue_discount import ReissueDiscount
                    discount_row = db.execute(
                        select(ReissueDiscount)
                        .where(ReissueDiscount.rate_table_id == county.owner_rate_table_id)
                        .where(ReissueDiscount.years_since_prior_policy >= data.years_since_prior_policy)
                        .order_by(ReissueDiscount.years_since_prior_policy.asc())
                        .limit(1)
                    ).scalars().first()
                    if discount_row:
                        discount_pct = _to_decimal(discount_row.discount_pct) / Decimal("100")
                        reissue_savings = owner_title_base * discount_pct
                        owner_title_premium = owner_title_base - reissue_savings
                except Exception as re_err:
                    logger.debug("Reissue discount lookup failed: %s", re_err)

            # Title search fee (if toggled on)
            title_search = _to_decimal(fees.get("title_search_fee_amount", 175.00)) if seller_toggles.get("title_search_fee", False) else ZERO

            # Apply seller_toggles — toggled OFF = fee not charged, not shown
            recording_fee = _to_decimal(county.recording_fee_flat) if seller_toggles.get("recording_fee", True) else ZERO
            transfer_tax = (sale_price * _to_decimal(county.transfer_tax_rate_pct) / Decimal("100")) if seller_toggles.get("transfer_tax", True) else ZERO
            fee_tax_cert = fee_tax_cert if seller_toggles.get("tax_cert", True) else ZERO
            fee_e_recording = fee_e_recording if seller_toggles.get("e_recording", True) else ZERO
            fee_guaranty = fee_guaranty if seller_toggles.get("guaranty_fee", True) else ZERO

            # Doc prep: deed + release if there's a payoff (fees from settings)
            seller_doc_prep = fee_deed_prep
            if loan_balance > ZERO:
                seller_doc_prep = seller_doc_prep + fee_release_prep

            closing_fee = _to_decimal(county.closing_fee_flat) / Decimal("2")
            survey_fee = (_to_decimal(county.survey_fee_flat) if data.include_survey else ZERO) if seller_toggles.get("survey", True) else ZERO
            home_warranty = (_to_decimal(data.home_warranty_amount) if data.include_home_warranty else ZERO) if seller_toggles.get("home_warranty", True) else ZERO
            per_diem_rate = _to_decimal(data.loan_payoff_per_diem_rate) if data.loan_payoff_per_diem_rate is not None else fee_per_diem_default
            per_diem_interest = ((loan_balance * per_diem_rate / Decimal("365")) * Decimal("30")) if seller_toggles.get("per_diem_interest", True) else ZERO
            hoa_payoff = _to_decimal(data.hoa_payoff)
            seller_concessions = _to_decimal(data.seller_concessions)
            miscellaneous = _to_decimal(data.miscellaneous_fees)

            # ── Custom fees (admin-defined per company) ──
            custom_fees_list = fees.get("custom_fees", [])
            custom_seller_total = ZERO
            custom_seller_items: List[LineItem] = []
            for cf in custom_fees_list:
                if not isinstance(cf, dict):
                    continue
                side = cf.get("side", "seller")
                if side not in ("seller", "both"):
                    continue
                label = cf.get("label", "Custom Fee")
                fee_type = cf.get("type", "flat")
                amount = _to_decimal(cf.get("amount", 0))
                if fee_type == "percent":
                    computed = sale_price * amount / Decimal("100")
                else:
                    computed = amount
                if computed > ZERO:
                    pct_note = f" ({amount}%)" if fee_type == "percent" else ""
                    custom_seller_total += computed
                    custom_seller_items.append(LineItem(label=f"{label}{pct_note}", amount=_round_cents(computed), category="custom"))

            # Tax proration
            annual_taxes = _to_decimal(data.annual_property_taxes)
            tax_proration = ZERO
            proration_note = None
            if annual_taxes > ZERO and data.closing_date:
                jan1 = _date_type(data.closing_date.year, 1, 1)
                days_owned = (data.closing_date - jan1).days
                days_in_year = 366 if (data.closing_date.year % 4 == 0 and (data.closing_date.year % 100 != 0 or data.closing_date.year % 400 == 0)) else 365
                daily_rate = annual_taxes / Decimal(str(days_in_year))
                tax_proration = daily_rate * Decimal(str(days_owned))
                proration_note = f"Jan 1 to {data.closing_date.strftime('%m/%d/%Y')} ({days_owned} days)"

            total_seller_costs = (
                total_commission + owner_title_premium + closing_fee + recording_fee
                + transfer_tax + survey_fee + home_warranty + per_diem_interest
                + seller_doc_prep + fee_tax_cert + fee_e_recording
                + fee_guaranty + tax_proration + hoa_payoff
                + seller_concessions + miscellaneous + title_search
                + custom_seller_total
            )
            net_proceeds = sale_price - loan_balance - total_seller_costs

            line_items: List[LineItem] = [
                LineItem(label=f"Seller Agent Commission ({seller_pct}%)", amount=_round_cents(seller_commission), category="commissions"),
                LineItem(label=f"Buyer Agent Commission ({buyer_pct}%)", amount=_round_cents(buyer_commission), category="commissions"),
                LineItem(label="Owner's Title Policy", amount=_round_cents(owner_title_base), category="title"),
            ]
            if reissue_savings > ZERO:
                line_items.append(LineItem(label=f"Reissue Rate Discount ({data.years_since_prior_policy}yr)", amount=_round_cents(-reissue_savings), category="title"))
            if title_search > ZERO:
                line_items.append(LineItem(label="Title Search Fee", amount=_round_cents(title_search), category="title"))
            line_items.extend([
                LineItem(label="Title Closing Fee (split)", amount=_round_cents(closing_fee), category="title"),
                LineItem(label="Deed Prep" + (" + Release" if loan_balance > ZERO else ""), amount=_round_cents(seller_doc_prep), category="title"),
            ])
            if recording_fee > ZERO:
                line_items.append(LineItem(label="Recording Fee", amount=_round_cents(recording_fee), category="government"))
            if transfer_tax > ZERO:
                line_items.append(LineItem(label="Transfer Tax", amount=_round_cents(transfer_tax), category="government"))
            if fee_tax_cert > ZERO:
                line_items.append(LineItem(label="Tax Certificates", amount=_round_cents(fee_tax_cert), category="government"))
            if fee_e_recording > ZERO:
                line_items.append(LineItem(label="E-Recording Fee", amount=_round_cents(fee_e_recording), category="government"))
            if fee_guaranty > ZERO:
                line_items.append(LineItem(label="TX Policy Guaranty Fee", amount=_round_cents(fee_guaranty), category="title"))
            if tax_proration > ZERO:
                line_items.append(LineItem(label="Property Tax Proration", amount=_round_cents(tax_proration), category="government", note=proration_note))
            if home_warranty > ZERO:
                line_items.append(LineItem(label="Home Warranty", amount=_round_cents(home_warranty), category="other"))
            if survey_fee > ZERO:
                line_items.append(LineItem(label="Survey", amount=_round_cents(survey_fee), category="other"))
            if per_diem_interest > ZERO:
                line_items.append(LineItem(label="Per Diem Interest (est. 30 days)", amount=_round_cents(per_diem_interest), category="other"))
            if hoa_payoff > ZERO:
                line_items.append(LineItem(label="HOA Payoff", amount=_round_cents(hoa_payoff), category="other"))
            if seller_concessions > ZERO:
                line_items.append(LineItem(label="Seller Concessions", amount=_round_cents(seller_concessions), category="other"))
            if miscellaneous > ZERO:
                line_items.append(LineItem(label="Miscellaneous Fees", amount=_round_cents(miscellaneous), category="other"))
            line_items.extend(custom_seller_items)

            result = SellerNetSheetResult(
                net_proceeds=_round_cents(net_proceeds), sale_price=_round_cents(sale_price),
                loan_payoff=_round_cents(loan_balance), total_closing_costs=_round_cents(total_seller_costs),
                total_commission=_round_cents(total_commission), owner_title_premium=_round_cents(owner_title_premium),
                reissue_savings=_round_cents(reissue_savings), tax_proration=_round_cents(tax_proration),
                line_items=line_items, order_ready=True,
            )
            if data.save:
                try:
                    import uuid
                    sheet = SavedSheet(sheet_type="seller_net_sheet", property_address=data.property_address,
                        property_city=data.property_city, client_name=data.client_name, county_id=data.county_id,
                        input_data=data.model_dump(mode="json"), output_data=result.model_dump(mode="json"),
                        share_token=uuid.uuid4().hex)
                    db.add(sheet); db.commit(); db.refresh(sheet)
                    result.saved_sheet_id = sheet.id
                except Exception as save_err:
                    db.rollback(); logger.error("Failed to save sheet: %s", save_err)
            return result
        except CalculatorError:
            raise
        except Exception as e:
            logger.error("seller_net_sheet failed: %s", e)
            raise CalculatorError(f"seller_net_sheet failed: {e}") from e

    # -----------------------------------------------------------------------
    # 2. Buyer Estimate
    # -----------------------------------------------------------------------
    def buyer_estimate(self, data: BuyerEstimateInput, db: Session = None) -> BuyerEstimateResult:
        db = db if db is not None else getattr(self, "_db", None)
        try:
            # Load admin-configurable fees (falls back to hardcoded defaults)
            fees = _load_fee_settings(db)
            fee_tax_cert = _to_decimal(fees.get("tax_cert_fee", 10.00))
            fee_e_recording_buyer = _to_decimal(fees.get("e_recording_fee_buyer", 6.45))

            county = self._get_county(data.county_id, db)
            rate = self._rate(db)
            pp = _to_decimal(data.purchase_price)
            la = _to_decimal(data.loan_amount)
            ir = _to_decimal(data.interest_rate)
            at = _to_decimal(data.annual_property_taxes)
            ai = _to_decimal(data.annual_homeowners_insurance)
            mi = int(data.months_insurance_prepaid)
            mt = int(data.months_tax_escrow)
            sc = _to_decimal(data.seller_paid_closing_costs)
            lt = (data.loan_type or "conventional").lower()
            is_cash = lt == "cash"
            dp = pp - la if not is_cash else pp

            # Title fees
            ltp = ZERO
            if not is_cash and county.lender_rate_table_id is not None and la > ZERO:
                ltp = _tdi_2025_premium(la)
            cf = _to_decimal(county.closing_fee_flat) / Decimal("2")
            rf = _to_decimal(county.recording_fee_flat)
            escrow_fee = _to_decimal(data.escrow_fee)
            doc_prep = _to_decimal(data.doc_prep_buyer)

            # Title endorsements
            t19 = _to_decimal(data.t19_endorsement) if not is_cash else ZERO
            survey_cover = _to_decimal(data.survey_cover_endorsement) if not is_cash else ZERO
            t17 = _to_decimal(data.t17_endorsement) if not is_cash else ZERO
            t36 = _to_decimal(data.t36_endorsement) if not is_cash else ZERO
            t30 = _to_decimal(data.t30_endorsement) if not is_cash else ZERO

            # Lender fees
            misc_lender = _to_decimal(data.misc_lender_fees) if not is_cash else ZERO
            af = _to_decimal(data.appraisal_fee) if not is_cash else ZERO
            cr = _to_decimal(data.credit_report_fee) if not is_cash else ZERO

            # Inspections
            survey = _to_decimal(data.survey_fee)
            pest = _to_decimal(data.pest_inspection_fee)
            home_insp = _to_decimal(data.home_inspection_fee)

            # Government/loan fees
            fha = la * FHA_UFMIP_RATE if lt == "fha" else ZERO
            va = la * VA_FUNDING_FEE_RATE if lt == "va" else ZERO

            # Prepaids
            pi = ZERO
            if not is_cash and la > ZERO:
                pi = (la * ir / Decimal("100") / Decimal("365")) * Decimal("15")
            pins = (ai / Decimal("12")) * Decimal(mi)
            tesc = (at / Decimal("12")) * Decimal(mt)

            # Total closing costs (fixed fees + title + endorsements + lender)
            # Custom fees (buyer side)
            custom_buyer_total = ZERO
            custom_buyer_items: List[LineItem] = []
            for cfe in fees.get("custom_fees", []):
                if not isinstance(cfe, dict):
                    continue
                side = cfe.get("side", "seller")
                if side not in ("buyer", "both"):
                    continue
                label = cfe.get("label", "Custom Fee")
                fee_type = cfe.get("type", "flat")
                amount = _to_decimal(cfe.get("amount", 0))
                if fee_type == "percent":
                    computed = pp * amount / Decimal("100")
                else:
                    computed = amount
                if computed > ZERO:
                    pct_note = f" ({amount}%)" if fee_type == "percent" else ""
                    custom_buyer_total += computed
                    custom_buyer_items.append(LineItem(label=f"{label}{pct_note}", amount=_round_cents(computed), category="custom"))

            tcc = (ltp + cf + rf
                   + t19 + survey_cover + t17 + t36 + t30
                   + misc_lender + af + cr + fha + va
                   + fee_tax_cert + fee_e_recording_buyer
                   + custom_buyer_total)

            # Cash to close = down + closing + prepaids + inspections - seller credit
            ctc = dp + tcc + pi + pins + tesc + survey + pest + home_insp - sc

            # Monthly payment breakdown
            monthly_pi = _monthly_payment(la, ir, 30) if not is_cash and la > ZERO else ZERO
            monthly_taxes = at / Decimal("12")
            monthly_ins = ai / Decimal("12")
            # PMI for conventional with LTV > 80%
            ltv_pct = (la / pp * Decimal("100")) if pp > ZERO else ZERO
            monthly_pmi = ZERO
            if lt == "conventional" and ltv_pct > Decimal("80") and la > ZERO:
                monthly_pmi = la * Decimal("0.0045") / Decimal("12")  # ~0.45% annual PMI
            total_monthly = monthly_pi + monthly_taxes + monthly_ins + monthly_pmi

            # Build line items
            items: List[LineItem] = []

            # Prepaids
            if pi > ZERO:
                items.append(LineItem(label="Prepaid Interest (15 days)", amount=_round_cents(pi), category="prepaid"))
            items.append(LineItem(label=f"Prepaid Insurance ({mi} mo)", amount=_round_cents(pins), category="prepaid"))
            items.append(LineItem(label=f"Tax Escrow ({mt} mo)", amount=_round_cents(tesc), category="prepaid"))

            # Title fees
            items.extend([
                LineItem(label="Lender's Title Policy", amount=_round_cents(ltp), category="title"),
            ])
            if t19 > ZERO:
                items.append(LineItem(label="T-19 Endorsement", amount=_round_cents(t19), category="title"))
            if survey_cover > ZERO:
                items.append(LineItem(label="Survey Cover Endorsement", amount=_round_cents(survey_cover), category="title"))
            if t17 > ZERO:
                items.append(LineItem(label="Mortgagee's T-17 Endorsement", amount=_round_cents(t17), category="title"))
            if t36 > ZERO:
                items.append(LineItem(label="Mortgagee's T-36 Endorsement", amount=_round_cents(t36), category="title"))
            if t30 > ZERO:
                items.append(LineItem(label="Mortgagee's T-30 Endorsement", amount=_round_cents(t30), category="title"))

            # Lender fees
            if not is_cash:
                items.extend([
                    LineItem(label="Misc. Lender Fees", amount=_round_cents(misc_lender), category="lender"),
                    LineItem(label="Appraisal", amount=_round_cents(af), category="lender"),
                    LineItem(label="Credit Report", amount=_round_cents(cr), category="lender"),
                ])
            if fha > ZERO:
                items.append(LineItem(label="FHA Upfront MIP (1.75%)", amount=_round_cents(fha), category="lender"))
            if va > ZERO:
                items.append(LineItem(label="VA Funding Fee (2.15%)", amount=_round_cents(va), category="lender"))

            # Inspections
            items.extend([
                LineItem(label="Survey", amount=_round_cents(survey), category="inspection"),
                LineItem(label="Pest Inspection", amount=_round_cents(pest), category="inspection"),
                LineItem(label="Home Inspection", amount=_round_cents(home_insp), category="inspection"),
            ])

            # Government
            items.extend([
                LineItem(label="Recording Fee", amount=_round_cents(rf), category="government"),
                LineItem(label="Tax Certificates", amount=_round_cents(fee_tax_cert), category="government"),
                LineItem(label="E-Recording Fee", amount=_round_cents(fee_e_recording_buyer), category="government"),
            ])

            items.extend(custom_buyer_items)

            if sc > ZERO:
                items.append(LineItem(label="Seller Concession", amount=_round_cents(-sc), category="credits"))

            result = BuyerEstimateResult(
                cash_to_close=_round_cents(ctc), purchase_price=_round_cents(pp),
                down_payment=_round_cents(dp), loan_amount=_round_cents(la),
                total_closing_costs=_round_cents(tcc + pi + pins + tesc + survey + pest + home_insp),
                lender_title_premium=_round_cents(ltp),
                monthly_payment=_round_cents(total_monthly),
                monthly_pi=_round_cents(monthly_pi),
                monthly_taxes=_round_cents(monthly_taxes),
                monthly_insurance=_round_cents(monthly_ins),
                monthly_pmi=_round_cents(monthly_pmi) if monthly_pmi > ZERO else None,
                line_items=items, order_ready=True,
            )
            if data.save:
                try:
                    import uuid
                    sheet = SavedSheet(sheet_type="buyer_estimate", property_address=data.property_address,
                        client_name=data.client_name, county_id=data.county_id,
                        input_data=data.model_dump(mode="json"), output_data=result.model_dump(mode="json"),
                        share_token=uuid.uuid4().hex)
                    db.add(sheet); db.commit(); db.refresh(sheet)
                    result.saved_sheet_id = sheet.id
                except Exception as save_err:
                    db.rollback(); logger.error("Failed to save buyer sheet: %s", save_err)
            return result
        except CalculatorError:
            raise
        except Exception as e:
            logger.error("buyer_estimate failed: %s", e)
            raise CalculatorError(f"buyer_estimate failed: {e}") from e

    # -----------------------------------------------------------------------
    # 3. Sell vs Rent
    # -----------------------------------------------------------------------
    def sell_vs_rent(self, data: SellVsRentInput) -> SellVsRentResult:
        try:
            cv = _to_decimal(data.current_value)
            mr = _to_decimal(data.monthly_rent_income)
            mm = _to_decimal(data.monthly_mortgage_payment)
            tr = _to_decimal(data.annual_tax_rate_pct) / Decimal("100")
            ap = _to_decimal(data.annual_appreciation_rate_pct) / Decimal("100")
            years = max(1, min(int(data.analysis_years), 30))
            proj, cum, be, val = [], ZERO, None, cv
            for y in range(1, years + 1):
                val *= (Decimal("1") + ap)
                net = mr * Decimal("12") - mm * Decimal("12") - val * tr
                cum += net
                eq = val - cv
                diff = eq - cum
                if be is None and cum >= eq:
                    be = y
                proj.append(SellVsRentYear(year=y, equity_if_sell=_round_cents(eq), net_if_rent=_round_cents(cum), difference=_round_cents(diff)))
            return SellVsRentResult(projection=proj, break_even_year=be,
                recommendation_text=f"Renting overtakes selling in year {be}." if be else "Selling generates more equity over the analysis window.")
        except Exception as e:
            raise CalculatorError(f"sell_vs_rent failed: {e}") from e

    # -----------------------------------------------------------------------
    # 4. Holding Cost
    # -----------------------------------------------------------------------
    def holding_cost(self, data: HoldingCostInput) -> HoldingCostResult:
        try:
            pp = _to_decimal(data.purchase_price)
            rp = _to_decimal(data.loan_rate_pct) / Decimal("100")
            mo = max(0, int(data.months_holding))
            at = _to_decimal(data.annual_property_tax)
            ai = _to_decimal(data.annual_insurance)
            hoa = _to_decimal(data.monthly_hoa)
            maint = _to_decimal(data.monthly_maintenance)
            mi = pp * rp / Decimal("12")
            mt = at / Decimal("12")
            mins = ai / Decimal("12")
            mc = mi + mt + mins + hoa + maint
            tc = mc * Decimal(mo)
            return HoldingCostResult(monthly_cost=_round_cents(mc), total_cost=_round_cents(tc), line_items=[
                LineItem(label="Monthly Interest", amount=_round_cents(mi), category="finance"),
                LineItem(label="Monthly Property Tax", amount=_round_cents(mt), category="government"),
                LineItem(label="Monthly Insurance", amount=_round_cents(mins), category="insurance"),
                LineItem(label="Monthly HOA", amount=_round_cents(hoa), category="other"),
                LineItem(label="Monthly Maintenance", amount=_round_cents(maint), category="other"),
            ])
        except Exception as e:
            raise CalculatorError(f"holding_cost failed: {e}") from e

    # -----------------------------------------------------------------------
    # 5. Buydown
    # -----------------------------------------------------------------------
    def buydown(self, data: BuydownInput) -> BuydownResult:
        try:
            la = _to_decimal(data.loan_amount)
            br = _to_decimal(data.base_rate_pct)
            ty = max(1, int(data.loan_term_years))
            pc = _to_decimal(data.points_cost)
            bt = (data.buydown_type or "").lower().strip()
            if bt in ("1-0", "1_0", "10"):
                pat = [Decimal("1.0")] + [Decimal("0")] * (ty - 1)
            elif bt in ("2-1", "2_1", "21"):
                pat = [Decimal("2.0"), Decimal("1.0")] + [Decimal("0")] * (ty - 2)
            elif bt in ("3-2-1", "3_2_1", "321"):
                pat = [Decimal("3.0"), Decimal("2.0"), Decimal("1.0")] + [Decimal("0")] * (ty - 3)
            else:
                pat = [(pc / la * Decimal("100") * Decimal("0.25")) if la > ZERO else ZERO] * ty
            sched, cs, bp = [], ZERO, _monthly_payment(la, br, ty)
            for i, rd in enumerate(pat, 1):
                yr = max(Decimal("0.01"), br - rd)
                yp = _monthly_payment(la, yr, ty)
                ms = bp - yp
                cs += ms * Decimal("12")
                sched.append(BuydownYear(year=i, rate=_round_cents(yr), payment=_round_cents(yp), monthly_savings=_round_cents(ms)))
            bem, run = None, ZERO
            if pc > ZERO:
                for i, r in enumerate(sched, 1):
                    for _ in range(12):
                        run += r.monthly_savings
                        if run >= pc and bem is None:
                            bem = (i - 1) * 12 + 1
                            break
                    if bem:
                        break
            return BuydownResult(schedule=sched, total_savings=_round_cents(cs), break_even_months=bem, net_benefit=_round_cents(cs - pc))
        except Exception as e:
            raise CalculatorError(f"buydown failed: {e}") from e

    # -----------------------------------------------------------------------
    # 6. TruValue Analysis
    # -----------------------------------------------------------------------
    def truvalue(self, data: TruValueInput, db: Session = None) -> TruValueResult:
        db = db if db is not None else getattr(self, "_db", None)
        try:
            prices = [
                ("Below Market", _to_decimal(data.price_low), data.days_on_market_low),
                ("At Market", _to_decimal(data.price_mid), data.days_on_market_mid),
                ("Above Market", _to_decimal(data.price_high), data.days_on_market_high),
            ]
            holding = _to_decimal(data.monthly_holding_cost)
            scenarios = []
            best_idx, best_net = 0, Decimal("-999999999")

            for idx, (label, price, dom) in enumerate(prices):
                sns_input = SellerNetSheetInput(
                    sale_price=price, existing_loan_balance=data.existing_loan_balance,
                    seller_agent_commission_pct=data.seller_agent_commission_pct,
                    buyer_agent_commission_pct=data.buyer_agent_commission_pct,
                    county_id=data.county_id, include_home_warranty=data.include_home_warranty,
                )
                sns = self.seller_net_sheet(sns_input, db=db)
                hc = holding * Decimal(str(dom)) / Decimal("30")
                adjusted = _to_decimal(sns.net_proceeds) - hc
                if adjusted > best_net:
                    best_net = adjusted
                    best_idx = idx
                scenarios.append(TruValueScenario(
                    label=label, list_price=_round_cents(price),
                    net_proceeds=_round_cents(sns.net_proceeds), days_on_market=dom,
                    holding_cost=_round_cents(hc), adjusted_net=_round_cents(adjusted),
                    total_closing_costs=_round_cents(sns.total_closing_costs),
                    line_items=sns.line_items,
                ))

            best = scenarios[best_idx]
            rec = f"Pricing at {best.label} (${best.list_price:,.0f}) yields the best adjusted net of ${best.adjusted_net:,.2f} after accounting for {best.days_on_market} estimated days on market."
            return TruValueResult(scenarios=scenarios, recommendation=rec, best_scenario_index=best_idx)
        except CalculatorError:
            raise
        except Exception as e:
            raise CalculatorError(f"truvalue failed: {e}") from e

    # -----------------------------------------------------------------------
    # 7. Buyer Agent Compensation
    # -----------------------------------------------------------------------
    def buyer_compensation(self, data: BuyerCompensationInput) -> BuyerCompensationResult:
        try:
            pp = _to_decimal(data.purchase_price)
            la = _to_decimal(data.loan_amount)
            sop = _to_decimal(data.seller_offered_compensation_pct)
            baf = _to_decimal(data.buyer_agent_fee_pct)
            ir = _to_decimal(data.interest_rate)
            ty = max(1, int(data.loan_term_years))

            total_fee = pp * baf / Decimal("100")
            seller_contrib = pp * sop / Decimal("100")
            gap = max(ZERO, total_fee - seller_contrib)

            # Build all 4 scenarios
            scenarios = [
                CompensationScenario(structure="seller_pays", buyer_cost=ZERO,
                    seller_cost=total_fee, note="Seller pays full buyer agent fee"),
                CompensationScenario(structure="buyer_pays", buyer_cost=total_fee,
                    seller_cost=ZERO, note="Buyer pays full fee out of pocket"),
                CompensationScenario(structure="split", buyer_cost=_round_cents(gap),
                    seller_cost=_round_cents(seller_contrib),
                    note=f"Seller offers {sop}%, buyer covers the {baf - sop}% gap"),
                CompensationScenario(structure="flat_fee",
                    buyer_cost=_round_cents(max(ZERO, _to_decimal(data.flat_fee_amount) - seller_contrib)),
                    seller_cost=_round_cents(min(seller_contrib, _to_decimal(data.flat_fee_amount))),
                    note=f"Flat fee of ${data.flat_fee_amount:,.0f}"),
            ]

            # Determine active scenario
            struct = (data.compensation_structure or "split").lower()
            if struct == "seller_pays":
                oop = ZERO
            elif struct == "buyer_pays":
                oop = total_fee
            elif struct == "flat_fee":
                oop = max(ZERO, _to_decimal(data.flat_fee_amount) - seller_contrib)
            else:
                oop = gap

            # Can the gap be financed into the loan?
            can_finance = la > ZERO and oop > ZERO
            mpi = ZERO
            if can_finance and la > ZERO:
                base_pmt = _monthly_payment(la, ir, ty)
                new_pmt = _monthly_payment(la + oop, ir, ty)
                mpi = new_pmt - base_pmt

            explainer = (
                f"The buyer agent fee is ${total_fee:,.2f} ({baf}% of ${pp:,.0f}). "
                f"The seller is offering ${seller_contrib:,.2f} ({sop}%) toward buyer agent compensation. "
            )
            if oop > ZERO:
                explainer += f"Under the '{struct}' structure, the buyer pays ${oop:,.2f} out of pocket."
                if can_finance:
                    explainer += f" If financed, this adds ${mpi:,.2f}/mo to the mortgage payment."
            else:
                explainer += "The buyer has no out-of-pocket agent fee under this structure."

            return BuyerCompensationResult(
                total_agent_fee=_round_cents(total_fee), seller_contribution=_round_cents(seller_contrib),
                buyer_out_of_pocket=_round_cents(oop), can_finance=can_finance,
                monthly_payment_impact=_round_cents(mpi), scenarios=scenarios, explainer_text=explainer,
            )
        except Exception as e:
            raise CalculatorError(f"buyer_compensation failed: {e}") from e

    # -----------------------------------------------------------------------
    # 8. Buy Now vs Buy Later
    # -----------------------------------------------------------------------
    def buy_now_vs_later(self, data: BuyNowVsLaterInput) -> BuyNowVsLaterResult:
        try:
            cp = _to_decimal(data.current_price)
            cr = _to_decimal(data.current_rate)
            ltv = _to_decimal(data.loan_amount_pct) / Decimal("100")
            ap = _to_decimal(data.annual_appreciation_pct) / Decimal("100")
            rc = _to_decimal(data.rate_change_per_year)
            rent = _to_decimal(data.monthly_rent_if_waiting)
            ty = max(1, int(data.loan_term_years))

            curr_loan = cp * ltv
            curr_pmt = _monthly_payment(curr_loan, cr, ty)
            current = BuyNowCurrentScenario(price=_round_cents(cp), rate=_round_cents(cr),
                loan=_round_cents(curr_loan), monthly_payment=_round_cents(curr_pmt))

            futures = []
            for months in (data.analysis_months or [6, 12, 18, 24]):
                m = max(1, int(months))
                frac = Decimal(str(m)) / Decimal("12")
                fp = cp * (Decimal("1") + ap * frac)
                fr = cr + rc * frac
                fl = fp * ltv
                fpmt = _monthly_payment(fl, fr, ty)
                inc = fpmt - curr_pmt
                rs = rent * Decimal(str(m))
                # Total cost = rent spent + extra payment over life of loan
                tcw = rs + (inc * Decimal(str(ty * 12)))
                futures.append(BuyNowFutureScenario(
                    months_waited=m, price=_round_cents(fp), rate=_round_cents(fr),
                    loan=_round_cents(fl), monthly_payment=_round_cents(fpmt),
                    payment_increase=_round_cents(inc), rent_spent=_round_cents(rs),
                    total_cost_of_waiting=_round_cents(tcw),
                ))

            if futures:
                worst = max(futures, key=lambda f: f.total_cost_of_waiting)
                rec = f"Waiting {worst.months_waited} months could cost ${worst.total_cost_of_waiting:,.0f} in rent spent plus higher payments over the life of your loan."
            else:
                rec = "Buy now to lock in current rates and pricing."
            return BuyNowVsLaterResult(current_scenario=current, future_scenarios=futures, recommendation=rec)
        except Exception as e:
            raise CalculatorError(f"buy_now_vs_later failed: {e}") from e

    # -----------------------------------------------------------------------
    # 9. Price vs Rate Impact
    # -----------------------------------------------------------------------
    def price_vs_rate(self, data: PriceVsRateInput) -> PriceVsRateResult:
        try:
            bp = _to_decimal(data.base_price)
            br = _to_decimal(data.base_rate)
            ltv = _to_decimal(data.loan_amount_pct) / Decimal("100")
            ty = max(1, int(data.loan_term_years))
            base_loan = bp * ltv
            base_pmt = _monthly_payment(base_loan, br, ty)

            matrix = []
            for pa in (data.price_adjustments or []):
                for ra in (data.rate_adjustments or []):
                    p = bp + _to_decimal(pa)
                    r = br + _to_decimal(ra)
                    if p <= ZERO or r <= ZERO:
                        continue
                    loan = p * ltv
                    pmt = _monthly_payment(loan, r, ty)
                    delta = pmt - base_pmt
                    total_int = (pmt * Decimal(str(ty * 12))) - loan
                    matrix.append(PriceVsRateCell(
                        price=_round_cents(p), rate=_round_cents(r),
                        monthly_payment=_round_cents(pmt), payment_delta=_round_cents(delta),
                        total_interest=_round_cents(total_int),
                    ))

            return PriceVsRateResult(base_payment=_round_cents(base_pmt), matrix=matrix)
        except Exception as e:
            raise CalculatorError(f"price_vs_rate failed: {e}") from e

    # -----------------------------------------------------------------------
    # 10. Extra Payment / Accelerated Payoff
    # -----------------------------------------------------------------------
    def extra_payment(self, data: ExtraPaymentInput) -> ExtraPaymentResult:
        try:
            la = _to_decimal(data.loan_amount)
            ir = _to_decimal(data.interest_rate) / Decimal("100")
            ty = max(1, int(data.loan_term_years))
            em = _to_decimal(data.extra_monthly)
            ea = _to_decimal(data.extra_annual)
            eo = _to_decimal(data.extra_one_time)
            mr = ir / Decimal("12")
            base_pmt = _monthly_payment(la, data.interest_rate, ty)

            # Standard amortization
            std_bal, std_int, std_months = la, ZERO, 0
            for m in range(1, ty * 12 + 1):
                if std_bal <= ZERO:
                    break
                interest = std_bal * mr
                std_int += interest
                principal = base_pmt - interest
                std_bal = max(ZERO, std_bal - principal)
                std_months = m

            # Accelerated amortization
            acc_bal, acc_int, acc_months = la, ZERO, 0
            comparison = []
            std_track = la
            for m in range(1, ty * 12 + 1):
                if acc_bal <= ZERO:
                    break
                interest = acc_bal * mr
                acc_int += interest
                principal = base_pmt - interest + em
                if m == 1:
                    principal += eo
                if ea > ZERO and m % 12 == 0:
                    principal += ea
                acc_bal = max(ZERO, acc_bal - principal)
                acc_months = m
                # Track standard for comparison
                if std_track > ZERO:
                    si = std_track * mr
                    std_track = max(ZERO, std_track - (base_pmt - si))
                if m % 12 == 0:
                    comparison.append(AmortizationPoint(month=m,
                        standard_balance=_round_cents(std_track),
                        accelerated_balance=_round_cents(acc_bal)))

            ms = std_months - acc_months
            ys = _round_cents(Decimal(str(ms)) / Decimal("12"))
            isav = std_int - acc_int

            return ExtraPaymentResult(
                standard=PayoffScenario(months=std_months, total_interest=_round_cents(std_int),
                    total_paid=_round_cents(std_int + la)),
                accelerated=PayoffScenario(months=acc_months, total_interest=_round_cents(acc_int),
                    total_paid=_round_cents(acc_int + la)),
                savings=PayoffSavings(months_saved=ms, years_saved=ys, interest_saved=_round_cents(isav)),
                amortization_comparison=comparison,
            )
        except Exception as e:
            raise CalculatorError(f"extra_payment failed: {e}") from e

    # -----------------------------------------------------------------------
    # 11. Scenario Compare
    # -----------------------------------------------------------------------
    def scenario_compare(self, data: ScenarioCompareInput, db: Session = None) -> ScenarioCompareResult:
        db = db if db is not None else getattr(self, "_db", None)
        try:
            def _build_sns(offer: ScenarioOfferInput) -> SellerNetSheetInput:
                return SellerNetSheetInput(
                    sale_price=offer.offer_price,
                    existing_loan_balance=data.existing_loan_balance,
                    seller_agent_commission_pct=data.seller_agent_commission_pct,
                    buyer_agent_commission_pct=offer.buyer_agent_pct,
                    county_id=data.county_id,
                    closing_date=offer.closing_date,
                    annual_property_taxes=offer.annual_property_taxes,
                    seller_concessions=offer.seller_concessions,
                    include_home_warranty=data.include_home_warranty,
                )

            result_a = self.seller_net_sheet(_build_sns(data.scenario_a), db=db)
            result_b = self.seller_net_sheet(_build_sns(data.scenario_b), db=db)
            diff = _to_decimal(result_a.net_proceeds) - _to_decimal(result_b.net_proceeds)

            if diff > ZERO:
                rec = f"Offer A nets ${diff:,.2f} more than Offer B."
                if data.scenario_a.notes:
                    rec += f" (A: {data.scenario_a.notes})"
            elif diff < ZERO:
                rec = f"Offer B nets ${abs(diff):,.2f} more than Offer A."
                if data.scenario_b.notes:
                    rec += f" (B: {data.scenario_b.notes})"
            else:
                rec = "Both offers produce identical net proceeds."

            return ScenarioCompareResult(
                scenario_a=result_a, scenario_b=result_b,
                difference=_round_cents(diff), recommendation=rec,
            )
        except CalculatorError:
            raise
        except Exception as e:
            raise CalculatorError(f"scenario_compare failed: {e}") from e


def get_title_calculator_service(db: Session = Depends(get_db)) -> TitleCalculatorService:
    inst = TitleCalculatorService()
    inst._db = db
    return inst
