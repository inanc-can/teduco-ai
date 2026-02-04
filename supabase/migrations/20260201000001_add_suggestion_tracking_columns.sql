-- Add columns for tracking suggestion states
ALTER TABLE public.application_letters
ADD COLUMN IF NOT EXISTS rejected_suggestion_ids TEXT[] DEFAULT '{}',
ADD COLUMN IF NOT EXISTS applied_suggestion_metadata JSONB DEFAULT '[]'::jsonb;

-- Add comment explaining the columns
COMMENT ON COLUMN public.application_letters.rejected_suggestion_ids IS 'Array of suggestion IDs that user has explicitly rejected';
COMMENT ON COLUMN public.application_letters.applied_suggestion_metadata IS 'Array of objects tracking applied suggestions with {id, appliedAt, historyEntryId}';
