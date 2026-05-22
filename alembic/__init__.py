# Local alembic package — exposes env module only.
# Do NOT import from the alembic pip package here (circular).
try:
    from . import env
except Exception:
    pass
