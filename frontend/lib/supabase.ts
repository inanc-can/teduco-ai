import { createClient, Session } from '@supabase/supabase-js'

// Create a single supabase client for client-side use
export const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_DEFAULT_KEY!
)

// For compatibility with components that might use createBrowserClient
export const createBrowserClient = () => supabase

// Session cache for performance optimization
let sessionCache: {
  session: Session | null
  expiry: number
} | null = null

/**
 * Get cached session to avoid redundant Supabase auth checks
 * Cache TTL: 5 minutes
 */
export async function getCachedSession() {
  // Check if cache is still valid
  if (sessionCache && Date.now() < sessionCache.expiry) {
    return sessionCache.session
  }
  
  // Cache expired or doesn't exist, fetch fresh
  const { data: { session } } = await supabase.auth.getSession()
  
  // Store in cache for 5 minutes
  sessionCache = {
    session,
    expiry: Date.now() + 5 * 60 * 1000  // 5 minutes
  }
  
  return session
}

/**
 * Invalidate session cache (e.g., on logout)
 */
export function invalidateSessionCache() {
  sessionCache = null
}
