import os
from datetime import timedelta


def normalize_database_url(value):
    if value.startswith("postgres://"):
        return value.replace("postgres://", "postgresql+psycopg://", 1)
    if value.startswith("postgresql://"):
        return value.replace("postgresql://", "postgresql+psycopg://", 1)
    return value


class Config:
    SQLALCHEMY_DATABASE_URI = normalize_database_url(os.getenv("DATABASE_URL", ""))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "pool_size": int(os.getenv("DB_POOL_SIZE", "5")),
        "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "10")),
    }
    JWT_SECRET = os.getenv("JWT_SECRET", "")
    CRON_SECRET = os.getenv("CRON_SECRET", "")
    X_CLIENT_ID = os.getenv("X_CLIENT_ID", "")
    X_CLIENT_SECRET = os.getenv("X_CLIENT_SECRET", "")
    X_BEARER_TOKEN = os.getenv("X_BEARER_TOKEN", "")
    X_REDIRECT_URI = os.getenv("X_REDIRECT_URI", "http://localhost:5000/api/x/oauth/callback")
    ALLOWED_ORIGINS = [
        value.strip() for value in os.getenv("ALLOWED_ORIGINS", "").split(",") if value.strip()
    ]
    ACCESS_TOKEN_TTL = timedelta(minutes=int(os.getenv("ACCESS_TOKEN_MINUTES", "15")))
    REFRESH_TOKEN_TTL = timedelta(days=int(os.getenv("REFRESH_TOKEN_DAYS", "30")))
    FEED_CACHE_TTL = timedelta(minutes=int(os.getenv("FEED_CACHE_MINUTES", "15")))
    OAUTH_STATE_TTL = timedelta(minutes=10)
    RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI", "")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    FORCE_HTTPS = os.getenv("FORCE_HTTPS", "false").lower() == "true"

    @classmethod
    def validate(cls):
        required = {
            "DATABASE_URL": cls.SQLALCHEMY_DATABASE_URI,
            "JWT_SECRET": cls.JWT_SECRET,
            "CRON_SECRET": cls.CRON_SECRET,
            "ALLOWED_ORIGINS": cls.ALLOWED_ORIGINS,
            "RATELIMIT_STORAGE_URI": cls.RATELIMIT_STORAGE_URI,
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")
        if len(cls.JWT_SECRET) < 32:
            raise RuntimeError("JWT_SECRET must contain at least 32 characters")
        if "*" in cls.ALLOWED_ORIGINS:
            raise RuntimeError("ALLOWED_ORIGINS must list explicit trusted origins")


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = normalize_database_url(
        os.getenv("TEST_DATABASE_URL", "sqlite+pysqlite:///:memory:")
    )
    SQLALCHEMY_ENGINE_OPTIONS = {}
    JWT_SECRET = "test-secret-that-is-at-least-thirty-two-characters"
    CRON_SECRET = "test-cron-secret"
    X_CLIENT_ID = "test-client"
    X_CLIENT_SECRET = "test-client-secret"
    X_BEARER_TOKEN = "test-bearer"
    ALLOWED_ORIGINS = ["chrome-extension://test"]
    RATELIMIT_ENABLED = False
    RATELIMIT_STORAGE_URI = "memory://"
    FORCE_HTTPS = False
