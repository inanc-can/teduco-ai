import os
from typing import Any, Dict, List, Optional, Union
from langchain_core.documents import Document  # type: ignore

from supabase import create_client
from core.config import get_settings

settings = get_settings()
supabase = create_client(settings.supabase_url, settings.supabase_service_key)

# ---------- INSERT CHUNKS ----------
def insert_one_chunk(doc: Document, embedding: List[float], table: str = "rag_uni_degree_documents"):
    """Insert a single document row into the configured table.

    Args:
        doc: mapping with keys `source`, `metadata`, and `content`/`page_content`.
        embedding: list of floats representing the embedding vector.
        table: Supabase table name to insert the row into (default: "rag_uni_degree_documents").

    Returns:
        None. Raises on failure.
    """
    content = doc.page_content or None
    if content:
        payload = {
            "metadata": doc.metadata,
            "content": content,
            "embedding": embedding,
        }
        print(f"[Inserter] inserting single row into {table}: source={payload['metadata']['source']}")
        res = supabase.table(table).insert(payload).execute()
        err = getattr(res, "error", None)
        if err:
            print("[Inserter] insert_one error:", err)
            raise RuntimeError(err)
        print("[Inserter] insert_one OK")

def bulk_insert(docs: List[Document], embeddings: List[List[float]], batch_size: int = 256, table: str = "rag_uni_degree_documents") -> int:
    """Insert many documents into the configured table in batches.

    Args:
        docs: list of document dicts.
        embeddings: list of embeddings aligned with `docs`.
        batch_size: number of rows to insert per request.
        table: Supabase table name to insert rows into (default: "rag_uni_degree_documents").

    Returns:
        Number of rows successfully inserted.
    """
    if len(docs) != len(embeddings):
        raise ValueError("docs and embeddings must have same length")

    total_inserted = 0
    rows: List[Dict[str, Any]] = []
    for doc, emb in zip(docs, embeddings):
        rows.append({
            "metadata": doc.metadata,
            "content": doc.page_content,
            "embedding": emb,
        })

    print(f"[Inserter] bulk_insert: inserting {len(rows)} rows in batches of {batch_size}")
    for i in range(0, len(rows), batch_size):
        batch = rows[i : i + batch_size]
        res = supabase.table(table).insert(batch).execute()
        err = getattr(res, "error", None)
        if err:
            print(f"[Inserter] batch insert failed at batch starting {i}:", err)
            raise RuntimeError(err)
        total_inserted += len(batch)
        print(f"[Inserter] inserted batch {i // batch_size + 1}: {len(batch)} rows")

    print(f"[Inserter] bulk_insert completed: {total_inserted} rows")
    return total_inserted

# ----------HYBRID RETRIEVAL ----------
def retrieve_chunks(query: str, query_embedding: List[float], top_k: int = 3):
    """
    Retrieve top-k related chunks using the hybrid retrieval RPC.

    Args:
        query: Textual query string (currently unused; kept for future filter extraction).
        query_embedding: Embedding vector for the query.
        top_k: Number of nearest neighbors to retrieve.

    Returns:
        List[Dict[str, Any]]: Each item contains 'content' and 'similarity_score'.
        Returns an empty list on error or when no results are found.
    """

    # Create function to extract filters afterwards
    # filters = extract_filters(query)
    filters = {
        "filter_university": None,
        "filter_degree": None,
        "filter_degree_level": None
    }
    response = supabase.rpc(
        "retrieve_rag_uni_degree_documents",
        {
            "query_embedding": query_embedding,
            "match_count": top_k,
            **filters
        }
    ).execute()
    # If the RPC returned an error or no data, return an empty list
    if not response:
        return []
    if getattr(response, "error", None):
        print("[Retriever] rpc error")
        return []
    data = getattr(response, "data", None)
    if not data:
        return []

    try:
        related_chunks = []
        for r in data:
            if not isinstance(r, dict):
                continue
            related_chunks.append({
                "content": r.get("content"),
                "similarity_score": r.get("similarity")
            })
        return related_chunks
    except Exception as e:
        print("[Retriever] response parsing error:", e)
        return []
