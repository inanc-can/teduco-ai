import { redirect } from "next/navigation"
import { cookies } from "next/headers"
import { createServerClient } from '@supabase/ssr'
import { AppSidebar } from "@/components/app-sidebar"
import { SidebarProvider } from "@/components/ui/sidebar"

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

  // Get user profile from users table
  const { data: profile } = await supabase
    .from('users')
    .select('first_name, last_name, onboarding_completed')
    .eq('user_id', authUser.id)
    .single()

  if (!profile) {
    redirect('/login')
  }

  const fullName = profile 
    ? `${profile.first_name || ''} ${profile.last_name || ''}`.trim()
    : authUser.email?.split('@')[0] || 'User'

  const userData: UserData = {
    name: fullName || 'User',
    email: authUser.email || '',
    avatar: authUser.user_metadata?.avatar_url || '',
  }

  return (
    <SidebarProvider>
      <AppSidebar user={userData} />
      {children}
    </SidebarProvider>
  )
}
