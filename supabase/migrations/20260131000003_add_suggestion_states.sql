-- Add suggestion state tracking columns to application_letters table
-- This enables persisting rejected and applied suggestion IDs across sessions

-- Add rejected_suggestion_ids array (stores IDs of suggestions user dismissed)
ALTER TABLE application_letters
ADD COLUMN IF NOT EXISTS rejected_suggestion_ids TEXT[] DEFAULT '{}';

-- Add applied_suggestion_metadata (stores detailed info about applied suggestions)
ALTER TABLE application_letters
ADD COLUMN IF NOT EXISTS applied_suggestion_metadata JSONB DEFAULT '[]';

-- Add comments
COMMENT ON COLUMN application_letters.rejected_suggestion_ids IS 'Array of suggestion IDs that user has rejected/dismissed';
COMMENT ON COLUMN application_letters.applied_suggestion_metadata IS 'Array of objects: {id, appliedAt, historyEntryId} for tracking applied suggestions';

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_application_letters_rejected_suggestions 
ON application_letters USING GIN (rejected_suggestion_ids);
