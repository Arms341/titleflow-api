"""
config.py - Canonical locked template v1.0.3
JARVIS Locked File Library — DO NOT MODIFY WITHOUT UPDATING VERSION

Rules enforced by this template:
1. import os and import logging FIRST
2. ALL module-level constants (JWT_SECRET, SECRET_KEY, ALGORITHM, etc.)
   defined BEFORE Settings class — critical: Settings fields reference them
   at class-definition time, not instance time.
3. Settings(BaseSettings) with all required fields
4. get_settings() cached with @lru_cache
5. ConfigError(Exception) always present for downstream error handling
6. Pydantic v2 compatible — uses model_config instead of nested Config class

CHANGE LOG:
  v1.0.3 - REMOVED type annotations from module-level constants. 
           `JWT_SECRET: str = ...` produces AnnAssign AST nodes which the
           IMPORT-GRAPH scanner misses (it only finds Assign nodes).
           Changed to `JWT_SECRET = ...` so scanner sees them as exports.
           This was causing 'Symbol JWT_SECRET not found in module config'
           and blocking 3 downstream files every build.
  v1.0.2 - Added JWT_SECRET + SECRET_KEY to module-level constants block.
           IMP4-RECONCILE was stripping them post-load, causing NameError:
           'SECRET_KEY' is not defined at Settings class import time.
  v1.0.1 - Initial locked template.
"""
import logging
import os
from functools import lru_cache
from typing import Optional

try:
    from pydantic_settings import BaseSettings
    from pydantic import ConfigDict
except ImportError:
    from pydantic import BaseSettings  # type: ignore
    ConfigDict = None  # type: ignore

logger = logging.getLogger(__name__)

# ── Module-level constants ───────────────────────────────────────────────────
# ALL constants must be defined here, BEFORE the Settings class.
# Settings fields use these as default values at class-definition time.
# Files that do `from config import JWT_SECRET` also depend on these.
# v1.0.3: NO type annotations — AnnAssign nodes are invisible to IMPORT-GRAPH.
JWT_SECRET = os.getenv("JWT_SECRET", "change-me-in-production")
SECRET_KEY = JWT_SECRET  # alias — some files import SECRET_KEY directly
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
API_VERSION = os.getenv("API_VERSION", "1.0.0")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", str(10 * 1024 * 1024)))  # 10 MB


class ConfigError(Exception):
    """Raised when configuration is invalid or a required value is missing."""

    def __init__(self, message: str = "ConfigError", **kwargs):
        super().__init__(message)
        self.kwargs = kwargs


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Reads .env file if present. All fields have safe defaults so the
    application starts without a configured environment during development.
    """

    # Use Pydantic v2 model_config when available, fall back to nested Config
    if ConfigDict is not None:
        model_config = ConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            case_sensitive=False,
            extra="ignore",
        )
    else:
        class Config:  # Pydantic v1 fallback
            env_file = ".env"
            env_file_encoding = "utf-8"
            case_sensitive = False

    # Application
    app_name: str = os.getenv("APP_NAME", "JARVIS App")
    debug: bool = DEBUG
    api_version: str = API_VERSION

    # Database
    database_url: str = DATABASE_URL

    # Auth / Security — these reference module-level constants defined above
    secret_key: str = SECRET_KEY
    jwt_secret: str = JWT_SECRET
    algorithm: str = ALGORITHM
    access_token_expire_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES

    # Redis / Cache
    redis_url: str = REDIS_URL
    redis_host: str = os.getenv("REDIS_HOST", "localhost")
    redis_port: int = int(os.getenv("REDIS_PORT", "6379"))
    redis_db: int = int(os.getenv("REDIS_DB", "0"))
    redis_password: Optional[str] = os.getenv("REDIS_PASSWORD") or None
    redis_socket_timeout: int = int(os.getenv("REDIS_SOCKET_TIMEOUT", "5"))

    # Storage
    max_file_size: int = MAX_FILE_SIZE
    s3_bucket_name: Optional[str] = os.getenv("S3_BUCKET_NAME") or None
    s3_region: str = os.getenv("S3_REGION", "us-east-1")
    aws_access_key_id: Optional[str] = os.getenv("AWS_ACCESS_KEY_ID") or None
    aws_secret_access_key: Optional[str] = os.getenv("AWS_SECRET_ACCESS_KEY") or None

    # Email
    email_host: str = os.getenv("EMAIL_HOST", "")
    email_port: int = int(os.getenv("EMAIL_PORT", "587"))
    email_username: str = os.getenv("EMAIL_USERNAME", "")
    email_password: str = os.getenv("EMAIL_PASSWORD", "")

    # Celery / Tasks
    celery_broker_url: str = os.getenv("CELERY_BROKER_URL", REDIS_URL)
    celery_result_backend: str = os.getenv("CELERY_RESULT_BACKEND", REDIS_URL)


@lru_cache()
def get_settings() -> Settings:
    """
    Return the cached Settings instance loaded from environment.

    Reads: environment variables and .env file.
    Returns: Settings singleton (cached after first call).
    Raises: ConfigError if settings cannot be loaded.
    """
    try:
        return Settings()
    except Exception as exc:
        logger.error(f"[CONFIG] Failed to load settings: {exc}")
        raise ConfigError(f"Invalid configuration: {exc}") from exc


def load_config() -> dict:
    """Return config as a plain dict for serialisation or logging."""
    s = get_settings()
    return {
        "database_url": s.database_url,
        "debug": s.debug,
        "secret_key": "***",
        "algorithm": s.algorithm,
        "access_token_expire_minutes": s.access_token_expire_minutes,
        "redis_url": s.redis_url,
    }


def validate_config() -> bool:
    """
    Validate that required config values are present and non-empty.

    Returns: True if valid. Raises: ConfigError listing missing fields.
    """
    required = ["database_url", "secret_key"]
    s = get_settings()
    missing = [k for k in required if not getattr(s, k, None)]
    if missing:
        raise ConfigError(f"Missing required settings: {missing}")
    return True
