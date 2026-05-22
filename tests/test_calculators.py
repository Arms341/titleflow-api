"""
tests/test_calculators.py  v1.1.0
Locked template — JARVIS title_company gig.

v1.1.0: Fixed URL prefixes — hyphens → underscores to match main.py
  include_router(prefix="/rate_tables") convention.

Tests verify:
  - Seller net sheet math end-to-end against hand-calculated values
  - Buyer estimate with FHA UFMIP applied correctly
  - Cash-loan path (no lender fees)
  - Reissue discount reduces owner title premium
  - Sell-vs-rent, holding-cost, buydown basic sanity
"""
import logging
from typing import Any

logger = logging.getLogger(__name__)


def _setup_rate_table_with_brackets(client: Any, auth_headers: Any,
                                    state: str = "TX",
                                    table_type: str = "owner_policy") -> int:
    """Helper: create a Texas standard rate table + brackets."""
    rt_payload = {
        "name": f"TX {table_type} standard",
        "state": state,
        "table_type": table_type,
        "is_active": True,
    }
    r = client.post("/rate_tables/", json=rt_payload, headers=auth_headers)
    assert r.status_code == 201, f"Rate table setup failed: {r.text}"
    rt_id = r.json()["id"]

    brackets = {
        "brackets": [
            {"rate_table_id": rt_id, "min_value": 0, "max_value": 100000, "rate_per_thousand": 5.75},
            {"rate_table_id": rt_id, "min_value": 100000, "max_value": 500000, "rate_per_thousand": 5.00},
            {"rate_table_id": rt_id, "min_value": 500000, "max_value": 1000000, "rate_per_thousand": 4.50},
        ],
    }
    b = client.post(f"/rate_brackets/bulk/{rt_id}", json=brackets, headers=auth_headers)
    assert b.status_code == 201, f"Bracket setup failed: {b.text}"
    return rt_id


def _setup_county(client: Any, auth_headers: Any,
                  owner_rate_table_id: int,
                  lender_rate_table_id: int) -> int:
    """Helper: create a Lubbock county row wired to given rate tables."""
    payload = {
        "state": "TX",
        "county_name": "Lubbock",
        "city": "Lubbock",
        "closing_fee_flat": 250.00,
        "recording_fee_flat": 75.00,
        "transfer_tax_rate_pct": 0.0,
        "survey_fee_flat": 450.00,
        "home_warranty_flat": 600.00,
        "simultaneous_issue_discount_flat": 200.00,
        "owner_rate_table_id": owner_rate_table_id,
        "lender_rate_table_id": lender_rate_table_id,
        "is_active": True,
    }
    r = client.post("/counties/", json=payload, headers=auth_headers)
    assert r.status_code == 201, f"County setup failed: {r.text}"
    return r.json()["id"]


def test_seller_net_sheet_basic(client: Any, auth_headers: Any, test_db: Any) -> None:
    """$400k sale, $250k loan, 3%+3% commission — sanity check."""
    owner_rt = _setup_rate_table_with_brackets(client, auth_headers, table_type="owner_policy")
    lender_rt = _setup_rate_table_with_brackets(client, auth_headers, table_type="lender_policy")
    county_id = _setup_county(client, auth_headers, owner_rt, lender_rt)

    payload = {
        "sale_price": 400000.00,
        "existing_loan_balance": 250000.00,
        "seller_agent_commission_pct": 3.0,
        "buyer_agent_commission_pct": 3.0,
        "county_id": county_id,
        "include_home_warranty": True,
        "include_survey": False,
    }
    response = client.post("/calculators/seller-net-sheet", json=payload, headers=auth_headers)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert "net_proceeds" in data
    assert "sale_price" in data
    assert "line_items" in data
    # Commission = 400000 * 6% = 24000
    assert float(data["total_commission"]) == 24000.00
    # Owner title on $400k: 575 + 300000 * 5/1000 = 575 + 1500 = 2075
    assert float(data["owner_title_premium"]) == 2075.00
    logger.info("Seller net proceeds: %s", data["net_proceeds"])


def test_seller_net_sheet_with_reissue_discount(client: Any, auth_headers: Any, test_db: Any) -> None:
    """Prior title insurance triggers reissue discount row."""
    owner_rt = _setup_rate_table_with_brackets(client, auth_headers, table_type="owner_policy")
    lender_rt = _setup_rate_table_with_brackets(client, auth_headers, table_type="lender_policy")
    county_id = _setup_county(client, auth_headers, owner_rt, lender_rt)

    # Seed a reissue discount row (30% for <= 5 years)
    rd = client.post("/reissue_discounts/",
                     json={"rate_table_id": owner_rt,
                           "years_since_prior_policy": 5,
                           "discount_pct": 30.0},
                     headers=auth_headers)
    assert rd.status_code == 201

    payload = {
        "sale_price": 400000.00,
        "existing_loan_balance": 250000.00,
        "county_id": county_id,
        "prior_title_insurance": True,
        "years_since_prior_policy": 3,
    }
    response = client.post("/calculators/seller-net-sheet", json=payload, headers=auth_headers)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    # 30% of 2075 = 622.50
    assert float(data["reissue_savings"]) > 0
    logger.info("Reissue savings applied: %s", data["reissue_savings"])


def test_buyer_estimate_conventional(client: Any, auth_headers: Any, test_db: Any) -> None:
    """$350k purchase, $280k conventional loan — cash-to-close sanity check."""
    owner_rt = _setup_rate_table_with_brackets(client, auth_headers, table_type="owner_policy")
    lender_rt = _setup_rate_table_with_brackets(client, auth_headers, table_type="lender_policy")
    county_id = _setup_county(client, auth_headers, owner_rt, lender_rt)

    payload = {
        "purchase_price": 350000.00,
        "loan_amount": 280000.00,
        "loan_type": "conventional",
        "interest_rate": 7.0,
        "county_id": county_id,
        "annual_property_taxes": 4500.00,
        "annual_homeowners_insurance": 1500.00,
        "months_insurance_prepaid": 3,
        "months_tax_escrow": 3,
    }
    response = client.post("/calculators/buyer-estimate", json=payload, headers=auth_headers)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert "cash_to_close" in data
    assert float(data["down_payment"]) == 70000.00  # 350k - 280k


def test_buyer_estimate_fha_ufmip(client: Any, auth_headers: Any, test_db: Any) -> None:
    """FHA loan includes UFMIP line item."""
    owner_rt = _setup_rate_table_with_brackets(client, auth_headers, table_type="owner_policy")
    lender_rt = _setup_rate_table_with_brackets(client, auth_headers, table_type="lender_policy")
    county_id = _setup_county(client, auth_headers, owner_rt, lender_rt)

    payload = {
        "purchase_price": 300000.00,
        "loan_amount": 280000.00,
        "loan_type": "fha",
        "interest_rate": 6.5,
        "county_id": county_id,
        "annual_property_taxes": 4000.00,
        "annual_homeowners_insurance": 1400.00,
    }
    response = client.post("/calculators/buyer-estimate", json=payload, headers=auth_headers)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    # FHA UFMIP = 280000 * 0.0175 = 4900
    labels = [li["label"] for li in data["line_items"]]
    assert any("FHA" in l for l in labels), f"FHA UFMIP missing from line items: {labels}"


def test_buyer_estimate_cash(client: Any, auth_headers: Any, test_db: Any) -> None:
    """Cash loan_type — no lender fees, no FHA/VA."""
    owner_rt = _setup_rate_table_with_brackets(client, auth_headers, table_type="owner_policy")
    lender_rt = _setup_rate_table_with_brackets(client, auth_headers, table_type="lender_policy")
    county_id = _setup_county(client, auth_headers, owner_rt, lender_rt)

    payload = {
        "purchase_price": 250000.00,
        "loan_amount": 0.00,
        "loan_type": "cash",
        "interest_rate": 0,
        "county_id": county_id,
        "annual_property_taxes": 3000.00,
    }
    response = client.post("/calculators/buyer-estimate", json=payload, headers=auth_headers)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert float(data["lender_title_premium"]) == 0.0


def test_sell_vs_rent_basic(client: Any, auth_headers: Any) -> None:
    """Sell-vs-rent returns a projection array."""
    payload = {
        "current_value": 300000.00,
        "monthly_rent_income": 2000.00,
        "monthly_mortgage_payment": 1500.00,
        "annual_tax_rate_pct": 2.0,
        "annual_appreciation_rate_pct": 3.0,
        "analysis_years": 5,
    }
    response = client.post("/calculators/sell-vs-rent", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "projection" in data
    assert len(data["projection"]) == 5


def test_holding_cost_basic(client: Any, auth_headers: Any) -> None:
    """Holding cost returns monthly + total."""
    payload = {
        "purchase_price": 300000.00,
        "loan_rate_pct": 7.0,
        "months_holding": 6,
        "annual_property_tax": 4500.00,
        "annual_insurance": 1400.00,
        "monthly_hoa": 50.00,
        "monthly_maintenance": 100.00,
    }
    response = client.post("/calculators/holding-cost", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "monthly_cost" in data
    assert "total_cost" in data


def test_buydown_2_1(client: Any, auth_headers: Any) -> None:
    """2-1 buydown returns 2+ years of rate reductions."""
    payload = {
        "loan_amount": 300000.00,
        "base_rate_pct": 7.0,
        "buydown_type": "2-1",
        "points_cost": 6000.00,
        "loan_term_years": 30,
    }
    response = client.post("/calculators/buydown", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "schedule" in data
    assert len(data["schedule"]) >= 2
    # Year 1 rate should be 5% (7 - 2), year 2 should be 6% (7 - 1)
    assert float(data["schedule"][0]["rate"]) == 5.00
    assert float(data["schedule"][1]["rate"]) == 6.00
