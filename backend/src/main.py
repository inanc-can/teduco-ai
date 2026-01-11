"""
Teduco API - Main Application Entry Point

This module initializes the FastAPI application and mounts all routers.
"""

import os
import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add src directory to path for proper imports
sys.path.insert(0, str(Path(__file__).parent))

# Import routers
from routers.auth import router as auth_router
from routers.profile import router as profile_router
from routers.documents import router as documents_router
from routers.chats import router as chats_router, set_rag_pipeline
from routers.rag import router as rag_router, get_rag_pipeline, is_rag_ready
from routers.rag_data_ingestions import router as rag_data_router

# ============================================================================
# APPLICATION SETUP
# ============================================================================

app = FastAPI(
    title="Teduco API",
    version="0.1.0",
    description="University admissions assistant API with RAG-powered chatbot"
)

# gurantee that main_new is only run when executing docker compose up
if __name__ != "__main__":
    # Print startup message
    print("\n" + "="*70)
    print("TEDUCO API - Starting FastAPI Application with main_new.py")
    print("="*70)

# CORS configuration for frontend
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# MOUNT ROUTERS
# ============================================================================

app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(documents_router)
app.include_router(chats_router)
app.include_router(rag_router)
app.include_router(rag_data_router)

# Share RAG pipeline with chats router
set_rag_pipeline(get_rag_pipeline())

# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/health", tags=["health"])
def health_check():
    """Health check endpoint for debugging."""
    return {
        "status": "healthy",
        "rag_ready": is_rag_ready()
    }
