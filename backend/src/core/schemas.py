"""
API response models with camelCase conversion for frontend.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from .models import CamelCaseModel

# ========== User Profile Models ==========

class UserProfileUpdate(CamelCaseModel):
    """
    User profile update request.
    All fields are optional to support partial updates.
    Automatically converts camelCase from frontend to snake_case for backend.
    """
    # Basic user info
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    applicant_type: Optional[str] = None
    current_city: Optional[str] = None
    
    # High school fields
    high_school_name: Optional[str] = None
    high_school_gpa: Optional[float] = None
    high_school_gpa_scale: Optional[float] = None
    high_school_grad_year: Optional[int] = None
    yks_placed: Optional[str] = None
    
    # University fields  
    university_name: Optional[str] = None
    university_program: Optional[str] = None
    university_gpa: Optional[float] = None
    credits_completed: Optional[int] = None
    expected_graduation: Optional[str] = None
    study_mode: Optional[str] = None
    research_focus: Optional[str] = None
    portfolio_link: Optional[str] = None
    
    # Preferences
    desired_countries: Optional[List[str]] = None
    desired_field: Optional[List[str]] = None
    target_program: Optional[List[str]] = None
    preferred_intake: Optional[str] = None
    preferred_support: Optional[str] = None
    additional_notes: Optional[str] = None

class UserBasic(CamelCaseModel):
    """Basic user information."""
    user_id: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    applicant_type: Optional[str] = None
    current_city: Optional[str] = None
    onboarding_completed: bool = False
    created_at: Optional[str] = None

class HighSchoolEducation(CamelCaseModel):
    """High school education details."""
    high_school_name: Optional[str] = None
    gpa: Optional[float] = None
    gpa_scale: Optional[float] = None
    grad_year: Optional[int] = None
    yks_placed: Optional[str] = None
    extracurriculars: Optional[str] = None
    scholarship_interest: Optional[bool] = None

class UniversityEducation(CamelCaseModel):
    """University education details."""
    university_name: Optional[str] = None
    university_program: Optional[str] = None
    gpa: Optional[float] = None
    credits_completed: Optional[int] = None
    expected_graduation: Optional[str] = None  # ISO date string
    study_mode: Optional[str] = None
    research_focus: Optional[str] = None
    portfolio_link: Optional[str] = None

class OnboardingPreferences(CamelCaseModel):
    """User preferences from onboarding."""
    desired_countries: List[str] = []
    desired_fields: List[str] = []
    target_programs: List[str] = []
    preferred_intake: Optional[str] = None
    preferred_support: Optional[str] = None
    additional_notes: Optional[str] = None

class UserProfileResponse(CamelCaseModel):
    """
    Complete user profile response.
    Flattens the nested structure from database into a single object.
    """
    # Basic user info
    first_name: str
    last_name: str
    phone: Optional[str] = None
    applicant_type: Optional[str] = None
    current_city: Optional[str] = None
    onboarding_completed: bool = False
    
    # High school fields
    high_school_name: Optional[str] = None
    high_school_gpa: Optional[float] = None
    high_school_gpa_scale: Optional[float] = None
    high_school_grad_year: Optional[int] = None
    yks_placed: Optional[str] = None
    
    # University fields  
    university_name: Optional[str] = None
    university_program: Optional[str] = None
    university_gpa: Optional[float] = None
    credits_completed: Optional[int] = None
    expected_graduation: Optional[str] = None
    study_mode: Optional[str] = None
    research_focus: Optional[str] = None
    portfolio_link: Optional[str] = None
    
    # Preferences
    desired_countries: List[str] = []
    desired_field: List[str] = []  # Note: frontend uses singular
    target_program: List[str] = []  # Note: frontend uses singular
    preferred_intake: Optional[str] = None
    preferred_support: Optional[str] = None
    additional_notes: Optional[str] = None

# ========== Document Models ==========

class DocumentResponse(CamelCaseModel):
    """Document metadata response."""
    document_id: str
    user_id: str
    doc_type: str
    storage_path: str
    mime_type: Optional[str] = None
    created_at: Optional[str] = None

# ========== Chat Models ==========

class ChatResponse(CamelCaseModel):
    """Chat response."""
    chat_id: str
    user_id: str
    title: str
    emoji: Optional[str] = None
    is_pinned: bool = False
    created_at: str
    last_message_at: Optional[str] = None

class MessageResponse(CamelCaseModel):
    """Message response."""
    message_id: str
    chat_id: str
    role: str  # 'user' or 'assistant'
    content: str
    metadata: Optional[dict] = None
    created_at: str
