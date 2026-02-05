import { redirect } from "next/navigation"
import { cookies } from "next/headers"
import { createServerClient } from '@supabase/ssr'
import { AppSidebar } from "@/components/app-sidebar"
import { SidebarProvider } from "@/components/ui/sidebar"
import { ErrorBoundary } from "@/components/error-boundary"
import { serverApi } from "@/lib/server-api-client"

type UserData = {
  name: string
  email: string
  avatar: string
}

export default async function AuthLayout({ children }: { children: React.ReactNode }) {
  const cookieStore = await cookies()
  
  // Create server-side Supabase client
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

  // Get authenticated user (middleware ensures this exists)
  const { data: { user: authUser } } = await supabase.auth.getUser()
  
  if (!authUser) {
    redirect('/login')
  }

  // Get user profile from backend API instead of direct database call
  // Fall back to email if profile fetch fails (e.g., new user during onboarding)
  let profile
  try {
    profile = await serverApi.getProfile()
  } catch (error) {
    // Silently fail for 404 (user not in profile table yet, might be new user)
    // Only log non-404 errors
    if (error instanceof Error && !error.message.includes('Not Found')) {
      console.error('Failed to fetch profile:', error)
    }
    // Don't redirect - user might be in onboarding flow
    // Just use email as fallback
    profile = null
  }

  const fullName = profile 
    ? `${profile.firstName || ''} ${profile.lastName || ''}`.trim()
    : authUser.email?.split('@')[0] || 'User'

  const userData: UserData = {
    name: fullName || 'User',
    email: authUser.email || '',
    avatar: authUser.user_metadata?.avatar_url || '',
  }

  return (
    <SidebarProvider>
      <AppSidebar user={userData} />
      <ErrorBoundary>
        {children}
      </ErrorBoundary>
    </SidebarProvider>
  )
}
