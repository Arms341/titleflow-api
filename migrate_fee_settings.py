"""
migrate_fee_settings.py — Add fee_settings column to companies table.
Run once: python migrate_fee_settings.py
"""
import json
from sqlalchemy import text
from database import get_db, engine

DEFAULT_FEES = {
    "closing_fee_per_side": 300.00,
    "recording_fee": 33.00,
    "deed_prep_fee": 150.00,
    "release_prep_fee": 50.00,
    "tax_cert_fee": 10.00,
    "e_recording_fee_seller": 19.35,
    "e_recording_fee_buyer": 6.45,
    "guaranty_fee": 2.00,
    "survey_fee": 500.00,
    "default_home_warranty": 700.00,
    "appraisal_fee": 550.00,
    "credit_report_fee": 35.00,
    "flood_cert_fee": 20.00,
    "origination_rate_pct": 1.0,
    "default_per_diem_rate_pct": 6.5,
    "endorsements": {
        "t19": {"amount": 80.99, "enabled": True, "label": "T-19 Restrictions/Encroachments"},
        "survey_cover": {"amount": 99.15, "enabled": True, "label": "Survey Cover (T-19.1)"},
        "t17": {"amount": 25.00, "enabled": True, "label": "T-17 Access"},
        "t36": {"amount": 25.00, "enabled": True, "label": "T-36 Environmental Lien"},
        "t30": {"amount": 25.00, "enabled": True, "label": "T-30 Mortgagee"}
    },
    "seller_toggles": {
        "recording_fee": True,
        "transfer_tax": True,
        "tax_cert": True,
        "e_recording": True,
        "guaranty_fee": True,
        "home_warranty": True,
        "survey": True,
        "per_diem_interest": True
    }
}


def migrate():
    db = next(get_db())
    try:
        # Add column if not exists
        try:
            db.execute(text("ALTER TABLE companies ADD COLUMN fee_settings TEXT"))
            db.commit()
            print("Added fee_settings column.")
        except Exception as e:
            db.rollback()
            if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                print("fee_settings column already exists.")
            else:
                print(f"Column add error (may already exist): {e}")

        # Seed defaults if empty
        row = db.execute(text("SELECT id, fee_settings FROM companies LIMIT 1")).fetchone()
        if row and not row[1]:
            db.execute(
                text("UPDATE companies SET fee_settings = :fs WHERE id = :id"),
                {"fs": json.dumps(DEFAULT_FEES), "id": row[0]}
            )
            db.commit()
            print(f"Seeded default fee settings for company id={row[0]}.")
        else:
            print("Fee settings already populated or no company row found.")

        print("Done.")
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    migrate()
