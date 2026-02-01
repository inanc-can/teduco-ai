"""
Application Letters Router - CRUD operations for managing application letters
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from datetime import datetime
import hashlib

from core.dependencies import get_current_user
from db.lib.core import supabase

router = APIRouter(prefix="/letters", tags=["letters"])


# Pydantic Models
class ApplicationLetterCreate(BaseModel):
    """Request model for creating a new application letter"""
    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(default="")
    program_id: Optional[str] = None
    program_name: Optional[str] = None
    status: str = Field(default="draft")
    metadata: dict = Field(default_factory=dict)


class ApplicationLetterUpdate(BaseModel):
    """Request model for updating an application letter"""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    content: Optional[str] = None
    program_id: Optional[str] = None
    program_name: Optional[str] = None
    status: Optional[str] = None
    metadata: Optional[dict] = None


class ApplicationLetterAutoSave(BaseModel):
    """Request model for auto-saving letter content"""
    content: str
    rejected_suggestion_ids: Optional[List[str]] = None
    applied_suggestion_metadata: Optional[List[dict]] = None


class ApplicationLetterResponse(BaseModel):
    """Response model for application letter"""
    id: UUID
    user_id: UUID
    title: str
    content: str
    program_id: Optional[str]
    program_name: Optional[str]
    status: str
    word_count: int
    created_at: datetime
    updated_at: datetime
    metadata: dict
    rejected_suggestion_ids: List[str] = []
    applied_suggestion_metadata: List[dict] = []

    class Config:
        from_attributes = True


@router.get("", response_model=List[ApplicationLetterResponse])
async def list_letters(
    current_user: str = Depends(get_current_user),
    limit: int = 50,
    offset: int = 0
):
    """
    List all application letters for the current user
    Ordered by most recently updated first
    """
    user_id = current_user
    
    try:
        response = (
            supabase.table("application_letters")
            .select("*")
            .eq("user_id", user_id)
            .order("updated_at", desc=True)
            .limit(limit)
            .offset(offset)
            .execute()
        )
        
        return response.data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch letters: {str(e)}"
        )


@router.post("", response_model=ApplicationLetterResponse, status_code=status.HTTP_201_CREATED)
async def create_letter(
    letter: ApplicationLetterCreate,
    current_user: str = Depends(get_current_user)
):
    """
    Create a new application letter
    """
    user_id = current_user
    
    try:
        # Prepare letter data
        letter_data = {
            "user_id": user_id,
            "title": letter.title,
            "content": letter.content,
            "program_id": letter.program_id,
            "program_name": letter.program_name,
            "status": letter.status,
            "metadata": letter.metadata
        }
        
        response = (
            supabase.table("application_letters")
            .insert(letter_data)
            .execute()
        )
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create letter"
            )
        
        return response.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create letter: {str(e)}"
        )


@router.get("/{letter_id}", response_model=ApplicationLetterResponse)
async def get_letter(
    letter_id: UUID,
    current_user: str = Depends(get_current_user)
):
    """
    Get a specific application letter by ID
    """
    user_id = current_user
    
    try:
        response = (
            supabase.table("application_letters")
            .select("*")
            .eq("id", str(letter_id))
            .eq("user_id", user_id)
            .execute()
        )
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Letter not found"
            )
        
        return response.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch letter: {str(e)}"
        )


@router.put("/{letter_id}", response_model=ApplicationLetterResponse)
async def update_letter(
    letter_id: UUID,
    letter: ApplicationLetterUpdate,
    current_user: str = Depends(get_current_user)
):
    """
    Update an application letter
    """
    user_id = current_user
    
    try:
        # Build update data from non-None fields
        update_data = {}
        if letter.title is not None:
            update_data["title"] = letter.title
        if letter.content is not None:
            update_data["content"] = letter.content
        if letter.program_id is not None:
            update_data["program_id"] = letter.program_id
        if letter.program_name is not None:
            update_data["program_name"] = letter.program_name
        if letter.status is not None:
            update_data["status"] = letter.status
        if letter.metadata is not None:
            update_data["metadata"] = letter.metadata
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )
        
        response = (
            supabase.table("application_letters")
            .update(update_data)
            .eq("id", str(letter_id))
            .eq("user_id", user_id)
            .execute()
        )
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Letter not found"
            )
        
        return response.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update letter: {str(e)}"
        )


@router.patch("/{letter_id}/auto-save", response_model=ApplicationLetterResponse)
async def auto_save_letter(
    letter_id: UUID,
    auto_save: ApplicationLetterAutoSave,
    current_user: str = Depends(get_current_user)
):
    """
    Auto-save letter content (lightweight endpoint for frequent saves)
    Only updates content field and triggers word_count recalculation
    Also clears cached analysis since content changed
    """
    user_id = current_user
    
    try:
        # Build update data
        update_data = {
            "content": auto_save.content,
            "content_hash": None,  # Clear hash to invalidate cache
            "last_analysis": None  # Clear cached analysis
            # Note: Keep analysis_version as is - it's only incremented when new analysis completes
        }
        
        # Include suggestion states if provided
        if auto_save.rejected_suggestion_ids is not None:
            update_data["rejected_suggestion_ids"] = auto_save.rejected_suggestion_ids
        if auto_save.applied_suggestion_metadata is not None:
            update_data["applied_suggestion_metadata"] = auto_save.applied_suggestion_metadata
        
        # Clear cached analysis when content changes (invalidate cache)
        response = (
            supabase.table("application_letters")
            .update(update_data)
            .eq("id", str(letter_id))
            .eq("user_id", user_id)
            .execute()
        )
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Letter not found"
            )
        
        return response.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to auto-save letter: {str(e)}"
        )


@router.delete("/{letter_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_letter(
    letter_id: UUID,
    current_user: str = Depends(get_current_user)
):
    """
    Delete an application letter
    """
    user_id = current_user
    
    try:
        response = (
            supabase.table("application_letters")
            .delete()
            .eq("id", str(letter_id))
            .eq("user_id", user_id)
            .execute()
        )
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Letter not found"
            )
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete letter: {str(e)}"
        )
