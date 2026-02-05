-- Create application_letters table for storing user application letters
CREATE TABLE IF NOT EXISTS public.application_letters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    content TEXT NOT NULL DEFAULT '',
    program_id TEXT,
    program_name TEXT,
    status TEXT NOT NULL DEFAULT 'draft',
    word_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_application_letters_user_id ON public.application_letters(user_id);
CREATE INDEX IF NOT EXISTS idx_application_letters_updated_at ON public.application_letters(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_application_letters_status ON public.application_letters(status);

-- Enable Row Level Security
ALTER TABLE public.application_letters ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Users can view their own letters
CREATE POLICY "Users can view their own letters"
    ON public.application_letters
    FOR SELECT
    USING (auth.uid() = user_id);

-- RLS Policy: Users can insert their own letters
CREATE POLICY "Users can insert their own letters"
    ON public.application_letters
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- RLS Policy: Users can update their own letters
CREATE POLICY "Users can update their own letters"
    ON public.application_letters
    FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- RLS Policy: Users can delete their own letters
CREATE POLICY "Users can delete their own letters"
    ON public.application_letters
    FOR DELETE
    USING (auth.uid() = user_id);

-- RLS Policy: Service role has full access
CREATE POLICY "Service role has full access to application_letters"
    ON public.application_letters
    FOR ALL
    USING (auth.role() = 'service_role');

-- Function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION public.update_application_letters_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update updated_at on row update
CREATE TRIGGER update_application_letters_updated_at
    BEFORE UPDATE ON public.application_letters
    FOR EACH ROW
    EXECUTE FUNCTION public.update_application_letters_updated_at();

-- Function to automatically update word_count from content
CREATE OR REPLACE FUNCTION public.update_application_letters_word_count()
RETURNS TRIGGER AS $$
BEGIN
    -- Simple word count: split by whitespace and count non-empty elements
    NEW.word_count = array_length(
        regexp_split_to_array(trim(NEW.content), '\s+'),
        1
    );
    -- Handle empty content case
    IF NEW.content = '' THEN
        NEW.word_count = 0;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update word_count when content changes
CREATE TRIGGER update_application_letters_word_count
    BEFORE INSERT OR UPDATE OF content ON public.application_letters
    FOR EACH ROW
    EXECUTE FUNCTION public.update_application_letters_word_count();
