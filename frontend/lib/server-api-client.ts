/**
 * Server-side API client for Next.js server components and server actions
 * Use this for calling the backend from server components and server actions
 */

import { config } from './config'
import { cookies } from 'next/headers'
import { createServerClient } from '@supabase/ssr'

export class ServerApiError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public code?: string
  ) {
    super(message)
    this.name = 'ServerApiError'
  }
}

/**
 * Get the auth token from server-side Supabase client
 */
async function getServerAuthToken(): Promise<string | null> {
  const cookieStore = await cookies()
  
  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_DEFAULT_KEY!,
    {
      cookies: {
        get(name: string) {
          return cookieStore.get(name)?.value
        },
      },
    }
  )

  // Use getSession() to get the current session with access token
  const { data: { session }, error } = await supabase.auth.getSession()
  
  if (error) {
    console.error('Failed to get session:', error)
    return null
  }
  
  return session?.access_token || null
}

/**
 * Server-side request to backend API
 */
async function serverRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = await getServerAuthToken()
  
  if (!token) {
    throw new ServerApiError('No authentication token available', 401, 'NO_TOKEN')
  }
  
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${token}`,
    ...options.headers,
  }

  const url = `${config.api.baseUrl}${endpoint}`
  
  const response = await fetch(url, {
    ...options,
    headers,
    cache: 'no-store', // Disable caching for server components
  })

  if (!response.ok) {
    let errorMessage = 'An error occurred'
    let errorCode = 'UNKNOWN_ERROR'
    
    try {
      const errorData = await response.json()
      if (Array.isArray(errorData.detail)) {
        errorMessage = errorData.detail
          .map((err: { loc?: string[]; msg: string }) => `${err.loc?.join('.') || 'field'}: ${err.msg}`)
          .join('; ')
      } else if (typeof errorData.detail === 'string') {
        errorMessage = errorData.detail
      } else if (errorData.message) {
        errorMessage = errorData.message
      }
      errorCode = errorData.code || errorCode
    } catch {
      errorMessage = response.statusText || errorMessage
    }
    
    // Log server-side errors for debugging
    if (response.status === 404 && endpoint === '/profile') {
      console.warn(
        `[ServerAPI] 404 ${endpoint}: Backend may not be running or route not registered. ` +
        `Ensure the API is running at ${config.api.baseUrl} (see NEXT_PUBLIC_BACKEND_URL / NEXT_INTERNAL_BACKEND_URL).`
      )
    } else {
      console.error(`[ServerAPI] ${response.status} ${endpoint}:`, errorMessage)
    }

    throw new ServerApiError(errorMessage, response.status, errorCode)
  }

  return response.json()
}

/**
 * Server API client methods
 */
export const serverApi = {
  /**
   * Get user profile (server-side)
   */
  async getProfile() {
    return serverRequest<{
      firstName: string
      lastName: string
      phone?: string
      applicantType?: string
      currentCity?: string
      onboardingCompleted: boolean
      // ... other fields from UserProfileResponse
    }>('/profile', { method: 'GET' })
  },

  /**
   * Get user settings (server-side)
   */
  async getSettings() {
    return serverRequest<{
      firstName: string
      lastName: string
      phone?: string
      applicantType?: string
      currentCity?: string
      onboardingCompleted: boolean
      // ... other fields
    }>('/settings', { method: 'GET' })
  },
}
