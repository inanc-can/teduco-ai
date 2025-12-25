'use server'

import { revalidatePath } from 'next/cache'
import { cookies } from 'next/headers'
import { createServerClient } from '@supabase/ssr'
import { invalidateSessionCache } from '@/lib/supabase'

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000'

export async function updateProfileSettings(formData: FormData) {
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

  const { data: { user } } = await supabase.auth.getUser()
  
  if (!user) {
    return { error: 'Unauthorized' }
  }

  const settings = {
    firstName: formData.get('firstName') as string,
    lastName: formData.get('lastName') as string,
    phone: formData.get('phone') as string,
    currentCity: formData.get('currentCity') as string,
    applicantType: formData.get('applicantType') as string,
    desiredCountries: JSON.parse(formData.get('desiredCountries') as string || '[]'),
    desiredField: JSON.parse(formData.get('desiredField') as string || '[]'),
    targetProgram: JSON.parse(formData.get('targetProgram') as string || '[]'),
    preferredIntake: formData.get('preferredIntake') as string,
    highSchoolName: formData.get('highSchoolName') as string,
    highSchoolGPA: formData.get('highSchoolGPA') as string,
    highSchoolGPAScale: formData.get('highSchoolGPAScale') as string,
    highSchoolGradYear: formData.get('highSchoolGradYear') as string,
    yksPlaced: formData.get('yksPlaced') as string,
    universityName: formData.get('universityName') as string,
    universityProgram: formData.get('universityProgram') as string,
    universityGPA: formData.get('universityGPA') as string,
    creditsCompleted: formData.get('creditsCompleted') as string,
    expectedGraduation: formData.get('expectedGraduation') as string,
    studyMode: formData.get('studyMode') as string,
    researchFocus: formData.get('researchFocus') as string,
    portfolioLink: formData.get('portfolioLink') as string,
    preferredSupport: formData.get('preferredSupport') as string,
    additionalNotes: formData.get('additionalNotes') as string,
  }

  try {
    const { data: { session } } = await supabase.auth.getSession()
    
    if (!session) {
      return { error: 'No session found' }
    }

    // Call backend API
    const response = await fetch(`${BACKEND_URL}/profile`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${session.access_token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(settings),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.detail || 'Failed to update settings')
    }

    // Invalidate session cache to force refresh
    invalidateSessionCache()
    
    // Revalidate the settings page
    revalidatePath('/settings')
    
    return { success: true }
  } catch (error) {
    console.error('Settings update error:', error)
    return { 
      error: error instanceof Error ? error.message : 'Failed to update settings' 
    }
  }
}

export async function uploadDocument(formData: FormData) {
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

  const { data: { user } } = await supabase.auth.getUser()
  
  if (!user) {
    return { error: 'Unauthorized' }
  }

  try {
    const { data: { session } } = await supabase.auth.getSession()
    
    if (!session) {
      return { error: 'No session found' }
    }

    // Call backend API
    const response = await fetch(`${BACKEND_URL}/documents`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${session.access_token}`,
      },
      body: formData,
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.detail || 'Failed to upload document')
    }

    const result = await response.json()
    
    // Revalidate the settings page
    revalidatePath('/settings')
    
    return { success: true, data: result }
  } catch (error) {
    console.error('Document upload error:', error)
    return { 
      error: error instanceof Error ? error.message : 'Failed to upload document' 
    }
  }
}

export async function deleteDocument(documentId: string) {
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

  const { data: { user } } = await supabase.auth.getUser()
  
  if (!user) {
    return { error: 'Unauthorized' }
  }

  try {
    const { data: { session } } = await supabase.auth.getSession()
    
    if (!session) {
      return { error: 'No session found' }
    }

    // Call backend API
    const response = await fetch(`${BACKEND_URL}/documents/${documentId}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${session.access_token}`,
      },
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.detail || 'Failed to delete document')
    }
    
    // Revalidate the settings page
    revalidatePath('/settings')
    
    return { success: true }
  } catch (error) {
    console.error('Document delete error:', error)
    return { 
      error: error instanceof Error ? error.message : 'Failed to delete document' 
    }
  }
}
