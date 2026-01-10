"""
Chats router - CRUD operations for chat conversations.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Optional, List
from datetime import datetime
from core.models import CamelCaseModel
from core.dependencies import get_current_user
from core.schemas import ChatResponse
from db.lib.core import supabase

router = APIRouter(
    prefix="/chats",
    tags=["chats"]
)

# Global reference to RAG pipeline (set by main.py)
rag_pipeline = None


def set_rag_pipeline(pipeline):
    """Set the RAG pipeline reference for generating AI responses."""
    global rag_pipeline
    rag_pipeline = pipeline


# ============= REQUEST/RESPONSE MODELS =============

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


# ============= CHAT ENDPOINTS =============

@router.get("", response_model=List[ChatResponse])
def list_chats(user_id: str = Depends(get_current_user)):
    """List all chats for the authenticated user in camelCase format."""
    try:
        response = supabase.table("chats")\
            .select("*")\
            .eq("user_id", user_id)\
            .order("last_message_at", desc=True)\
            .execute()
        
        # Convert to camelCase using Pydantic models
        result = []
        for chat in response.data:
            try:
                result.append(ChatResponse(
                    chat_id=chat["id"],
                    user_id=chat["user_id"],
                    title=chat["title"],
                    emoji=chat.get("emoji"),
                    is_pinned=chat.get("is_pinned", False),
                    created_at=chat["created_at"],
                    last_message_at=chat.get("last_message_at")
                ))
            except Exception as chat_err:
                print(f"Error mapping chat {chat.get('id')}: {chat_err}")
                print(f"Chat data: {chat}")
                raise
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"Failed to fetch chats: {str(e)}")


@router.post("", response_model=ChatResponse)
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
        
        # Return properly formatted camelCase response
        return ChatResponse(
            chat_id=created_chat["id"],
            user_id=created_chat["user_id"],
            title=created_chat["title"],
            emoji=created_chat.get("emoji"),
            is_pinned=created_chat.get("is_pinned", False),
            created_at=created_chat["created_at"],
            last_message_at=created_chat.get("last_message_at")
        )
    except Exception as e:
        raise HTTPException(500, f"Failed to create chat: {str(e)}")


@router.get("/{chat_id}")
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


@router.put("/{chat_id}")
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


@router.delete("/{chat_id}")
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


# ============= MESSAGE ENDPOINTS =============

@router.get("/{chat_id}/messages")
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


@router.post("/{chat_id}/messages")
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
        
        # Call AI service to generate response with chat history
        if rag_pipeline:
            try:
                # Fetch recent chat history for context
                history_response = supabase.table("messages")\
                    .select("role, content")\
                    .eq("chat_id", chat_id)\
                    .order("created_at", desc=False)\
                    .limit(10)\
                    .execute()
                
                # Format chat history for the RAG pipeline (exclude the current message just added)
                chat_history = []
                if history_response.data:
                    for msg in history_response.data[:-1]:  # Exclude the last message (current user message)
                        chat_history.append({
                            "role": msg["role"],
                            "content": msg["content"]
                        })
                
                # Use agent if available for user-personalized responses
                if hasattr(rag_pipeline, 'agent'):
                    ai_response_content = rag_pipeline.agent.run(
                        message.content, 
                        user_id=user_id, 
                        chat_history=chat_history
                    )
                else:
                    ai_response_content = rag_pipeline.answer_question(message.content, chat_history=chat_history)
            except Exception as e:
                print(f"Error generating AI response: {e}")
                import traceback
                traceback.print_exc()
                ai_response_content = "I apologize, but I encountered an error while processing your request."
        else:
            ai_response_content = "The AI service is currently unavailable. Please try again later."
        
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
