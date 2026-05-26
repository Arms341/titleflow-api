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
            # Always update to Hub City branding
            existing_company.company_name = "HUB City Title"
            existing_company.logo_url = "https://www.hubcitytitle.com/uploads/8/1/1/8/81183436/published/2534139.jpg?1497909780"
            existing_company.primary_color = "#0f172a"
            existing_company.secondary_color = "#f59e0b"
            existing_company.phone = "(806) 412-1234"
            existing_company.email = "info@hubcitytitle.com"
            existing_company.website = "https://www.hubcitytitle.com"
            existing_company.address = "4415 66th Street, Suite 100, Lubbock, TX 79414"
            existing_company.tagline = "No Bull. Just Title."
            existing_company.disclaimer_text = "These figures are estimates only and are subject to change at closing. This is not a commitment to insure or a guarantee of fees. Actual costs may vary."
            existing_company.order_submission_email = admin_email
            db.commit()
            print("Updated company branding to HUB City Title.")
        else:
            company = Company(
                company_name="HUB City Title",
                logo_url="https://www.hubcitytitle.com/uploads/8/1/1/8/81183436/published/2534139.jpg?1497909780",
                primary_color="#1e3a8a",
                secondary_color="#f59e0b",
                phone="(806) 412-1234",
                email="info@hubcitytitle.com",
                website="https://www.hubcitytitle.com",
                address="4415 66th Street, Suite 100, Lubbock, TX 79414",
                tagline="No Bull. Just Title.",
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

        # =====================================================================
        # TAX DISTRICTS — Lubbock area school district combined rates
        # =====================================================================
        from models.tax_district import TaxDistrict

        existing_districts = db.query(TaxDistrict).count()
        if existing_districts > 0:
            print(f"Tax districts already exist ({existing_districts}). Skipping.")
        else:
            # Find Lubbock county ID
            lubbock_county = db.query(County).filter(County.county_name == "Lubbock").first()
            lubbock_county_id = lubbock_county.id if lubbock_county else None

            # Combined rates from WesternAgent ONE (city+county+ISD+hospital+water)
            tax_districts = [
                ("Lubbock (Lubbock ISD)", "2.2500", True),
                ("Lubbock Cooper", "2.5600", False),
                ("Frenship", "2.7600", False),
                ("Slaton", "2.7100", False),
                ("Idalou", "2.2700", False),
                ("Shallowater", "2.3600", False),
                ("New Deal", "2.3800", False),
                ("Roosevelt", "2.1300", False),
            ]
            for name, rate, is_default in tax_districts:
                db.add(TaxDistrict(
                    county_id=lubbock_county_id,
                    name=name,
                    combined_rate_pct=Decimal(rate),
                    is_default=is_default,
                    is_active=True,
                ))
            db.commit()
            print(f"Seeded {len(tax_districts)} Lubbock-area tax districts.")

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
