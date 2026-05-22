"""
alembic/env.py - Deterministic locked template v1.0.0
JARVIS - Never AI-generated.

Rules:
1. MUST import Base from models.base and set target_metadata = Base.metadata
2. DATABASE_URL from env var overrides alembic.ini — required for autogenerate
3. sys.path includes project root so model imports always work in subprocesses
4. Both run_migrations_offline() and run_migrations_online() implemented
5. Single try/except for Base import — no duplicate blocks
"""
import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# Ensure project root is on sys.path so models can be imported
_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# Import ORM metadata — required for --autogenerate to detect table changes
target_metadata = None
try:
    from models.base import Base
    target_metadata = Base.metadata
except Exception:
    pass

# Alembic Config object — provides access to alembic.ini values
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# DATABASE_URL env var overrides alembic.ini sqlalchemy.url
# This allows `alembic upgrade head` to work without editing alembic.ini
_db_url = os.environ.get("DATABASE_URL")
if _db_url:
    config.set_main_option("sqlalchemy.url", _db_url)


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    Configures the context with just a URL, without an Engine.
    Useful for generating SQL scripts without a live DB connection.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.

    Creates an Engine and associates a connection with the context.
    Standard mode for `alembic upgrade head` against a live database.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
