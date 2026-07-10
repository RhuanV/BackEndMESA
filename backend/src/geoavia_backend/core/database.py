"""Database configuration: loads environment variables and builds connection URLs.

Sandbox and production are isolated at the database level: when APP_ENV=sandbox
the app connects to a dedicated sandbox database, so data created there never
leaks into the production database. Any other APP_ENV value (fail-safe default
"production") uses the main database. APP_ENV is read once per process — restart
the backend after changing it.
"""
import logging
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("geoavia.startup")

DB_HOST = os.getenv("DB_HOST", "db")
DB_NAME = os.getenv("DB_NAME")
SANDBOX_DB_NAME = os.getenv("SANDBOX_DB_NAME", "geoavia_sandbox_db")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")

# Environment resolves which database is active. Unknown values fail safe to the
# main (production) database. Kept in sync with core.sandbox.SANDBOX_ENV.
APP_ENV = os.getenv("APP_ENV", "production").strip().lower()
ACTIVE_DB_NAME = SANDBOX_DB_NAME if APP_ENV == "sandbox" else DB_NAME

# Use the external port when running locally; otherwise the internal port.
if DB_HOST in ("localhost", "127.0.0.1"):
    DB_PORT = os.getenv("DB_EXT_PORT", "5433")
else:
    DB_PORT = os.getenv("DB_PORT", "5432")

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
FRONTEND_PORT = os.getenv("FRONTEND_PORT", "5173")
DEV_USER = os.getenv("DEV_USER", "admin")

# Extra allowed CORS origins (comma-separated). Empty falls back to the local
# frontend only. Configure this for staging/production domains.
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]

# Connection string used by the repository layer via psycopg2.
DATABASE_URL = f"host={DB_HOST} dbname={ACTIVE_DB_NAME} user={DB_USER} password={DB_PASS} port={DB_PORT}"

# SQLAlchemy-format URL used by Alembic — same active database, so migrations
# apply to whichever environment the backend booted in.
SQLALCHEMY_DATABASE_URL = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{ACTIVE_DB_NAME}"
)

# Observability: record the active environment and database (never credentials).
logger.info("Active environment: APP_ENV=%s, database=%s", APP_ENV, ACTIVE_DB_NAME)