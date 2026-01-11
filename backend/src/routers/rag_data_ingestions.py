"""
RAG data ingestion router

Provides a simple POST endpoint to crawl documents, compute embeddings and
bulk-insert chunks into the Supabase RAG table. The work runs in the
background (FastAPI BackgroundTasks) so the request returns immediately.

This module does not change any existing functions; it only calls them.
"""
import tempfile
import shutil

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import Optional, List

# Import the running RAG pipeline from the existing routers.rag module
from rag.chatbot.loader import DocumentLoader, loaded_docs_to_chunks
from rag.chatbot.db_ops import (
    insert_one_chunk,
    bulk_insert,
    retrieve_chunks
)
from langchain_community.embeddings import HuggingFaceEmbeddings
embedding_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    encode_kwargs={
        "normalize_embeddings": True  # VERY IMPORTANT for cosine similarity
    },
    model_kwargs={'device': 'cpu'}
)
    


router = APIRouter(
    prefix="/rag-data",
    tags=["rag-data"]
)


class CrawlIngestRequest(BaseModel):
    program_slugs: Optional[List[str]] = None
    use_cache: bool = True
    batch_size: int = 256
    table: str = "rag_uni_degree_documents"


def _background_crawl_and_insert(
    data_dir,
    program_slugs: Optional[List[str]],
    use_cache: bool,
    batch_size: int = 256,
    table: str = "rag_uni_degree_documents",
    
):
    """Background worker: load docs, create embeddings, and bulk-insert them."""
    try:
        use_cache = True
        loader = DocumentLoader(data_dir=data_dir)
        documents = loader.load_from_crawler(
            program_slugs=program_slugs, use_cache=use_cache)
        chunks = loaded_docs_to_chunks(
            documents,
            chunk_size=500,
            chunk_overlap=50
        )
        chunk_contents = [chunk.page_content  for chunk in chunks]
        chunk_embeddings = embedding_model.embed_documents(chunk_contents)
        bulk_insert(
            docs=chunks, embeddings=chunk_embeddings, batch_size=batch_size, table=table)
        print(f"[RAG-INGEST] bulk_insert completed.")
    except Exception as e:
        print(f"[RAG-INGEST] bulk_insert failed: {e}")


@router.post("/crawl-and-bulk-insert")
async def crawl_and_bulk_insert(request: CrawlIngestRequest, background_tasks: BackgroundTasks):
    """Trigger a crawl + bulk insert run in the background.

    This is intended for manual/occasional runs (e.g. once every few months).
    The endpoint returns immediately while the heavy work runs in the background.
    """
    # Temporary data_dir
    tmp_file = tempfile.mkdtemp(prefix="rag_ingest_")

    # Default: background task as before
    background_tasks.add_task(
        _background_crawl_and_insert,
        tmp_file,
        request.program_slugs,
        request.use_cache,
        request.batch_size,
        request.table,
    )
    return {"status": "started", "detail": "Crawl and bulk insert started in background"}