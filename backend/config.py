"""
Configuration module — loads environment variables via Pydantic Settings.
"""

from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from .env file."""

    GEE_SERVICE_ACCOUNT_EMAIL: str
    GEE_KEY_FILE_PATH: str
    GEE_PROJECT_ID: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def gee_key_absolute_path(self) -> str:
        """Resolve the GEE key file path relative to the backend directory."""
        key_path = Path(self.GEE_KEY_FILE_PATH)
        if key_path.is_absolute():
            return str(key_path)
        # Resolve relative to this config file's parent (backend/)
        return str(Path(__file__).parent / key_path)


settings = Settings()
