-- Create hybrid search function for rag_uni_degree_documents table
-- Combines semantic (vector) + keyword (full-text) search
-- Uses the same parameters as the original hybrid_search but adapted for our table structure

CREATE OR REPLACE FUNCTION hybrid_search_uni_degree_documents(
  query_embedding vector(384),
  query_text text,
  match_count int DEFAULT 5,
  semantic_weight float DEFAULT 0.5,
  keyword_weight float DEFAULT 0.5,
  filter_university TEXT DEFAULT NULL,
  filter_degree TEXT DEFAULT NULL,
  filter_degree_level TEXT DEFAULT NULL
)
RETURNS TABLE (
  id uuid,
  content text,
  metadata jsonb,
  similarity float,
  keyword_rank float,
  hybrid_score float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  WITH semantic AS (
    SELECT 
      rc.id,
      rc.content,
      rc.metadata,
      1 - (rc.embedding <=> query_embedding::vector) AS sim
    FROM rag_uni_degree_documents rc
    WHERE
      embedding IS NOT NULL
      AND (filter_university IS NULL OR rc.university = filter_university)
      AND (filter_degree IS NULL OR rc.degree = filter_degree)
      AND (filter_degree_level IS NULL OR rc.degree_level = filter_degree_level)
  ),
  keyword AS (
    SELECT
      rc.id,
      -- On-the-fly full-text search (no new columns needed)
      ts_rank(to_tsvector('english', rc.content), plainto_tsquery('english', query_text)) AS rank
    FROM rag_uni_degree_documents rc
    WHERE 
      to_tsvector('english', rc.content) @@ plainto_tsquery('english', query_text)
      AND (filter_university IS NULL OR rc.university = filter_university)
      AND (filter_degree IS NULL OR rc.degree = filter_degree)
      AND (filter_degree_level IS NULL OR rc.degree_level = filter_degree_level)
  )
  SELECT 
    s.id,
    s.content,
    s.metadata,
    s.sim::float AS similarity,
    COALESCE(k.rank, 0.0)::float AS keyword_rank,
    (semantic_weight * s.sim + keyword_weight * COALESCE(k.rank, 0.0))::float AS hybrid_score
  FROM semantic s
  LEFT JOIN keyword k ON s.id = k.id
  ORDER BY hybrid_score DESC
  LIMIT match_count;
END;
$$;

-- Grant execute permission to authenticated and anon users
GRANT EXECUTE ON FUNCTION hybrid_search_uni_degree_documents TO authenticated, anon;
