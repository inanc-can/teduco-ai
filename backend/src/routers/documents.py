"""
Documents router.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from typing import List
from core.dependencies import get_current_user, get_signed_url
from core.schemas import DocumentResponse
from db.lib.core import upload_document, get_user_documents, delete_document

router = APIRouter(
    prefix="/documents",
    tags=["documents"]
)


@router.post("")
def add_document(
    file: UploadFile = File(...),
    doc_type: str = Form(...),
    user_id: str = Depends(get_current_user)
):
    """Upload a new document."""
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


@router.get("", response_model=List[DocumentResponse])
def list_documents(user_id: str = Depends(get_current_user)):
    """List all documents for the user in camelCase format."""
    result = get_user_documents(user_id)
    return [DocumentResponse(**doc) for doc in result.data]


@router.get("/{document_id}/signed-url")
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


@router.delete("/{document_id}")
def remove_document(document_id: str, user_id: str = Depends(get_current_user)):
    """Delete a document."""
    delete_document(document_id, user_id)
    return {"status": "deleted"}
