"""Application configuration."""
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://iaas:iaas@localhost:5432/iaas")
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-in-production")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7
