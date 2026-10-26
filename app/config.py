import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:CHANGE_ME@localhost:5432/production_events",
)
JWT_SECRET = os.getenv("JWT_SECRET", "development-only-change-me")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))

SCANNER_USERNAME = os.getenv("SCANNER_USERNAME", "scanner")
SCANNER_PASSWORD = os.getenv("SCANNER_PASSWORD", "scanner-dev-password")
MANAGER_USERNAME = os.getenv("MANAGER_USERNAME", "manager")
MANAGER_PASSWORD = os.getenv("MANAGER_PASSWORD", "manager-dev-password")