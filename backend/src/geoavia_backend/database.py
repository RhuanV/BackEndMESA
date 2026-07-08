"""
Database configuration module.
Responsible for loading environment variables and building the connection string 
for the repository layer to connect to PostgreSQL.
"""
import os
from dotenv import load_dotenv

# Loads variables from the .env file into the system environment
load_dotenv()

# Retrieves each variable individually
DB_HOST = os.getenv("DB_HOST", "db")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")

# Smart port resolution: uses external port if running locally, otherwise internal port
if DB_HOST in ("localhost", "127.0.0.1"):
    DB_PORT = os.getenv("DB_EXT_PORT", "5433")
else:
    DB_PORT = os.getenv("DB_PORT", "5432")

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
FRONTEND_PORT = os.getenv("FRONTEND_PORT", "5173")
DEV_USER = os.getenv("DEV_USER", "admin")

# Builds the connection string (example for psycopg2)
DATABASE_URL = f"host={DB_HOST} dbname={DB_NAME} user={DB_USER} password={DB_PASS} port={DB_PORT}"

# SQLAlchemy-format URL used by Alembic; the rest of the codebase keeps using DATABASE_URL via psycopg2
SQLALCHEMY_DATABASE_URL = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)