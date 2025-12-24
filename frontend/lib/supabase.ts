import { createClient } from '@supabase/supabase-js'

// Create a single supabase client for client-side use
export const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_DEFAULT_KEY!
)

// For compatibility with components that might use createBrowserClient
export const createBrowserClient = () => supabase
