"use client"

import { useEffect, useState } from "react"
import { useRouter, usePathname } from "next/navigation"
import { supabase } from "@/lib/supabase"
import { AppSidebar } from "@/components/app-sidebar"
import { SidebarProvider } from "@/components/ui/sidebar"

type UserData = {
  name: string
  email: string
  avatar: string
}

export default function Layout({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const pathname = usePathname()
  const [user, setUser] = useState<UserData | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    async function loadUser() {
      try {
        // Get authenticated user
        const { data: { user: authUser }, error: authError } = await supabase.auth.getUser()
        
        if (authError || !authUser) {
          router.push("/login")
          return
        }

        // Get user profile from users table
        const { data: profile, error: profileError } = await supabase
          .from('users')
          .select('first_name, last_name, onboarding_completed')
          .eq('user_id', authUser.id)
          .single()

        if (profileError || !profile) {
          console.error('Profile fetch error:', profileError)
          router.push("/login")
          return
        }

        // Check if onboarding is completed
        // Allow access to settings/progress-tracking even without onboarding
        const allowedWithoutOnboarding = [
          '/auth/settings',
          '/auth/progress-tracking'
        ]
        const isAllowedRoute = allowedWithoutOnboarding.some(route => pathname?.startsWith(route))
        
        if (!profile.onboarding_completed && !isAllowedRoute) {
          router.push('/onboarding')
          return
        }

        const fullName = profile 
          ? `${profile.first_name} ${profile.last_name}`.trim()
          : authUser.email?.split('@')[0] || 'User'

        setUser({
          name: fullName,
          email: authUser.email || '',
          avatar: authUser.user_metadata?.avatar_url || '',
        })
      } catch (error) {
        console.error('Error loading user:', error)
        router.push("/login")
      } finally {
        setIsLoading(false)
      }
    }

    loadUser()
  }, [router, pathname])

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">Loading...</p>
        </div>
      </div>
    )
  }

  if (!user) {
    return null
  }

  return (
    <SidebarProvider>
      <AppSidebar user={user} />
      {children}
    </SidebarProvider>
  )
}