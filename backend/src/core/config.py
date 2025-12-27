from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    supabase_url: str
    supabase_service_key: str
    supabase_bucket: str = "user-documents"

    class Config:
        env_file = ".env"
        # Allow both uppercase and lowercase environment variables
        case_sensitive = False

@lru_cache
def get_settings():
    return Settings()
