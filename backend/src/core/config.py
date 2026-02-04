from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra='ignore'  # Ignore extra env vars not in schema
    )
    
    supabase_url: str
    supabase_service_key: str
    supabase_bucket: str = "user-documents"

@lru_cache
def get_settings():
    return Settings()
