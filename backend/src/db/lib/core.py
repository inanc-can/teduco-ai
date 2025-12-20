from supabase import create_client
from uuid import uuid4
from datetime import date
from core.config import get_settings

settings = get_settings()
supabase = create_client(settings.supabase_url, settings.supabase_service_key)

# ---------- USERS ----------
def upsert_user(auth_uid: str, first_name: str, last_name: str, **extras):
    payload = {
        "user_id": auth_uid,
        "first_name": first_name,
        "last_name": last_name,
        **extras
    }
    return supabase.table("users").upsert(payload).execute()

# ---------- EDUCATION ----------
def save_university_edu(user_id: str, data: dict):
    parsed = data.copy()
    if dg := parsed.get("expected_graduation"):
        parsed["expected_graduation"] = date.fromisoformat(dg)  # "YYYY-MM-DD"
    if gpa := parsed.get("universityGPA"):
        parsed["gpa"] = float(gpa)
    return supabase.table("university_education").upsert(
        {"user_id": user_id, **parsed}
    ).execute()

# ---------- ONBOARDING PREFERENCES ----------
def save_onboarding_preferences(user_id: str, data: dict):
    payload = {
        "user_id": user_id,
        "desired_countries": data.get("desiredCountries", []),
        "desired_fields": data.get("desiredField", []),
        "target_programs": data.get("targetProgram", []),
        "preferred_intake": data.get("preferredIntake"),
        "preferred_support": data.get("preferredSupport"),
        "additional_notes": data.get("additionalNotes"),
    }
    return supabase.table("onboarding_preferences").upsert(payload).execute()

# ---------- DOCUMENTS ----------
def upload_document(user_id: str, fileobj, doc_type: str, mime: str):
    path = f"{user_id}/{uuid4()}"
    supabase.storage.from_(settings.supabase_bucket).upload(
        path, fileobj, {"content-type": mime}
    )
    meta = {
        "user_id": user_id,
        "doc_type": doc_type,
        "storage_path": path,
        "mime_type": mime,
    }
    return supabase.table("documents").insert(meta).execute()
