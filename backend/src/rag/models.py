"""
Pydantic models for RAG chatbot API endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional


class ChatRequest(BaseModel):
    """
    Request model for the /chat endpoint.
    """
    question: str = Field(..., description="User's question to the chatbot")
    chat_id: Optional[str] = Field(None, description="Optional chat ID for continuing a conversation")


class ChatResponse(BaseModel):
    """
    Response model for the /chat endpoint.
    """
    answer: str = Field(..., description="AI-generated answer to the user's question")
    chat_id: str = Field(..., description="Chat ID for this conversation")
