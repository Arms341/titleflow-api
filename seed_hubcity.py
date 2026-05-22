"""
TitleFlow — Seed Script for Hub City Title Company
Run after alembic upgrade head to populate rate tables and Lubbock County data.

Usage:
  docker compose exec app python3 seed_hubcity.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from decimal import Decimal
from database import SessionLocal
from models.rate_table import RateTable
from models.rate_bracket import RateBracket
from models.reissue_discount import ReissueDiscount
from models.county import County

def seed():
    db = SessionLocal()
    try:
        # =====================================================================
        # RATE TABLES — Texas TDI 2026 Promulgated Rates
        # These are PLACEHOLDER brackets based on standard TDI schedule.
        # REPLACE with Lee's actual rate card before go-live.
        # =====================================================================

        # Check if already seeded
        existing = db.query(RateTable).first()
        if existing:
            print("Rate tables already seeded. Skipping.")
            db.close()
            return

        # Owner's Policy
        owner_table = RateTable(
            name="TX Owner's Policy 2026",
            state="TX",
            table_type="owner_policy",
            effective_date="2026-03-01",
            is_active=True
        )
        db.add(owner_table)
        db.flush()

        owner_brackets = [
            {"min_value": "0", "max_value": "100000", "rate_per_thousand": "5.75"},
            {"min_value": "100001", "max_value": "500000", "rate_per_thousand": "5.00"},
            {"min_value": "500001", "max_value": "1000000", "rate_per_thousand": "4.50"},
            {"min_value": "1000001", "max_value": "99999999", "rate_per_thousand": "4.00"},
        ]
        for b in owner_brackets:
            db.add(RateBracket(
                rate_table_id=owner_table.id,
                min_value=Decimal(b["min_value"]),
                max_value=Decimal(b["max_value"]),
                rate_per_thousand=Decimal(b["rate_per_thousand"])
            ))

        # Lender's Policy
        lender_table = RateTable(
            name="TX Lender's Policy 2026",
            state="TX",
            table_type="lender_policy",
            effective_date="2026-03-01",
            is_active=True
        )
        db.add(lender_table)
        db.flush()

        lender_brackets = [
            {"min_value": "0", "max_value": "100000", "rate_per_thousand": "5.25"},
            {"min_value": "100001", "max_value": "500000", "rate_per_thousand": "4.50"},
            {"min_value": "500001", "max_value": "1000000", "rate_per_thousand": "4.00"},
            {"min_value": "1000001", "max_value": "99999999", "rate_per_thousand": "3.50"},
        ]
        for b in lender_brackets:
            db.add(RateBracket(
                rate_table_id=lender_table.id,
                min_value=Decimal(b["min_value"]),
                max_value=Decimal(b["max_value"]),
                rate_per_thousand=Decimal(b["rate_per_thousand"])
            ))

        # Reissue Discounts (standard TDI)
        for years, pct in [(1, "30"), (2, "30"), (3, "25"), (4, "20"), (5, "15")]:
            db.add(ReissueDiscount(
                rate_table_id=owner_table.id,
                years_since_prior_policy=years,
                discount_pct=Decimal(pct)
            ))

        # =====================================================================
        # COUNTIES — Lubbock area with HUD-1 corrected fees
        # Fees from real Hub City Title HUD-1 file 260527
        # =====================================================================

        counties = [
            {
                "state": "TX", "county_name": "Lubbock",
                "closing_fee_flat": "600.00",      # $300/side, HUD-1 line 1101
                "recording_fee_flat": "33.00",      # 3-page deed, HUD-1 line 1201
                "transfer_tax_rate_pct": "0.0000",  # Texas has no transfer tax
                "survey_fee_flat": "500.00",
                "home_warranty_flat": "550.00",
                "simultaneous_issue_discount_flat": "100.00",
            },
            {
                "state": "TX", "county_name": "Hockley",
                "closing_fee_flat": "600.00",
                "recording_fee_flat": "30.00",
                "transfer_tax_rate_pct": "0.0000",
                "survey_fee_flat": "500.00",
                "home_warranty_flat": "550.00",
                "simultaneous_issue_discount_flat": "100.00",
            },
            {
                "state": "TX", "county_name": "Crosby",
                "closing_fee_flat": "600.00",
                "recording_fee_flat": "30.00",
                "transfer_tax_rate_pct": "0.0000",
                "survey_fee_flat": "475.00",
                "home_warranty_flat": "550.00",
                "simultaneous_issue_discount_flat": "100.00",
            },
            {
                "state": "TX", "county_name": "Lynn",
                "closing_fee_flat": "600.00",
                "recording_fee_flat": "30.00",
                "transfer_tax_rate_pct": "0.0000",
                "survey_fee_flat": "475.00",
                "home_warranty_flat": "550.00",
                "simultaneous_issue_discount_flat": "100.00",
            },
            {
                "state": "TX", "county_name": "Garza",
                "closing_fee_flat": "600.00",
                "recording_fee_flat": "30.00",
                "transfer_tax_rate_pct": "0.0000",
                "survey_fee_flat": "475.00",
                "home_warranty_flat": "550.00",
                "simultaneous_issue_discount_flat": "100.00",
            },
            {
                "state": "TX", "county_name": "Terry",
                "closing_fee_flat": "600.00",
                "recording_fee_flat": "30.00",
                "transfer_tax_rate_pct": "0.0000",
                "survey_fee_flat": "475.00",
                "home_warranty_flat": "550.00",
                "simultaneous_issue_discount_flat": "100.00",
            },
            {
                "state": "TX", "county_name": "Cochran",
                "closing_fee_flat": "600.00",
                "recording_fee_flat": "30.00",
                "transfer_tax_rate_pct": "0.0000",
                "survey_fee_flat": "475.00",
                "home_warranty_flat": "550.00",
                "simultaneous_issue_discount_flat": "100.00",
            },
        ]

        for c in counties:
            db.add(County(
                state=c["state"],
                county_name=c["county_name"],
                closing_fee_flat=Decimal(c["closing_fee_flat"]),
                recording_fee_flat=Decimal(c["recording_fee_flat"]),
                transfer_tax_rate_pct=Decimal(c["transfer_tax_rate_pct"]),
                survey_fee_flat=Decimal(c["survey_fee_flat"]),
                home_warranty_flat=Decimal(c["home_warranty_flat"]),
                simultaneous_issue_discount_flat=Decimal(c["simultaneous_issue_discount_flat"]),
                owner_rate_table_id=owner_table.id,
                lender_rate_table_id=lender_table.id,
                is_active=True,
                effective_date="2026-03-01"
            ))

        db.commit()
        print(f"Seeded successfully:")
        print(f"  - 2 rate tables (Owner + Lender) with brackets")
        print(f"  - 5 reissue discount tiers")
        print(f"  - {len(counties)} West Texas counties")
        print(f"")
        print(f"  NOTE: Rate brackets are TDI PLACEHOLDERS.")
        print(f"  Replace with Lee's actual rate card before demo.")

    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed()
