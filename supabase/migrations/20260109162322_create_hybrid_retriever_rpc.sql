-- Create RPC retriever function for university-based degree RAG search
-- This function queries the rag_uni_degree_documents table

CREATE OR REPLACE FUNCTION public.retrieve_rag_uni_degree_documents (
  query_embedding VECTOR(384),
  match_count INT,
  filter_university TEXT DEFAULT NULL,
  filter_degree TEXT DEFAULT NULL,
  filter_degree_level TEXT DEFAULT NULL
)
RETURNS TABLE (
  id UUID,
  content TEXT,
  metadata JSONB,
  similarity FLOAT
)
LANGUAGE SQL
AS $$
  SELECT id, content, metadata, similarity
  FROM (
    SELECT DISTINCT ON (content)  -- For each exact `content`, keep the most recent row (latest `created_at`)
      id,
      content,
      metadata,
      1 - (embedding <=> query_embedding) AS similarity
    FROM public.rag_uni_degree_documents
    WHERE
      embedding IS NOT NULL
      AND (filter_university IS NULL OR university = filter_university)
      AND (filter_degree IS NULL OR degree = filter_degree)
      AND (filter_degree_level IS NULL OR degree_level = filter_degree_level)
    ORDER BY
      content,
      created_at DESC
  ) AS deduped
  -- Order the deduplicated rows by similarity (highest first) and limit
  ORDER BY similarity DESC
  LIMIT match_count;
$$;
