"""
FastAPI routers package.
"""

from routers.auth import router as auth_router
from routers.profile import router as profile_router
from routers.documents import router as documents_router
from routers.chats import router as chats_router
from routers.rag import router as rag_router

__all__ = [
    "auth_router",
    "profile_router", 
    "documents_router",
    "chats_router",
    "rag_router",
]
