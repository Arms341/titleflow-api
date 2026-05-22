"""
TitleFlow — Seed Script for Hub City Title Company
Run after tables are created to populate admin, rate tables, and county data.

Usage:
  python3 seed_hubcity.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from decimal import Decimal
from database import SessionLocal
from models.base import get_password_hash

def seed():
    db = SessionLocal()
    try:
        # =====================================================================
        # ADMIN USER — Lee at Hub City Title
        # =====================================================================
        from models.user import User

        admin_email = os.environ.get("ADMIN_EMAIL", "lee@hubcitytitle.com")
        admin_password = os.environ.get("ADMIN_PASSWORD", "changeme123")

        existing_admin = db.query(User).filter(User.email == admin_email).first()
        if existing_admin:
            print(f"Admin user {admin_email} already exists. Skipping.")
        else:
            admin = User(
                email=admin_email,
                hashed_password=get_password_hash(admin_password),
                full_name="Lee",
                role="admin",
                is_active=True,
            )
            # Set approval_status if the field exists
            if hasattr(User, "approval_status"):
                admin.approval_status = "active"
            if hasattr(User, "is_approved"):
                admin.is_approved = True
            db.add(admin)
            db.commit()
            print(f"Admin user created: {admin_email}")

        # =====================================================================
        # RATE TABLES — Texas TDI 2026 Promulgated Rates
        # PLACEHOLDER brackets — replace with Lee's actual rate card
        # =====================================================================
        from models.rate_table import RateTable
        from models.rate_bracket import RateBracket
        from models.reissue_discount import ReissueDiscount

        existing_rt = db.query(RateTable).first()
        if existing_rt:
            print("Rate tables already seeded. Skipping.")
        else:
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

            # Reissue Discounts
            for years, pct in [(1, "30"), (2, "30"), (3, "25"), (4, "20"), (5, "15")]:
                db.add(ReissueDiscount(
                    rate_table_id=owner_table.id,
                    years_since_prior_policy=years,
                    discount_pct=Decimal(pct)
                ))

            db.commit()
            print("Rate tables and brackets seeded.")

        # =====================================================================
        # COUNTIES — Lubbock area with HUD-1 corrected fees
        # =====================================================================
        from models.county import County

        existing_county = db.query(County).first()
        if existing_county:
            print("Counties already seeded. Skipping.")
        else:
            counties = [
                {"state": "TX", "county_name": "Lubbock", "closing_fee_flat": "600.00", "recording_fee_flat": "33.00", "transfer_tax_rate_pct": "0.0000", "survey_fee_flat": "500.00", "home_warranty_flat": "550.00", "simultaneous_issue_discount_flat": "100.00"},
                {"state": "TX", "county_name": "Hockley", "closing_fee_flat": "600.00", "recording_fee_flat": "30.00", "transfer_tax_rate_pct": "0.0000", "survey_fee_flat": "500.00", "home_warranty_flat": "550.00", "simultaneous_issue_discount_flat": "100.00"},
                {"state": "TX", "county_name": "Crosby", "closing_fee_flat": "600.00", "recording_fee_flat": "30.00", "transfer_tax_rate_pct": "0.0000", "survey_fee_flat": "475.00", "home_warranty_flat": "550.00", "simultaneous_issue_discount_flat": "100.00"},
                {"state": "TX", "county_name": "Lynn", "closing_fee_flat": "600.00", "recording_fee_flat": "30.00", "transfer_tax_rate_pct": "0.0000", "survey_fee_flat": "475.00", "home_warranty_flat": "550.00", "simultaneous_issue_discount_flat": "100.00"},
                {"state": "TX", "county_name": "Garza", "closing_fee_flat": "600.00", "recording_fee_flat": "30.00", "transfer_tax_rate_pct": "0.0000", "survey_fee_flat": "475.00", "home_warranty_flat": "550.00", "simultaneous_issue_discount_flat": "100.00"},
                {"state": "TX", "county_name": "Terry", "closing_fee_flat": "600.00", "recording_fee_flat": "30.00", "transfer_tax_rate_pct": "0.0000", "survey_fee_flat": "475.00", "home_warranty_flat": "550.00", "simultaneous_issue_discount_flat": "100.00"},
                {"state": "TX", "county_name": "Cochran", "closing_fee_flat": "600.00", "recording_fee_flat": "30.00", "transfer_tax_rate_pct": "0.0000", "survey_fee_flat": "475.00", "home_warranty_flat": "550.00", "simultaneous_issue_discount_flat": "100.00"},
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
                    owner_rate_table_id=owner_table.id if 'owner_table' in dir() else 1,
                    lender_rate_table_id=lender_table.id if 'lender_table' in dir() else 2,
                    is_active=True,
                    effective_date="2026-03-01"
                ))
            db.commit()
            print(f"Seeded {len(counties)} West Texas counties.")

        print("Seed complete.")

    except Exception as e:
        db.rollback()
        print(f"Seed error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    seed()
