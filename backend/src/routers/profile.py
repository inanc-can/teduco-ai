"""
Profile, settings, and onboarding router.
"""

from fastapi import APIRouter, BackgroundTasks, Depends
from core.dependencies import get_current_user
from core.schemas import UserProfileResponse, UserProfileUpdate
from db.lib.core import (
    upsert_user,
    save_university_edu,
    save_high_school_edu,
    save_onboarding_preferences,
    get_user_profile,
    supabase
)

router = APIRouter(
    tags=["profile"]
)


def _embed_user_profile_background(user_id: str):
    """Background task: generate a text summary of the user profile, embed it, store in rag_user_profile_chunks."""
    try:
        from rag.chatbot.db_ops import upsert_user_profile_chunks
        from langchain_core.documents import Document
        from langchain_huggingface import HuggingFaceEmbeddings

        profile = get_user_profile(user_id)
        if not profile or not profile.get("user"):
            return

        user = profile["user"]
        edu = profile.get("education", {}) or {}
        prefs = profile.get("preferences", {}) or {}

        # Build a rich text summary of the user profile
        parts = []
        parts.append(f"Student Profile: {user.get('first_name', '')} {user.get('last_name', '')}")
        if user.get("applicant_type"):
            parts.append(f"Applicant Type: {user['applicant_type']}")
        if user.get("current_city"):
            parts.append(f"Location: {user['current_city']}")

        if edu.get("type") == "university":
            parts.append(f"University: {edu.get('university_name', '')}")
            parts.append(f"Program: {edu.get('university_program', '')}")
            if edu.get("gpa"):
                parts.append(f"GPA: {edu['gpa']}")
            if edu.get("credits_completed"):
                parts.append(f"Credits: {edu['credits_completed']}")
            if edu.get("expected_graduation"):
                parts.append(f"Expected Graduation: {edu['expected_graduation']}")
            if edu.get("research_focus"):
                parts.append(f"Research Focus: {edu['research_focus']}")
            if edu.get("portfolio_link"):
                parts.append(f"Portfolio: {edu['portfolio_link']}")
        elif edu.get("type") == "high-school":
            parts.append(f"High School: {edu.get('high_school_name', '')}")
            if edu.get("gpa"):
                parts.append(f"GPA: {edu['gpa']}/{edu.get('gpa_scale', '')}")
            if edu.get("grad_year"):
                parts.append(f"Graduation Year: {edu['grad_year']}")
            if edu.get("extracurriculars"):
                parts.append(f"Extracurriculars: {edu['extracurriculars']}")

        if prefs.get("desired_countries"):
            parts.append(f"Desired Countries: {', '.join(prefs['desired_countries'])}")
        if prefs.get("desired_fields"):
            parts.append(f"Desired Fields: {', '.join(prefs['desired_fields'])}")
        if prefs.get("target_programs"):
            parts.append(f"Target Programs: {', '.join(prefs['target_programs'])}")
        if prefs.get("additional_notes"):
            parts.append(f"Notes: {prefs['additional_notes']}")

        summary_text = "\n".join(parts)
        docs = [Document(page_content=summary_text, metadata={"source": "user_profile", "user_id": user_id})]

        import pathlib
        cache_dir = "/app/.hf_cache" if pathlib.Path("/app/.hf_cache").exists() else None
        embeddings_model = HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            **({"cache_folder": cache_dir} if cache_dir else {}),
            encode_kwargs={"normalize_embeddings": True},
            model_kwargs={"device": "cpu"},
        )
        chunk_embeddings = embeddings_model.embed_documents([summary_text])
        upsert_user_profile_chunks(user_id, docs, chunk_embeddings)
        print(f"[PROFILE EMBED] Embedded profile for user {user_id}")

    except Exception as e:
        import traceback
        print(f"[PROFILE EMBED] Error: {e}")
        traceback.print_exc()


def _build_profile_response(user_id: str) -> UserProfileResponse:
    """Build profile response from database data."""
    try:
        raw_profile = get_user_profile(user_id)
        
        # Handle case where user doesn't exist yet (new users during onboarding)
        if not raw_profile or not raw_profile.get("user"):
            return UserProfileResponse(
                first_name="",
                last_name="",
                onboarding_completed=False
            )
        
        # Flatten the nested structure into a single dict
        result = {}
        
        # Add basic user info
        if raw_profile.get("user"):
            user_data = raw_profile["user"]
            result.update({
                "first_name": user_data.get("first_name", ""),
                "last_name": user_data.get("last_name", ""),
                "phone": user_data.get("phone"),
                "applicant_type": user_data.get("applicant_type"),
                "current_city": user_data.get("current_city"),
                "onboarding_completed": user_data.get("onboarding_completed", False),
            })
    except Exception as e:
        # Log the error and return minimal profile for new users
        import traceback
        print(f"[PROFILE] Error building profile response: {e}")
        traceback.print_exc()
        return UserProfileResponse(
            first_name="",
            last_name="",
            onboarding_completed=False
        )
    
    # Add education info
    if raw_profile.get("education"):
        edu_data = raw_profile["education"]
        edu_type = edu_data.get("type")
        
        if edu_type == "high-school":
            result.update({
                "high_school_name": edu_data.get("high_school_name"),
                "high_school_gpa": edu_data.get("gpa"),
                "high_school_gpa_scale": edu_data.get("gpa_scale"),
                "high_school_grad_year": edu_data.get("grad_year"),
                "yks_placed": edu_data.get("yks_placed"),
            })
        elif edu_type == "university":
            result.update({
                "university_name": edu_data.get("university_name"),
                "university_program": edu_data.get("university_program"),
                "university_gpa": edu_data.get("gpa"),
                "credits_completed": edu_data.get("credits_completed"),
                "expected_graduation": edu_data.get("expected_graduation"),
                "study_mode": edu_data.get("study_mode"),
                "research_focus": edu_data.get("research_focus"),
                "portfolio_link": edu_data.get("portfolio_link"),
            })
    
    # Add preferences
    if raw_profile.get("preferences"):
        pref_data = raw_profile["preferences"]
        result.update({
            "desired_countries": pref_data.get("desired_countries", []),
            "desired_field": pref_data.get("desired_fields", []),  # Map plural to singular
            "target_program": pref_data.get("target_programs", []),  # Map plural to singular
            "preferred_intake": pref_data.get("preferred_intake"),
            "preferred_support": pref_data.get("preferred_support"),
            "additional_notes": pref_data.get("additional_notes"),
        })
    
    return UserProfileResponse(**result)


def _update_profile_data(user_id: str, payload: UserProfileUpdate) -> dict:
    """Update profile data in database."""
    # Convert to dict with snake_case keys (Pydantic does this automatically)
    data = payload.model_dump(exclude_none=True)
    
    # Update user profile if basic fields are present
    if any(k in data for k in ["first_name", "last_name", "phone", "applicant_type", "current_city"]):
        upsert_user(
            user_id,
            data.get("first_name"),
            data.get("last_name"),
            phone=data.get("phone"),
            applicant_type=data.get("applicant_type"),
            current_city=data.get("current_city")
        )
    
    # Save education info based on applicant type (only if relevant fields are present)
    applicant_type = data.get("applicant_type")
    university_fields = ["university_name", "university_program", "university_gpa", "credits_completed", "expected_graduation", "study_mode", "research_focus", "portfolio_link"]
    high_school_fields = ["high_school_name", "high_school_gpa", "high_school_gpa_scale", "high_school_grad_year", "yks_placed"]
    
    if applicant_type == "university" and any(k in data for k in university_fields):
        save_university_edu(user_id, data)
    elif applicant_type == "high-school" and any(k in data for k in high_school_fields):
        save_high_school_edu(user_id, data)
    
    # Save onboarding preferences if any are present
    pref_fields = ["desired_countries", "desired_field", "target_program", "preferred_intake", "preferred_support", "additional_notes"]
    if any(k in data for k in pref_fields):
        save_onboarding_preferences(user_id, data)
    
    return {"message": "ok", "user_id": user_id}


# ============= PROFILE ENDPOINTS =============

@router.get("/profile", response_model=UserProfileResponse)
def get_profile(user_id: str = Depends(get_current_user)):
    """Get user profile data in camelCase format."""
    return _build_profile_response(user_id)


@router.put("/profile")
def update_profile(payload: UserProfileUpdate, user_id: str = Depends(get_current_user)):
    """Update user profile. Pydantic automatically converts camelCase to snake_case."""
    return _update_profile_data(user_id, payload)


# ============= SETTINGS ENDPOINTS (Aliases for profile) =============

@router.get("/settings", response_model=UserProfileResponse)
def get_settings(user_id: str = Depends(get_current_user)):
    """Get user settings (alias for profile)."""
    return _build_profile_response(user_id)


@router.patch("/settings")
def update_settings(payload: UserProfileUpdate, user_id: str = Depends(get_current_user)):
    """Update user settings (alias for profile)."""
    return _update_profile_data(user_id, payload)


@router.put("/settings")
def update_settings_put(payload: UserProfileUpdate, user_id: str = Depends(get_current_user)):
    """Update user settings via PUT (alias for profile)."""
    return _update_profile_data(user_id, payload)


# ============= ONBOARDING ENDPOINTS =============

@router.get("/onboarding")
def get_onboarding_status(user_id: str = Depends(get_current_user)):
    """Get onboarding status for the current user."""
    user_res = supabase.table("users").select("onboarding_completed").eq("user_id", user_id).execute()
    
    if not user_res.data or len(user_res.data) == 0:
        return {"onboarding_completed": False}
    
    return {"onboarding_completed": user_res.data[0].get("onboarding_completed", False)}


@router.post("/onboarding")
def onboarding(
    payload: UserProfileUpdate,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user)
):
    """Onboarding endpoint (calls update_profile, then embeds profile for RAG)."""
    result = _update_profile_data(user_id, payload)
    # Embed the profile in the background for RAG retrieval
    background_tasks.add_task(_embed_user_profile_background, user_id)
    return result


@router.post("/onboarding/profile")
def onboarding_profile(payload: UserProfileUpdate, user_id: str = Depends(get_current_user)):
    """Legacy onboarding profile endpoint."""
    data = payload.model_dump(exclude_none=True)
    upsert_user(
        user_id,
        data.get("first_name"),
        data.get("last_name"),
        phone=data.get("phone"),
        applicant_type=data.get("applicant_type"),
        current_city=data.get("current_city")
    )
    save_university_edu(user_id, data)  # silently ignores hs fields
    return {"status": "ok"}
