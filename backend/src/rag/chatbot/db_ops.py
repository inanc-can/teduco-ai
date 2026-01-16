import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from langchain_core.documents import Document  # type: ignore

from supabase import create_client
from core.config import get_settings

settings = get_settings()
supabase = create_client(settings.supabase_url, settings.supabase_service_key)

# ---------- DEGREE PROGRAM LISTING ----------
def list_all_degree_programs(table: str = "rag_uni_degree_documents") -> List[Dict[str, str]]:
    """Get a list of all unique degree programs in the database.
    
    Returns:
        List of dicts with 'degree', 'degree_level', 'source' for each unique program.
    """
    try:
        # Query for distinct degree programs
        response = supabase.rpc(
            'list_unique_degree_programs'
        ).execute()
        
        if response.data:
            return response.data
        
        # Fallback: query the table directly and dedupe in Python
        response = supabase.table(table).select("metadata").limit(1000).execute()
        
        if not response.data:
            return []
        
        # Extract unique programs
        programs = {}
        for row in response.data:
            meta = row.get("metadata", {})
            degree = meta.get("degree")
            degree_level = meta.get("degree_level")
            source = meta.get("source")
            
            if degree and source:
                key = f"{degree}_{degree_level}_{source}"
                if key not in programs:
                    programs[key] = {
                        "degree": degree,
                        "degree_level": degree_level or "unknown",
                        "source": source
                    }
        
        return list(programs.values())
        
    except Exception as e:
        print(f"[DB] Error listing degree programs: {e}")
        return []

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
def retrieve_chunks(
    query: str, 
    query_embedding: List[float], 
    top_k: int = 10,
    semantic_weight: float = 0.7,
    keyword_weight: float = 0.3,
    filter_university: Optional[str] = None,
    filter_degree: Optional[str] = None,
    filter_degree_level: Optional[str] = None
):
    """
    Retrieve top-k related chunks using hybrid search (semantic + keyword).
    Falls back to semantic-only search if hybrid search function is not available.

    Args:
        query: Textual query string for keyword search.
        query_embedding: Embedding vector for semantic search.
        top_k: Number of documents to retrieve.
        semantic_weight: Weight for semantic similarity (0-1, default: 0.7).
        keyword_weight: Weight for keyword matching (0-1, default: 0.3).
        filter_university: Optional university filter.
        filter_degree: Optional degree filter.
        filter_degree_level: Optional degree level filter.

    Returns:
        List[Dict[str, Any]]: Each item contains 'content', 'metadata', 'similarity_score', 
                              'keyword_rank', and 'hybrid_score'.
        Returns an empty list on error or when no results are found.
    """
    
    # Try hybrid search first
    try:
        # Prepare RPC parameters for hybrid search
        params = {
            "query_embedding": query_embedding,
            "query_text": query,
            "match_count": top_k,
            "semantic_weight": semantic_weight,
            "keyword_weight": keyword_weight,
        }
        
        # Add optional filters if provided
        if filter_university is not None:
            params["filter_university"] = filter_university
        if filter_degree is not None:
            params["filter_degree"] = filter_degree
        if filter_degree_level is not None:
            params["filter_degree_level"] = filter_degree_level
        
        # Call the hybrid search RPC function
        response = supabase.rpc(
            "hybrid_search_uni_degree_documents",
            params
        ).execute()
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [HYBRID SEARCH] Using hybrid search function")
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [HYBRID SEARCH] Raw Supabase response: {response}")
        
        # Attempt to show data payload size/preview for easier debugging
        raw_data = getattr(response, "data", None)
        if raw_data is not None:
            try:
                data_preview = raw_data[:2] if isinstance(raw_data, list) else raw_data
                print(f"[{datetime.now().strftime('%H:%M:%S')}] [HYBRID SEARCH] data length: {len(raw_data) if hasattr(raw_data, '__len__') else 'N/A'}")
                print(f"[{datetime.now().strftime('%H:%M:%S')}] [HYBRID SEARCH] preview (first 2): {data_preview}")
            except Exception:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] [HYBRID SEARCH] Unable to preview raw data")
        
        # If the RPC returned an error or no data, return an empty list
        if not response:
            return []
        if getattr(response, "error", None):
            print("[HYBRID SEARCH] rpc error:", getattr(response, "error"))
            return []
        data = getattr(response, "data", None)
        if not data:
            return []

        related_chunks = []
        for r in data:
            if not isinstance(r, dict):
                continue
            related_chunks.append({
                "content": r.get("content"),
                "metadata": r.get("metadata"),
                "similarity_score": r.get("similarity"),
                "keyword_rank": r.get("keyword_rank", 0.0),
                "hybrid_score": r.get("hybrid_score", 0.0)
            })
        
        # Debug: print the generated related chunks summary
        try:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [HYBRID SEARCH] Generated {len(related_chunks)} results")
            if related_chunks:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] [HYBRID SEARCH] Top result hybrid_score: {related_chunks[0].get('hybrid_score', 0):.4f}")
                print(f"[{datetime.now().strftime('%H:%M:%S')}] [HYBRID SEARCH] Top result similarity: {related_chunks[0].get('similarity_score', 0):.4f}")
                print(f"[{datetime.now().strftime('%H:%M:%S')}] [HYBRID SEARCH] Top result keyword_rank: {related_chunks[0].get('keyword_rank', 0):.4f}")
        except Exception:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [HYBRID SEARCH] Generated {len(related_chunks)} results - details unavailable")
        
        return related_chunks
        
    except Exception as e:
        # Check if it's a "function not found" error
        error_msg = str(e)
        if "PGRST202" in error_msg or "hybrid_search_uni_degree_documents" in error_msg:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [HYBRID SEARCH] ⚠ Hybrid search function not found, falling back to semantic-only search")
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [HYBRID SEARCH] ⚠ Please apply migration: supabase/migrations/20260115000001_create_hybrid_search_for_uni_docs.sql")
            
            # Fallback to semantic-only search using the old function
            try:
                filters = {
                    "filter_university": filter_university,
                    "filter_degree": filter_degree,
                    "filter_degree_level": filter_degree_level
                }
                response = supabase.rpc(
                    "retrieve_rag_uni_degree_documents",
                    {
                        "query_embedding": query_embedding,
                        "match_count": top_k,
                        **filters
                    }
                ).execute()
                
                print(f"[{datetime.now().strftime('%H:%M:%S')}] [SEMANTIC FALLBACK] Using semantic-only search")
                
                if not response or getattr(response, "error", None):
                    return []
                    
                data = getattr(response, "data", None)
                if not data:
                    return []
                
                related_chunks = []
                for r in data:
                    if not isinstance(r, dict):
                        continue
                    # Simulate hybrid score as just similarity for backward compatibility
                    similarity = r.get("similarity", 0.0)
                    related_chunks.append({
                        "content": r.get("content"),
                        "metadata": r.get("metadata"),
                        "similarity_score": similarity,
                        "keyword_rank": 0.0,  # No keyword search in fallback
                        "hybrid_score": similarity  # Just use similarity as hybrid score
                    })
                
                print(f"[{datetime.now().strftime('%H:%M:%S')}] [SEMANTIC FALLBACK] Retrieved {len(related_chunks)} results")
                return related_chunks
                
            except Exception as fallback_error:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] [SEMANTIC FALLBACK] Error in fallback:", fallback_error)
                import traceback
                traceback.print_exc()
                return []
        else:
            # Some other error
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [HYBRID SEARCH] Error:", e)
            import traceback
            traceback.print_exc()
            return []
