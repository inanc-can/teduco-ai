"""
Shared dependencies for FastAPI routers.
"""

from fastapi import Header, HTTPException
from db.lib.core import supabase
from core.config import get_settings as get_app_settings


def get_current_user(
    authorization: str = Header(..., description="Bearer <token>")
) -> str:
    """
    Extract and validate user from Authorization header.
    
    Returns:
        User ID (Supabase UID string)
    """
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer":
        raise HTTPException(401, "Invalid auth scheme")

    # Verify the JWT token with Supabase
    try:
        user = supabase.auth.get_user(token)
        if user is None:
            raise HTTPException(401, "Invalid or expired token")
        return user.user.id  # Supabase UID (uuid string)
    except Exception:
        raise HTTPException(401, "Invalid or expired token")


def get_signed_url(path: str, expires_sec: int = 60) -> str:
    """
    Generate a signed URL for a storage path.
    
    Args:
        path: Storage path
        expires_sec: URL expiration in seconds
        
    Returns:
        Signed URL string
    """
    settings = get_app_settings()
    res = (
        supabase.storage.from_(settings.supabase_bucket)
        .create_signed_url(path, expires_sec)
    )
    return res["signedURL"]
