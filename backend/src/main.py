from fastapi import FastAPI, HTTPException, Depends, Header, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import List
import os
from uuid import uuid4
from db.lib.core import upsert_user, save_university_edu, save_high_school_edu, save_onboarding_preferences, upload_document, supabase
from core.config import get_settings

import sys
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse


# Add backend directory to path for RAG imports
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "rag"))
# Import RAG chatbot components
from rag.models import ChatRequest, ChatResponse
from rag.storage import ChatHistoryStorage
from rag.chatbot.pipeline import initialize_rag_pipeline



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

@app.post("/onboarding")
def onboarding(payload: dict, user_id: str = Depends(get_current_user)):
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
    

# ============================================================================
# RAG CHATBOT INITIALIZATION
# ============================================================================
print("\n" + "="*70)
print("TEDUCO API - Initializing RAG Chatbot")
print("="*70)

# Initialize RAG pipeline
RAG_DATA_DIR = Path(__file__).parent / "rag" / "data"
RAG_DATA_DIR.mkdir(parents=True, exist_ok=True)

try:
    print("\n[STARTUP] Initializing RAG pipeline...")
    rag_pipeline = initialize_rag_pipeline(
        data_dir=str(RAG_DATA_DIR),
        use_cache=True
    )
    print("[STARTUP] ✓ RAG pipeline initialized")
except Exception as e:
    print(f"\n[ERROR] Failed to initialize RAG pipeline: {e}")
    print("\nMake sure:")
    print("1. GROQ_API_KEY is set in .env file")
    print("2. Run the crawler first: python -m rag.parser.crawler")
    rag_pipeline = None  # Allow API to start even if RAG fails

# Initialize chat history storage
storage = ChatHistoryStorage(storage_dir="chats")

# ============================================================================
# STATIC FILES - Serve the frontend
# ============================================================================
FRONTEND_PATH = Path(__file__).parent  # Points to /app/src in container
CHATBOT_HTML = FRONTEND_PATH / "chatbot.html"
if CHATBOT_HTML.exists():
    print("[STARTUP] ✓ Chatbot frontend found at chatbot.html")

# ============================================================================
# RAG CHATBOT ENDPOINTS
# ============================================================================

@app.get("/chat")
async def chat_frontend():
    """
    Chat endpoint - serves the standalone chatbot frontend (no credentials required).
    """
    if CHATBOT_HTML.exists():
        return FileResponse(str(CHATBOT_HTML))
    else:
        raise HTTPException(status_code=404, detail="Chatbot frontend not found")


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    RAG Chatbot endpoint - answers questions using the RAG pipeline.
    
    REQUEST:
    {
        "question": "What are the admission requirements?",
        "chat_id": null  // null = new chat, or "abc-123" = existing chat
    }
    
    RESPONSE:
    {
        "answer": "The admission requirements are...",
        "chat_id": "550e8400-e29b-41d4-a716-446655440000"
    }
    """
    if rag_pipeline is None:
        raise HTTPException(
            status_code=503,
            detail="RAG pipeline not initialized. Please check server logs."
        )
    
    print(f"\n[API] /chat endpoint called")
    print(f"     Question: {request.question[:60]}...")
    print(f"     Chat ID: {request.chat_id or 'NEW CHAT'}")
    
    try:
        # Get or create chat
        if request.chat_id:
            chat = storage.get_chat(request.chat_id)
            if chat is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Chat {request.chat_id} not found"
                )
        else:
            chat = storage.create_chat()
            print(f"[CHAT] Created new chat: {chat.chat_id}")
        
        # Save user's question
        storage.add_message_to_chat(chat.chat_id, request.question, "user")
        
        # Get answer from RAG pipeline
        print(f"[RAG] Querying RAG pipeline...")
        answer = rag_pipeline.answer_question(request.question)
        print(f"[RAG] ✓ Response generated")
        
        # Save assistant's answer
        storage.add_message_to_chat(chat.chat_id, answer, "assistant")
        
        # Return response
        return ChatResponse(
            answer=answer,
            chat_id=chat.chat_id
        )
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Exception in /chat: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing chat: {str(e)}"
        )