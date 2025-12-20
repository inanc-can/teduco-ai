from fastapi import FastAPI, HTTPException, Depends, Header, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import List
import os
from uuid import uuid4
from db.lib.core import upsert_user, save_university_edu, upload_document, supabase
from core.config import get_settings

app = FastAPI(title="Teduco API", version="0.1.0")

# CORS configuration for frontend
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# auxillary function to get current user from Authorization header
def get_current_user(
    authorization: str = Header(..., description="Bearer <token>")
):
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


# auxillary function, this shall be used to display an already uploaded document to user (if we need to)
def get_signed_url(path: str, expires_sec: int = 60):
    settings = get_settings()
    res = (
        supabase.storage.from_(settings.supabase_bucket)
        .create_signed_url(path, expires_sec)
    )
    return res["signedURL"]



@app.post("/onboarding/profile")
def onboarding_profile(payload: dict, user_id: str = Depends(get_current_user)):
    upsert_user(
        user_id,
        payload["firstName"],
        payload["lastName"],
        phone=payload.get("phone"),
        applicant_type=payload.get("applicantType"),
        current_city=payload.get("currentCity")
    )
    save_university_edu(user_id, payload)  # silently ignores hs fields
    return {"status": "ok"}

@app.post("/documents")
def add_document(
    doc_type: str,
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user)
):
    upload_document(user_id, file.file, doc_type, file.content_type)
    return {"status": "uploaded"}

class LoginIn(BaseModel):
    email: EmailStr
    password: str

@app.post("/auth/login")
def login(credentials: LoginIn):
    res = supabase.auth.sign_in_with_password(
        {"email": credentials.email, "password": credentials.password}
    )
    if res.error:
        raise HTTPException(400, res.error.message)

    # send back the JWT and a refresh token
    return {
        "access_token": res.session.access_token,
        "refresh_token": res.session.refresh_token,
        "token_type": "bearer",
        "expires_in": res.session.expires_in,
    }