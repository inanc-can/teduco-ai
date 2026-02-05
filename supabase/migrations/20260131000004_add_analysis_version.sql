-- Add version tracking for cache invalidation
ALTER TABLE application_letters
ADD COLUMN IF NOT EXISTS analysis_version INTEGER DEFAULT 1;

-- Create index for faster version queries
CREATE INDEX IF NOT EXISTS idx_application_letters_analysis_version 
ON application_letters(analysis_version);

-- Add comment
COMMENT ON COLUMN application_letters.analysis_version IS 'Incremented on each analysis to prevent cache race conditions and track suggestion state versions';
