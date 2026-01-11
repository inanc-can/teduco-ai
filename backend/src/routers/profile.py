"""
Profile, settings, and onboarding router.
"""

from fastapi import APIRouter, Depends
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


def _build_profile_response(user_id: str) -> UserProfileResponse:
    """Build profile response from database data."""
    raw_profile = get_user_profile(user_id)
    
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
def onboarding(payload: UserProfileUpdate, user_id: str = Depends(get_current_user)):
    """Onboarding endpoint (calls update_profile)."""
    return _update_profile_data(user_id, payload)


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
