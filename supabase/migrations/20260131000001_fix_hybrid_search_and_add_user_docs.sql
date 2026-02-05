-- Fix hybrid search: normalize keyword scores to 0-1 range using rank normalization
-- The problem: ts_rank returns tiny values (0.001-0.01) while cosine similarity returns 0.3-0.9
-- This makes keyword_weight effectively useless in the hybrid score
-- Fix: Use rank-based normalization where keyword scores are normalized within the result set

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
      ts_rank_cd(to_tsvector('english', rc.content), plainto_tsquery('english', query_text), 32) AS rank
    FROM rag_uni_degree_documents rc
    WHERE
      to_tsvector('english', rc.content) @@ plainto_tsquery('english', query_text)
      AND (filter_university IS NULL OR rc.university = filter_university)
      AND (filter_degree IS NULL OR rc.degree = filter_degree)
      AND (filter_degree_level IS NULL OR rc.degree_level = filter_degree_level)
  ),
  keyword_normalized AS (
    SELECT
      k.id,
      k.rank AS raw_rank,
      CASE
        WHEN max(k.rank) OVER () > 0
        THEN k.rank / max(k.rank) OVER ()
        ELSE 0.0
      END AS norm_rank
    FROM keyword k
  )
  SELECT
    s.id,
    s.content,
    s.metadata,
    s.sim::float AS similarity,
    COALESCE(kn.norm_rank, 0.0)::float AS keyword_rank,
    (semantic_weight * s.sim + keyword_weight * COALESCE(kn.norm_rank, 0.0))::float AS hybrid_score
  FROM semantic s
  LEFT JOIN keyword_normalized kn ON s.id = kn.id
  ORDER BY hybrid_score DESC
  LIMIT match_count;
END;
$$;

GRANT EXECUTE ON FUNCTION hybrid_search_uni_degree_documents TO authenticated, anon;

-- Create table for user document embeddings (for dual retrieval)
CREATE TABLE IF NOT EXISTS public.rag_user_documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  content TEXT NOT NULL,
  embedding VECTOR(384),
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  doc_type TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_rag_user_documents_user_id
ON public.rag_user_documents (user_id);

-- RLS: users can only access their own document embeddings
ALTER TABLE public.rag_user_documents ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own doc embeddings"
ON public.rag_user_documents FOR SELECT
TO authenticated
USING (auth.uid() = user_id);

CREATE POLICY "Service role full access to user doc embeddings"
ON public.rag_user_documents FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- Create table for user profile embeddings
CREATE TABLE IF NOT EXISTS public.rag_user_profile_chunks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  content TEXT NOT NULL,
  embedding VECTOR(384),
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_rag_user_profile_chunks_user_id
ON public.rag_user_profile_chunks (user_id);

ALTER TABLE public.rag_user_profile_chunks ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own profile embeddings"
ON public.rag_user_profile_chunks FOR SELECT
TO authenticated
USING (auth.uid() = user_id);

CREATE POLICY "Service role full access to user profile embeddings"
ON public.rag_user_profile_chunks FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- Hybrid search function for user documents (scoped to user_id)
CREATE OR REPLACE FUNCTION hybrid_search_user_documents(
  p_user_id uuid,
  query_embedding vector(384),
  query_text text,
  match_count int DEFAULT 5,
  semantic_weight float DEFAULT 0.6,
  keyword_weight float DEFAULT 0.4
)
RETURNS TABLE (
  id uuid,
  content text,
  metadata jsonb,
  doc_type text,
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
      ud.id,
      ud.content,
      ud.metadata,
      ud.doc_type,
      1 - (ud.embedding <=> query_embedding::vector) AS sim
    FROM rag_user_documents ud
    WHERE
      ud.user_id = p_user_id
      AND ud.embedding IS NOT NULL
  ),
  keyword AS (
    SELECT
      ud.id,
      ts_rank_cd(to_tsvector('english', ud.content), plainto_tsquery('english', query_text), 32) AS rank
    FROM rag_user_documents ud
    WHERE
      ud.user_id = p_user_id
      AND to_tsvector('english', ud.content) @@ plainto_tsquery('english', query_text)
  ),
  keyword_normalized AS (
    SELECT
      k.id,
      CASE
        WHEN max(k.rank) OVER () > 0
        THEN k.rank / max(k.rank) OVER ()
        ELSE 0.0
      END AS norm_rank
    FROM keyword k
  )
  SELECT
    s.id,
    s.content,
    s.metadata,
    s.doc_type,
    s.sim::float AS similarity,
    COALESCE(kn.norm_rank, 0.0)::float AS keyword_rank,
    (semantic_weight * s.sim + keyword_weight * COALESCE(kn.norm_rank, 0.0))::float AS hybrid_score
  FROM semantic s
  LEFT JOIN keyword_normalized kn ON s.id = kn.id
  ORDER BY hybrid_score DESC
  LIMIT match_count;
END;
$$;

GRANT EXECUTE ON FUNCTION hybrid_search_user_documents TO authenticated, anon;

-- Function to list unique degree programs
CREATE OR REPLACE FUNCTION list_unique_degree_programs()
RETURNS TABLE (
  degree text,
  degree_level text,
  source text
)
LANGUAGE sql
STABLE
AS $$
  SELECT DISTINCT
    r.degree,
    r.degree_level,
    r.metadata->>'source' AS source
  FROM rag_uni_degree_documents r
  WHERE r.degree IS NOT NULL
  ORDER BY r.degree_level, r.degree;
$$;

GRANT EXECUTE ON FUNCTION list_unique_degree_programs TO authenticated, anon;
