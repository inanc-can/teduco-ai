from fastapi import FastAPI, HTTPException, Depends, Header, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import EmailStr
from typing import Optional, List
from datetime import datetime
import os
from uuid import uuid4
from .db.lib.core import upsert_user, save_university_edu, save_high_school_edu, save_onboarding_preferences, upload_document, get_user_profile, get_user_documents, delete_document, supabase
from .core.config import get_settings
from .core.models import CamelCaseModel
from .core.schemas import UserProfileResponse, UserProfileUpdate, DocumentResponse, ChatResponse

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

@app.get("/profile", response_model=UserProfileResponse)
def get_profile(user_id: str = Depends(get_current_user)):
    """Get user profile data in camelCase format."""
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

@app.put("/profile")
def update_profile(payload: UserProfileUpdate, user_id: str = Depends(get_current_user)):
    """Update user profile. Pydantic automatically converts camelCase to snake_case."""
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
    
    # Save education info based on applicant type
    applicant_type = data.get("applicant_type")
    if applicant_type == "university":
        save_university_edu(user_id, data)
    elif applicant_type == "high-school":
        save_high_school_edu(user_id, data)
    
    # Save onboarding preferences if any are present
    pref_fields = ["desired_countries", "desired_field", "target_program", "preferred_intake", "preferred_support", "additional_notes"]
    if any(k in data for k in pref_fields):
        save_onboarding_preferences(user_id, data)
    
    return {"message": "ok", "user_id": user_id}

# Alias for settings (same as profile)
@app.get("/settings", response_model=UserProfileResponse)
def get_settings(user_id: str = Depends(get_current_user)):
    """Get user settings (alias for profile)."""
    return get_profile(user_id)

@app.patch("/settings")
def update_settings(payload: UserProfileUpdate, user_id: str = Depends(get_current_user)):
    """Update user settings (alias for profile)."""
    return update_profile(payload, user_id)

@app.put("/settings")
def update_settings_put(payload: UserProfileUpdate, user_id: str = Depends(get_current_user)):
    """Update user settings via PUT (alias for profile)."""
    return update_profile(payload, user_id)

@app.post("/onboarding")
def onboarding(payload: UserProfileUpdate, user_id: str = Depends(get_current_user)):
    """Onboarding endpoint (calls update_profile)."""
    return update_profile(payload, user_id)


@app.post("/onboarding/profile")
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

@app.post("/documents")
def add_document(
    file: UploadFile = File(...),
    doc_type: str = Form(...),
    user_id: str = Depends(get_current_user)
):
    try:
        upload_document(user_id, file.file, doc_type, file.content_type)
        return {"status": "uploaded", "filename": file.filename}
    except Exception as e:
        import traceback
        print(f"Error uploading document: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload document: {str(e)}"
        )

@app.get("/documents", response_model=List[DocumentResponse])
def list_documents(user_id: str = Depends(get_current_user)):
    """List all documents for the user in camelCase format."""
    result = get_user_documents(user_id)
    return [DocumentResponse(**doc) for doc in result.data]

@app.get("/documents/{document_id}/signed-url")
def get_document_signed_url(
    document_id: str, 
    user_id: str = Depends(get_current_user),
    expires_sec: int = 3600  # 1 hour default
):
    """Generate a signed URL for viewing a document."""
    # Verify the document belongs to the user
    result = get_user_documents(user_id)
    document = next((doc for doc in result.data if doc.get("document_id") == document_id), None)
    
    if not document:
        raise HTTPException(404, "Document not found")
    
    storage_path = document.get("storage_path")
    if not storage_path:
        raise HTTPException(400, "Document has no storage path")
    
    signed_url = get_signed_url(storage_path, expires_sec)
    return {"signedUrl": signed_url}

@app.delete("/documents/{document_id}")
def remove_document(document_id: str, user_id: str = Depends(get_current_user)):
    delete_document(document_id, user_id)
    return {"status": "deleted"}

class LoginIn(CamelCaseModel):
    email: EmailStr
    password: str

# Chat models
class ChatCreate(CamelCaseModel):
    title: Optional[str] = "New Chat"
    emoji: Optional[str] = "💬"
    initial_message: Optional[str] = None

class ChatUpdate(CamelCaseModel):
    title: Optional[str] = None
    emoji: Optional[str] = None
    is_pinned: Optional[bool] = None

class MessageCreate(CamelCaseModel):
    content: str
    metadata: Optional[dict] = None

@app.post("/auth/login")
def login(credentials: LoginIn):
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


# ============= CHAT ENDPOINTS =============

@app.get("/chats", response_model=List[ChatResponse])
def list_chats(user_id: str = Depends(get_current_user)):
    """List all chats for the authenticated user in camelCase format."""
    try:
        response = supabase.table("chats")\
            .select("*")\
            .eq("user_id", user_id)\
            .order("last_message_at", desc=True)\
            .execute()
        
        # Convert to camelCase using Pydantic models
        return [ChatResponse(
            chat_id=chat["id"],
            user_id=chat["user_id"],
            title=chat["title"],
            emoji=chat.get("emoji"),
            is_pinned=chat.get("is_pinned", False),
            created_at=chat["created_at"],
            last_message_at=chat.get("last_message_at")
        ) for chat in response.data]
    except Exception as e:
        raise HTTPException(500, f"Failed to fetch chats: {str(e)}")


@app.post("/chats")
def create_chat(chat: ChatCreate, user_id: str = Depends(get_current_user)):
    """Create a new chat."""
    try:
        new_chat = {
            "user_id": user_id,
            "title": chat.title,
            "emoji": chat.emoji,
        }
        
        response = supabase.table("chats").insert(new_chat).execute()
        
        if not response.data:
            raise HTTPException(500, "Failed to create chat")
        
        created_chat = response.data[0]
        
        # If there's an initial message, create it
        if chat.initial_message:
            message_data = {
                "chat_id": created_chat["id"],
                "user_id": user_id,
                "content": chat.initial_message,
                "role": "user",
            }
            supabase.table("messages").insert(message_data).execute()
        
        return created_chat
    except Exception as e:
        raise HTTPException(500, f"Failed to create chat: {str(e)}")


@app.get("/chats/{chat_id}")
def get_chat(chat_id: str, user_id: str = Depends(get_current_user)):
    """Get a specific chat."""
    try:
        response = supabase.table("chats")\
            .select("*")\
            .eq("id", chat_id)\
            .eq("user_id", user_id)\
            .single()\
            .execute()
        
        if not response.data:
            raise HTTPException(404, "Chat not found")
        
        return response.data
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(404, "Chat not found")
        raise HTTPException(500, f"Failed to fetch chat: {str(e)}")


@app.put("/chats/{chat_id}")
def update_chat(chat_id: str, chat_update: ChatUpdate, user_id: str = Depends(get_current_user)):
    """Update a chat (title, emoji, pinned status)."""
    try:
        # Build update dict with only provided fields
        update_data = {}
        if chat_update.title is not None:
            update_data["title"] = chat_update.title
        if chat_update.emoji is not None:
            update_data["emoji"] = chat_update.emoji
        if chat_update.is_pinned is not None:
            update_data["is_pinned"] = chat_update.is_pinned
        
        if not update_data:
            raise HTTPException(400, "No fields to update")
        
        response = supabase.table("chats")\
            .update(update_data)\
            .eq("id", chat_id)\
            .eq("user_id", user_id)\
            .execute()
        
        if not response.data:
            raise HTTPException(404, "Chat not found")
        
        return response.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to update chat: {str(e)}")


@app.delete("/chats/{chat_id}")
def delete_chat(chat_id: str, user_id: str = Depends(get_current_user)):
    """Delete a chat and all its messages."""
    try:
        response = supabase.table("chats")\
            .delete()\
            .eq("id", chat_id)\
            .eq("user_id", user_id)\
            .execute()
        
        if not response.data:
            raise HTTPException(404, "Chat not found")
        
        return {"message": "Chat deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to delete chat: {str(e)}")


@app.get("/chats/{chat_id}/messages")
def get_messages(
    chat_id: str, 
    limit: int = 100,
    offset: int = 0,
    user_id: str = Depends(get_current_user)
):
    """Get messages for a specific chat."""
    try:
        # First verify the chat belongs to the user
        chat_response = supabase.table("chats")\
            .select("id")\
            .eq("id", chat_id)\
            .eq("user_id", user_id)\
            .single()\
            .execute()
        
        if not chat_response.data:
            raise HTTPException(404, "Chat not found")
        
        # Fetch messages
        response = supabase.table("messages")\
            .select("*")\
            .eq("chat_id", chat_id)\
            .order("created_at", desc=False)\
            .limit(limit)\
            .range(offset, offset + limit - 1)\
            .execute()
        
        return response.data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to fetch messages: {str(e)}")


@app.post("/chats/{chat_id}/messages")
def send_message(
    chat_id: str,
    message: MessageCreate,
    user_id: str = Depends(get_current_user)
):
    """Send a message in a chat and get AI response."""
    try:
        # Verify chat belongs to user
        chat_response = supabase.table("chats")\
            .select("*")\
            .eq("id", chat_id)\
            .eq("user_id", user_id)\
            .single()\
            .execute()
        
        if not chat_response.data:
            raise HTTPException(404, "Chat not found")
        
        # Save user message
        user_message_data = {
            "chat_id": chat_id,
            "user_id": user_id,
            "content": message.content,
            "role": "user",
            "metadata": message.metadata or {}
        }
        
        user_msg_response = supabase.table("messages")\
            .insert(user_message_data)\
            .execute()
        
        if not user_msg_response.data:
            raise HTTPException(500, "Failed to save message")
        
        # TODO: Call AI service here to generate response
        # For now, return a placeholder response
        ai_response_content = "This is a placeholder AI response. Integration with AI service coming soon!"
        
        # Save AI response
        ai_message_data = {
            "chat_id": chat_id,
            "user_id": user_id,
            "content": ai_response_content,
            "role": "assistant",
            "metadata": {}
        }
        
        ai_msg_response = supabase.table("messages")\
            .insert(ai_message_data)\
            .execute()
        
        # Update chat's last_message_at
        supabase.table("chats")\
            .update({"last_message_at": datetime.utcnow().isoformat()})\
            .eq("id", chat_id)\
            .execute()
        
        # Auto-generate title from first message if still "New Chat"
        if chat_response.data["title"] == "New Chat" and len(message.content) > 0:
            # Simple title generation: first 30 chars
            new_title = message.content[:30] + ("..." if len(message.content) > 30 else "")
            supabase.table("chats")\
                .update({"title": new_title})\
                .eq("id", chat_id)\
                .execute()
        
        return {
            "user_message": user_msg_response.data[0],
            "assistant_message": ai_msg_response.data[0] if ai_msg_response.data else None
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to send message: {str(e)}")