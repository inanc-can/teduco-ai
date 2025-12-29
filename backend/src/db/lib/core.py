from supabase import create_client
from uuid import uuid4
from datetime import date, datetime
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
    # Handle date field - parse common formats
    if eg := data.get("expectedGraduation"):
        try:
            # Try ISO format first (YYYY-MM-DD)
            parsed = date.fromisoformat(eg)
            payload["expected_graduation"] = parsed.isoformat()
        except ValueError:
            try:
                # Try parsing "September 2026" or "June 2025" format
                parsed_date = datetime.strptime(eg, "%B %Y")
                # Use first day of the month and convert to ISO string
                payload["expected_graduation"] = parsed_date.date().isoformat()
            except ValueError:
                # Skip if unparseable
                pass
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

# ---------- GET USER DATA ----------
def get_user_profile(user_id: str):
    """Get complete user profile including education and preferences."""
    result = {
        "user": None,
        "education": None,
        "preferences": None
    }
    
    # Get user basic info
    user_res = supabase.table("users").select("*").eq("user_id", user_id).execute()
    if user_res.data:
        result["user"] = user_res.data[0]
    
    # Get education info (try both tables)
    hs_res = supabase.table("high_school_education").select("*").eq("user_id", user_id).execute()
    if hs_res.data:
        result["education"] = {"type": "high-school", **hs_res.data[0]}
    else:
        uni_res = supabase.table("university_education").select("*").eq("user_id", user_id).execute()
        if uni_res.data:
            result["education"] = {"type": "university", **uni_res.data[0]}
    
    # Get preferences
    pref_res = supabase.table("onboarding_preferences").select("*").eq("user_id", user_id).execute()
    if pref_res.data:
        result["preferences"] = pref_res.data[0]
    
    return result

# ---------- DOCUMENTS ----------
def upload_document(user_id: str, fileobj, doc_type: str, mime: str):
    try:
        path = f"{user_id}/{uuid4()}"
        
        # Read file content as bytes
        file_content = fileobj.read()
        
        # Reset file pointer in case it's needed again
        if hasattr(fileobj, 'seek'):
            fileobj.seek(0)
        
        # Upload to Supabase Storage
        storage_result = supabase.storage.from_(settings.supabase_bucket).upload(
            path, file_content, {"content-type": mime}
        )
        
        # Check for storage errors
        if hasattr(storage_result, 'error') and storage_result.error:
            raise Exception(f"Storage upload failed: {storage_result.error}")
        
        # Insert metadata into database
        meta = {
            "user_id": user_id,
            "doc_type": doc_type,
            "storage_path": path,
            "mime_type": mime,
        }
        db_result = supabase.table("documents").insert(meta).execute()
        
        # Check for database errors
        if hasattr(db_result, 'error') and db_result.error:
            # Rollback: delete the uploaded file
            supabase.storage.from_(settings.supabase_bucket).remove([path])
            raise Exception(f"Database insert failed: {db_result.error}")
        
        return db_result
    except Exception as e:
        print(f"Error in upload_document: {str(e)}")
        raise

def get_user_documents(user_id: str):
    """Get all documents for a user"""
    return supabase.table("documents").select("*").eq("user_id", user_id).execute()

def delete_document(document_id: str, user_id: str):
    """Delete a document from storage and database"""
    # First get the document to get its storage path
    doc_res = supabase.table("documents").select("*").eq("document_id", document_id).eq("user_id", user_id).execute()
    
    if not doc_res.data:
        raise ValueError("Document not found or access denied")
    
    storage_path = doc_res.data[0]["storage_path"]
    
    # Delete from storage
    supabase.storage.from_(settings.supabase_bucket).remove([storage_path])
    
    # Delete from database
    return supabase.table("documents").delete().eq("document_id", document_id).eq("user_id", user_id).execute()
