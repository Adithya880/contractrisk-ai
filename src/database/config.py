"""
Database Configuration Module for ContractRisk AI.
Provides centralized environment configuration and SQLAlchemy database connection URL construction.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file if available
env_path = Path(".env")
if env_path.exists():
    load_dotenv(dotenv_path=env_path)


class DatabaseSettings:
    """Centralized database configuration settings."""

    def __init__(self):
        self.postgres_host: str = os.getenv("POSTGRES_HOST", "localhost")
        self.postgres_port: str = os.getenv("POSTGRES_PORT", "5432")
        self.postgres_db: str = os.getenv("POSTGRES_DB", "contractrisk")
        self.postgres_user: str = os.getenv("POSTGRES_USER", "postgres")
        self.postgres_password: str = os.getenv("POSTGRES_PASSWORD", "")
        self.raw_database_url: str = os.getenv("DATABASE_URL", "")

    @property
    def database_url(self) -> str:
        """
        Construct or return SQLAlchemy 2.x connection URL.
        Defaults to postgresql+psycopg driver.
        """
        if self.raw_database_url.strip():
            url = self.raw_database_url.strip()
            # Normalize driver prefix if needed
            if url.startswith("postgresql://"):
                url = url.replace("postgresql://", "postgresql+psycopg://", 1)
            return url

        # Construct from individual parameters
        user_pass = self.postgres_user
        if self.postgres_password:
            user_pass += f":{self.postgres_password}"

        return f"postgresql+psycopg://{user_pass}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"


settings = DatabaseSettings()
