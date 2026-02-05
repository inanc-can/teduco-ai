"""
Shared dependencies for FastAPI routers.
"""

import os
import logging
from fastapi import Header, HTTPException
from db.lib.core import supabase
from core.config import get_settings as get_app_settings
from typing import Optional

logger = logging.getLogger(__name__)


def verify_jwt_locally(token: str) -> Optional[str]:
    """
    Verify JWT token locally using the Supabase JWT secret.
    This is faster and more reliable than calling the Supabase API.
    
    Returns:
        User ID if valid, None if verification fails
    """
    jwt_secret = os.getenv("SUPABASE_JWT_SECRET")
    
    if not jwt_secret:
        logger.info("[AUTH] SUPABASE_JWT_SECRET not set, skipping local verification")
        return None
    
    logger.info(f"[AUTH] Attempting local JWT verification (secret len: {len(jwt_secret)})")
    
    try:
        from jose import jwt, JWTError
        
        # Supabase uses HS256 algorithm
        payload = jwt.decode(
            token,
            jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
        user_id = payload.get("sub")
        if user_id:
            logger.info(f"[AUTH] JWT verified locally for user: {user_id}")
            return user_id
        logger.warning("[AUTH] JWT payload missing 'sub' claim")
        return None
    except JWTError as e:
        logger.warning(f"[AUTH] Local JWT verification failed (JWTError): {e}")
        return None
    except Exception as e:
        # Log but don't raise - we'll fall back to Supabase API
        logger.warning(f"[AUTH] Local JWT verification error: {type(e).__name__}: {e}")
        return None


def get_current_user(
    authorization: str = Header(..., description="Bearer <token>")
) -> str:
    """
    Extract and validate user from Authorization header.
    
    First tries local JWT verification (faster), then falls back to Supabase API.
    
    Returns:
        User ID (Supabase UID string)
    """
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer":
        raise HTTPException(401, "Invalid auth scheme")

    logger.info(f"[AUTH] Processing auth request (token len: {len(token)})")

    # First, try local JWT verification (faster and doesn't require network)
    user_id = verify_jwt_locally(token)
    if user_id:
        return user_id

    # Fallback: Verify the JWT token with Supabase API
    try:
        logger.info("[AUTH] Falling back to Supabase API verification")
        user = supabase.auth.get_user(token)
        if user is None or user.user is None:
            raise HTTPException(401, "Invalid or expired token")
        logger.info(f"[AUTH] Supabase API verified user: {user.user.id}")
        return user.user.id  # Supabase UID (uuid string)
    except HTTPException:
        raise
    except Exception as e:
        error_str = str(e).lower()
        if "403" in error_str or "forbidden" in error_str:
            logger.warning("[AUTH] Supabase returned 403 - token may be expired")
            raise HTTPException(401, "Token expired. Please log in again.")
        logger.error(f"[AUTH] Supabase verification error: {e}")
        raise HTTPException(401, "Invalid or expired token")


def get_optional_current_user(
    authorization: str = Header(None, description="Bearer <token>")
) -> Optional[str]:
    """
    Optional version of `get_current_user` that returns `None` when no Authorization header
    is provided (or when the token is invalid). This allows endpoints to accept both
    authenticated and anonymous requests without changing the frontend.
    """
    if not authorization:
        return None
    try:
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer":
            return None
        
        # First, try local JWT verification
        user_id = verify_jwt_locally(token)
        if user_id:
            return user_id
        
        # Fallback to Supabase API
        user = supabase.auth.get_user(token)
        if user is None or user.user is None:
            return None
        return user.user.id
    except Exception:
        return None


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
