-- Add columns for caching AI analysis results
ALTER TABLE public.application_letters 
ADD COLUMN last_analysis JSONB,
ADD COLUMN content_hash TEXT;

-- Create index for content_hash lookups
CREATE INDEX IF NOT EXISTS idx_application_letters_content_hash ON public.application_letters(content_hash);

-- Comment the columns
COMMENT ON COLUMN public.application_letters.last_analysis IS 'Cached AI analysis results (suggestions and overall feedback)';
COMMENT ON COLUMN public.application_letters.content_hash IS 'SHA256 hash of content to detect changes and invalidate cache';
