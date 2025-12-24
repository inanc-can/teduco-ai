-- Allow service role to bypass RLS for backend operations
-- The service role is used by the backend to write user data during onboarding

-- Users table
CREATE POLICY "Service role full access" ON public.users
  FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);

-- High school education
CREATE POLICY "Service role full access" ON public.high_school_education
  FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);

-- University education
CREATE POLICY "Service role full access" ON public.university_education
  FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);

-- Onboarding preferences
CREATE POLICY "Service role full access" ON public.onboarding_preferences
  FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);

-- Documents
CREATE POLICY "Service role full access" ON public.documents
  FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);
