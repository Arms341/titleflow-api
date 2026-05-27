"""
seed_6county_districts.py — Add tax districts for Hockley, Crosby, Lynn, Garza, Terry, Cochran.
Source: Texas Comptroller 2025 Total Tax Rates (comptroller.texas.gov/taxes/property-tax/rates/)
Combined rates = county + school district + countywide special districts (hospital, college, water, equalization).
Rates are per $100 valuation. City rates NOT included (rural unincorporated baseline).

Run: python seed_6county_districts.py
"""
from decimal import Decimal
from database import get_db, engine
from models.base import Base
from models.county import County
from models.tax_district import TaxDistrict

Base.metadata.create_all(bind=engine)

DISTRICTS = {
    "Hockley": [
        ("Anton ISD (Hockley Co.)", "2.0624"),
        ("Levelland ISD (Hockley Co.)", "1.8078"),
        ("Ropes ISD (Hockley Co.)", "1.8877"),
        ("Smyer ISD (Hockley Co.)", "1.5822"),
        ("Sundown ISD (Hockley Co.)", "1.7258"),
        ("Whitharral ISD (Hockley Co.)", "1.7922"),
    ],
    "Crosby": [
        ("Crosbyton CISD (Crosby Co.)", "1.9170"),
        ("Lorenzo ISD (Crosby Co.)", "1.5245"),
        ("Ralls ISD (Crosby Co.)", "1.5245"),
    ],
    "Lynn": [
        ("New Home ISD (Lynn Co.)", "1.9757"),
        ("O'Donnell ISD (Lynn Co.)", "2.0695"),
        ("Tahoka ISD (Lynn Co.)", "1.9616"),
        ("Wilson ISD (Lynn Co.)", "2.0034"),
    ],
    "Garza": [
        ("Post ISD (Garza Co.)", "2.0674"),
        ("Southland ISD (Garza Co.)", "1.6785"),
    ],
    "Terry": [
        ("Brownfield ISD (Terry Co.)", "2.4992"),
        ("Meadow ISD (Terry Co.)", "2.1062"),
        ("Wellman-Union CISD (Terry Co.)", "2.7989"),
    ],
    "Cochran": [
        ("Morton ISD (Cochran Co.)", "2.2329"),
        ("Whiteface CISD (Cochran Co.)", "2.2329"),
    ],
}


def seed():
    db = next(get_db())
    try:
        added = 0
        for county_name, districts in DISTRICTS.items():
            county = db.query(County).filter(County.county_name == county_name).first()
            if not county:
                print(f"WARNING: County '{county_name}' not found in database. Skipping.")
                continue

            existing = db.query(TaxDistrict).filter(TaxDistrict.county_id == county.id).count()
            if existing > 0:
                print(f"{county_name}: {existing} districts already exist. Skipping.")
                continue

            for name, rate in districts:
                db.add(TaxDistrict(
                    county_id=county.id,
                    name=name,
                    combined_rate_pct=Decimal(rate),
                    is_default=False,
                    is_active=True,
                ))
                added += 1
            print(f"{county_name}: added {len(districts)} districts.")

        db.commit()
        print(f"\nDone. {added} total districts added.")
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    seed()
