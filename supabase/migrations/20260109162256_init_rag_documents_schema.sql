-- Add extensions
-- TODO: add other extensions for the complex retrievals approaches like BM25 (vchord) etc.
CREATE extension IF NOT EXISTS vector;

-- Create RAG documents table for degree-based retrieval

-- Create Uni Degree documents table
CREATE TABLE IF NOT EXISTS public.rag_uni_degree_documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  content TEXT NOT NULL,
  embedding VECTOR(384),
  metadata JSONB NOT NULL,

  -- Generated columns for filtering
  university TEXT GENERATED ALWAYS AS (metadata->>'university') STORED,
  degree TEXT GENERATED ALWAYS AS (metadata->>'degree') STORED,
  degree_level TEXT GENERATED ALWAYS AS (metadata->>'degree_level') STORED,

  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for filtering by university
CREATE INDEX IF NOT EXISTS idx_rag_uni_degree_documents_university
ON public.rag_uni_degree_documents (university);

-- Create index for filtering by degree
CREATE INDEX IF NOT EXISTS idx_rag_uni_degree_documents_degree
ON public.rag_uni_degree_documents (degree);

-- Create index for filtering by degree level
CREATE INDEX IF NOT EXISTS idx_rag_uni_degree_documents_degree_level
ON public.rag_uni_degree_documents (degree_level);

-- Vector index intentionally skipped for now
-- Reason:
-- - Dataset size (~500 chunks) is too small
-- - Sequential scan is faster and more accurate
-- - Add ivfflat index later when data grows (>10k chunks)

-- Example for future use:
-- CREATE INDEX idx_rag_uni_degree_documents_embedding
-- ON public.rag_uni_degree_documents
-- USING ivfflat (embedding vector_cosine_ops)
-- WITH (lists = 50);
