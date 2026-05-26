"""
migrate_add_agent_profile_columns.py
Run ONCE to add brokerage_name + license_number columns to users table.
Safe to re-run — checks if columns exist before adding.

Usage (local): python migrate_add_agent_profile_columns.py
Usage (Render start cmd): python migrate_add_agent_profile_columns.py && python seed_hubcity.py && uvicorn main:app --host 0.0.0.0 --port $PORT
"""
import os
import sys
from sqlalchemy import create_engine, text, inspect

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)


def run_migration():
    """Add new columns to users and saved_sheets tables if missing."""
    inspector = inspect(engine)

    # -- Users table --
    if "users" in inspector.get_table_names():
        existing = {col["name"] for col in inspector.get_columns("users")}
        migrations = []
        if "brokerage_name" not in existing:
            migrations.append("ALTER TABLE users ADD COLUMN brokerage_name VARCHAR(255)")
        if "license_number" not in existing:
            migrations.append("ALTER TABLE users ADD COLUMN license_number VARCHAR(100)")
        if migrations:
            with engine.begin() as conn:
                for sql in migrations:
                    print(f"[MIGRATE] Running: {sql}")
                    conn.execute(text(sql))
            print(f"[MIGRATE] Users: added {len(migrations)} column(s)")
        else:
            print("[MIGRATE] Users: all columns exist")
    else:
        print("[MIGRATE] Users table not yet created — skipping")

    # -- Saved sheets table --
    if "saved_sheets" in inspector.get_table_names():
        existing = {col["name"] for col in inspector.get_columns("saved_sheets")}
        migrations = []
        if "client_signature" not in existing:
            migrations.append("ALTER TABLE saved_sheets ADD COLUMN client_signature TEXT")
        if "signed_at" not in existing:
            migrations.append("ALTER TABLE saved_sheets ADD COLUMN signed_at TIMESTAMP")
        if migrations:
            with engine.begin() as conn:
                for sql in migrations:
                    print(f"[MIGRATE] Running: {sql}")
                    conn.execute(text(sql))
            print(f"[MIGRATE] SavedSheets: added {len(migrations)} column(s)")
        else:
            print("[MIGRATE] SavedSheets: all columns exist")
    else:
        print("[MIGRATE] saved_sheets table not yet created — skipping")

    print("[MIGRATE] Done")


if __name__ == "__main__":
    run_migration()
