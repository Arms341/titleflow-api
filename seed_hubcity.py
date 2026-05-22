"""
TitleFlow — Seed Script for Hub City Title Company
Run after tables are created to populate admin, company branding, rate tables, and county data.

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
        # ADMIN USER
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
            if hasattr(User, "approval_status"):
                admin.approval_status = "active"
            if hasattr(User, "is_approved"):
                admin.is_approved = True
            db.add(admin)
            db.commit()
            print(f"Admin user created: {admin_email}")

        # =====================================================================
        # COMPANY BRANDING — Hub City Title
        # =====================================================================
        from models.company import Company

        existing_company = db.query(Company).first()
        if existing_company:
            # Update existing with Hub City branding if still default
            if existing_company.company_name in (None, "Title Company", ""):
                existing_company.company_name = "Hub City Title"
                existing_company.primary_color = "#1e3a8a"
                existing_company.secondary_color = "#f59e0b"
                existing_company.tagline = "Your West Texas Title Experts"
                existing_company.disclaimer_text = "These figures are estimates only and are subject to change at closing. This is not a commitment to insure or a guarantee of fees. Actual costs may vary."
                existing_company.order_submission_email = admin_email
                db.commit()
                print("Updated company branding to Hub City Title.")
            else:
                print(f"Company already configured: {existing_company.company_name}. Skipping.")
        else:
            company = Company(
                company_name="Hub City Title",
                primary_color="#1e3a8a",
                secondary_color="#f59e0b",
                phone="(806) 555-0100",
                email="info@hubcitytitle.com",
                website="https://hubcitytitle.com",
                address="Lubbock, TX",
                tagline="Your West Texas Title Experts",
                disclaimer_text="These figures are estimates only and are subject to change at closing. This is not a commitment to insure or a guarantee of fees. Actual costs may vary.",
                order_submission_email=admin_email,
            )
            db.add(company)
            db.commit()
            print("Company branding created: Hub City Title")

        # =====================================================================
        # RATE TABLES — Texas TDI 2026 Promulgated Rates
        # =====================================================================
        from models.rate_table import RateTable
        from models.rate_bracket import RateBracket
        from models.reissue_discount import ReissueDiscount

        existing_rt = db.query(RateTable).first()
        if existing_rt:
            print("Rate tables already seeded. Skipping.")
        else:
            owner_table = RateTable(name="TX Owner's Policy 2026", state="TX", table_type="owner_policy", effective_date="2026-03-01", is_active=True)
            db.add(owner_table)
            db.flush()
            for b in [("0","100000","5.75"),("100001","500000","5.00"),("500001","1000000","4.50"),("1000001","99999999","4.00")]:
                db.add(RateBracket(rate_table_id=owner_table.id, min_value=Decimal(b[0]), max_value=Decimal(b[1]), rate_per_thousand=Decimal(b[2])))

            lender_table = RateTable(name="TX Lender's Policy 2026", state="TX", table_type="lender_policy", effective_date="2026-03-01", is_active=True)
            db.add(lender_table)
            db.flush()
            for b in [("0","100000","5.25"),("100001","500000","4.50"),("500001","1000000","4.00"),("1000001","99999999","3.50")]:
                db.add(RateBracket(rate_table_id=lender_table.id, min_value=Decimal(b[0]), max_value=Decimal(b[1]), rate_per_thousand=Decimal(b[2])))

            for years, pct in [(1,"30"),(2,"30"),(3,"25"),(4,"20"),(5,"15")]:
                db.add(ReissueDiscount(rate_table_id=owner_table.id, years_since_prior_policy=years, discount_pct=Decimal(pct)))
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
            counties_data = [
                ("Lubbock", "600.00", "33.00", "500.00"),
                ("Hockley", "600.00", "30.00", "500.00"),
                ("Crosby", "600.00", "30.00", "475.00"),
                ("Lynn", "600.00", "30.00", "475.00"),
                ("Garza", "600.00", "30.00", "475.00"),
                ("Terry", "600.00", "30.00", "475.00"),
                ("Cochran", "600.00", "30.00", "475.00"),
            ]
            for name, closing, recording, survey in counties_data:
                db.add(County(
                    state="TX", county_name=name,
                    closing_fee_flat=Decimal(closing), recording_fee_flat=Decimal(recording),
                    transfer_tax_rate_pct=Decimal("0.0000"), survey_fee_flat=Decimal(survey),
                    home_warranty_flat=Decimal("550.00"), simultaneous_issue_discount_flat=Decimal("100.00"),
                    owner_rate_table_id=1, lender_rate_table_id=2,
                    is_active=True, effective_date="2026-03-01"
                ))
            db.commit()
            print(f"Seeded {len(counties_data)} West Texas counties.")

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
