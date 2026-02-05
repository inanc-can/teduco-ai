"""
Documents router.
"""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile, File, Form
from typing import List
from core.dependencies import get_current_user, get_signed_url
from core.schemas import DocumentResponse
from db.lib.core import upload_document, get_user_documents, delete_document

router = APIRouter(
    prefix="/documents",
    tags=["documents"]
)


def _embed_user_document_background(user_id: str, file_content: bytes, filename: str, doc_type: str, mime_type: str):
    """Background task: parse a user document, chunk it, embed it, store in rag_user_documents."""
    try:
        from rag.chatbot.db_ops import upsert_user_document_chunks
        from langchain_core.documents import Document
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        from langchain_huggingface import HuggingFaceEmbeddings

        text = None

        # Parse PDF
        if mime_type == "application/pdf" or filename.lower().endswith(".pdf"):
            try:
                from rag.parser.pdf_parser import PDFParser
                parser = PDFParser()
                text = parser.extract_text(file_content, filename)
            except Exception as e:
                print(f"[DOC EMBED] Failed to parse PDF {filename}: {e}")
        elif mime_type in ["text/plain", "text/markdown"] or filename.lower().endswith((".txt", ".md")):
            text = file_content.decode("utf-8", errors="replace")

        # Strip null bytes that PostgreSQL cannot store
        if text:
            text = text.replace("\x00", "")

        if not text or len(text.strip()) < 10:
            print(f"[DOC EMBED] No text extracted from {filename}, skipping embedding")
            return

        # Chunk
        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        chunks = splitter.split_text(text)
        docs = [
            Document(page_content=chunk, metadata={"source": "user_document", "doc_type": doc_type, "filename": filename})
            for chunk in chunks
        ]

        # Embed (use /app/.hf_cache in Docker, fallback to ~/.cache/huggingface locally)
        import pathlib
        cache_dir = "/app/.hf_cache" if pathlib.Path("/app/.hf_cache").exists() else None
        embeddings_model = HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            **({"cache_folder": cache_dir} if cache_dir else {}),
            encode_kwargs={"normalize_embeddings": True},
            model_kwargs={"device": "cpu"},
        )
        chunk_texts = [d.page_content for d in docs]
        chunk_embeddings = embeddings_model.embed_documents(chunk_texts)

        # Store
        upsert_user_document_chunks(user_id, docs, chunk_embeddings, doc_type=doc_type)
        print(f"[DOC EMBED] Embedded {len(docs)} chunks for {filename} (user={user_id})")

    except Exception as e:
        import traceback
        print(f"[DOC EMBED] Error embedding document: {e}")
        traceback.print_exc()


@router.post("")
def add_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    doc_type: str = Form(...),
    user_id: str = Depends(get_current_user)
):
    """Upload a new document and embed it for RAG in the background."""
    try:
        # Read file content for both storage and embedding
        file_content = file.file.read()
        file.file.seek(0)

        upload_document(user_id, file.file, doc_type, file.content_type)

        # Embed in background
        background_tasks.add_task(
            _embed_user_document_background,
            user_id, file_content, file.filename or "document",
            doc_type, file.content_type or ""
        )

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
