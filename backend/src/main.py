from fastapi import FastAPI, HTTPException, Depends, Header, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime
import os
from uuid import uuid4
from .db.lib.core import upsert_user, save_university_edu, save_high_school_edu, save_onboarding_preferences, upload_document, get_user_profile, get_user_documents, delete_document, supabase
from .core.config import get_settings

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

@app.get("/profile")
def get_profile(user_id: str = Depends(get_current_user)):
    """Get user profile data."""
    profile = get_user_profile(user_id)
    return profile

@app.put("/profile")
def update_profile(payload: dict, user_id: str = Depends(get_current_user)):
    """Update user profile (same as onboarding)."""
    # Update user profile
    upsert_user(
        user_id,
        payload["firstName"],
        payload["lastName"],
        phone=payload.get("phone"),
        applicant_type=payload.get("applicantType"),
        current_city=payload.get("currentCity")
    )
    
    # Save education info based on applicant type
    applicant_type = payload.get("applicantType")
    if applicant_type == "university":
        save_university_edu(user_id, payload)
    elif applicant_type == "high-school":
        save_high_school_edu(user_id, payload)
    
    # Save onboarding preferences
    save_onboarding_preferences(user_id, payload)
    
    return {"message": "ok", "user_id": user_id}

@app.post("/onboarding")
def onboarding(payload: dict, user_id: str = Depends(get_current_user)):
    """Onboarding endpoint (calls update_profile)."""
    return update_profile(payload, user_id)


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

@app.get("/documents")
def list_documents(user_id: str = Depends(get_current_user)):
    result = get_user_documents(user_id)
    return result.data

@app.delete("/documents/{document_id}")
def remove_document(document_id: str, user_id: str = Depends(get_current_user)):
    delete_document(document_id, user_id)
    return {"status": "deleted"}

class LoginIn(BaseModel):
    email: EmailStr
    password: str

# Chat models
class ChatCreate(BaseModel):
    title: Optional[str] = "New Chat"
    emoji: Optional[str] = "💬"
    initial_message: Optional[str] = None

class ChatUpdate(BaseModel):
    title: Optional[str] = None
    emoji: Optional[str] = None
    is_pinned: Optional[bool] = None

class MessageCreate(BaseModel):
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

@app.get("/chats")
def list_chats(user_id: str = Depends(get_current_user)):
    """List all chats for the authenticated user."""
    try:
        response = supabase.table("chats")\
            .select("*")\
            .eq("user_id", user_id)\
            .order("last_message_at", desc=True)\
            .execute()
        
        return response.data
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