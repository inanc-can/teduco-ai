"""
RAG Chatbot router - standalone RAG endpoint with local storage.
"""

from fastapi import APIRouter, HTTPException
from pathlib import Path
from rag.models import ChatRequest, ChatResponse
from rag.storage import ChatHistoryStorage
from rag.chatbot.pipeline import initialize_rag_pipeline

router = APIRouter(
    tags=["rag"]
)

# ============================================================================
# RAG CHATBOT INITIALIZATION
# ============================================================================
print("\n" + "="*70)
print("TEDUCO API - Initializing RAG Chatbot")
print("="*70)

# Initialize RAG pipeline
RAG_DATA_DIR = Path(__file__).parent.parent / "rag" / "data"
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

# Initialize chat history storage for standalone /chat endpoint
CHATS_DIR = Path(__file__).parent.parent / "chats"
storage = ChatHistoryStorage(storage_dir=str(CHATS_DIR))


def get_rag_pipeline():
    """Get the RAG pipeline instance (for use by other routers)."""
    return rag_pipeline


def is_rag_ready() -> bool:
    """Check if RAG pipeline is initialized."""
    return rag_pipeline is not None


# ============================================================================
# RAG CHATBOT ENDPOINT
# ============================================================================

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    RAG Chatbot endpoint - answers questions using the RAG pipeline.
    
    This is a standalone endpoint with its own local chat storage.
    For database-backed chats, use /chats/{chat_id}/messages instead.
    
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
        
        # Get chat history (excluding the just-added user message) for context
        chat_history_raw = storage.get_chat_history(chat.chat_id)
        chat_history = []
        if chat_history_raw and len(chat_history_raw) > 1:  # More than just the current message
            for msg in chat_history_raw[:-1]:  # Exclude the last message (current user message)
                chat_history.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        # Get answer from RAG pipeline with chat history
        print(f"[RAG] Querying RAG pipeline with {len(chat_history)} history messages...")
        answer = rag_pipeline.answer_question(request.question, chat_history=chat_history)
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
