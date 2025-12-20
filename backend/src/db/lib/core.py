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
    """Save university education data with proper schema mapping."""
    payload = {
        "user_id": user_id,
        "university_name": data.get("universityName"),
        "university_program": data.get("universityProgram"),
    }
    # Handle numeric fields
    if gpa := data.get("universityGPA"):
        payload["gpa"] = float(gpa)
    if credits := data.get("creditsCompleted"):
        payload["credits_completed"] = int(credits)
    # Handle date field
    if eg := data.get("expectedGraduation"):
        payload["expected_graduation"] = date.fromisoformat(eg)  # "YYYY-MM-DD"
    # Handle optional fields
    if study_mode := data.get("studyMode"):
        payload["study_mode"] = study_mode
    if research_focus := data.get("researchFocus"):
        payload["research_focus"] = research_focus
    if portfolio_link := data.get("portfolioLink"):
        payload["portfolio_link"] = portfolio_link
    
    return supabase.table("university_education").upsert(payload).execute()

def save_high_school_edu(user_id: str, data: dict):
    """Save high school education data with proper schema mapping."""
    payload = {
        "user_id": user_id,
        "high_school_name": data.get("highSchoolName"),
    }
    # Handle numeric fields
    if gpa := data.get("highSchoolGPA"):
        payload["gpa"] = float(gpa)
    if gpa_scale := data.get("highSchoolGPAScale"):
        payload["gpa_scale"] = float(gpa_scale)
    if grad_year := data.get("highSchoolGradYear"):
        payload["grad_year"] = int(grad_year)
    # Handle optional fields
    if yks_placed := data.get("yksPlaced"):
        payload["yks_placed"] = yks_placed
    if extracurriculars := data.get("extracurriculars"):
        payload["extracurriculars"] = extracurriculars
    if scholarship_interest := data.get("scholarshipInterest"):
        payload["scholarship_interest"] = scholarship_interest
    
    return supabase.table("high_school_education").upsert(payload).execute()

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
