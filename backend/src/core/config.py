from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    supabase_url: str
    supabase_service_key: str
    supabase_bucket: str = "user-documents"

    class Config:
        # Look for .env in the backend directory (parent of src)
        env_file = str(Path(__file__).parent.parent.parent / ".env")
        # Allow both uppercase and lowercase environment variables
        case_sensitive = False
        # Ignore extra fields from .env file
        extra = "ignore"

@lru_cache
def get_settings():
    return Settings()
