"""
Authentication router.
"""

from fastapi import APIRouter, HTTPException
from pydantic import EmailStr
from core.models import CamelCaseModel
from db.lib.core import supabase

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)


class LoginIn(CamelCaseModel):
    email: EmailStr
    password: str


@router.post("/login")
def login(credentials: LoginIn):
    """Authenticate user and return JWT tokens."""
    try:
        res = supabase.auth.sign_in_with_password(
            {"email": credentials.email, "password": credentials.password}
        )
        # send back the JWT and a refresh token
        return {
            "access_token": res.session.access_token,
            "refresh_token": res.session.refresh_token,
            "token_type": "bearer",
            "expires_in": res.session.expires_in,
        }
    except Exception as e:
        raise HTTPException(400, "Invalid email or password")
