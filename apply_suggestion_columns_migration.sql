-- Add columns for tracking suggestion states to application_letters table
-- Run this directly in your Supabase SQL editor

ALTER TABLE public.application_letters
ADD COLUMN IF NOT EXISTS rejected_suggestion_ids TEXT[] DEFAULT '{}',
ADD COLUMN IF NOT EXISTS applied_suggestion_metadata JSONB DEFAULT '[]'::jsonb;

-- Add comments
COMMENT ON COLUMN public.application_letters.rejected_suggestion_ids IS 'Array of suggestion IDs that user has explicitly rejected';
COMMENT ON COLUMN public.application_letters.applied_suggestion_metadata IS 'Array of objects tracking applied suggestions with {id, appliedAt, historyEntryId}';

-- Verify the columns were added
SELECT column_name, data_type, column_default 
FROM information_schema.columns 
WHERE table_name = 'application_letters' 
AND column_name IN ('rejected_suggestion_ids', 'applied_suggestion_metadata');
