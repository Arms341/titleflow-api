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
    """Add brokerage_name and license_number columns to users table if missing."""
    inspector = inspect(engine)

    if "users" not in inspector.get_table_names():
        print("[MIGRATE] users table does not exist yet — skipping (create_all will handle it)")
        return

    existing_columns = {col["name"] for col in inspector.get_columns("users")}
    migrations = []

    if "brokerage_name" not in existing_columns:
        migrations.append("ALTER TABLE users ADD COLUMN brokerage_name VARCHAR(255)")
    if "license_number" not in existing_columns:
        migrations.append("ALTER TABLE users ADD COLUMN license_number VARCHAR(100)")

    if not migrations:
        print("[MIGRATE] All columns already exist — nothing to do")
        return

    with engine.begin() as conn:
        for sql in migrations:
            print(f"[MIGRATE] Running: {sql}")
            conn.execute(text(sql))

    print(f"[MIGRATE] Done — added {len(migrations)} column(s)")


if __name__ == "__main__":
    run_migration()
