from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from backend.src.db.lib.core import supabase

router = APIRouter(prefix="/auth", tags=["auth"])

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    fname: str
    lname: str

@router.post("/signup")
def signup(payload: UserCreate):
    # 1) create Supabase auth user
    res = supabase.auth.admin.create_user(
        {
            "email": payload.email,
            "password": payload.password,
            "email_confirm": True,
        }
    )
    if res.error:
        raise HTTPException(400, res.error.message)

    uid = res.user.id
    # 2) insert the profile row
    supabase.table("users").insert(
        {
            "user_id": uid,
            "first_name": payload.fname,
            "last_name": payload.lname,
        }
    ).execute()

    return {"user_id": uid}
