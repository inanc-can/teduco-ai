import { NextRequest, NextResponse } from "next/server"
import { createServerClient } from '@supabase/ssr'
import { cookies } from "next/headers"
import { z } from 'zod'

// Validate environment variables
const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL
if (!BACKEND_URL) {
  throw new Error('NEXT_PUBLIC_BACKEND_URL environment variable is required')
}

// Input validation schema for PUT requests
const SettingsUpdateSchema = z.object({
  firstName: z.string().min(1).max(100).optional(),
  lastName: z.string().min(1).max(100).optional(),
  phone: z.string().max(20).optional(),
  currentCity: z.string().max(100).optional(),
  applicantType: z.enum(['high-school', 'university']).optional(),
  highSchoolName: z.string().max(200).optional(),
  highSchoolGPA: z.string().max(10).optional(),
  highSchoolGPAScale: z.string().max(10).optional(),
  highSchoolGradYear: z.string().max(4).optional(),
  yksPlaced: z.string().max(500).optional(),
  extracurriculars: z.string().max(2000).optional(),
  universityName: z.string().max(200).optional(),
  universityProgram: z.string().max(200).optional(),
  universityGPA: z.string().max(10).optional(),
  creditsCompleted: z.string().max(10).optional(),
  expectedGraduation: z.string().max(50).optional(),
  studyMode: z.string().max(50).optional(),
  researchFocus: z.string().max(2000).optional(),
  portfolioLink: z.string().url().max(500).optional(),
  desiredCountries: z.array(z.string()).optional(),
  desiredField: z.array(z.string()).optional(),
  targetProgram: z.array(z.string()).optional(),
  preferredIntake: z.string().max(50).optional(),
  preferredSupport: z.string().max(2000).optional(),
  additionalNotes: z.string().max(2000).optional(),
  documentFiles: z.record(z.string(), z.array(z.object({
    name: z.string(),
    size: z.number()
  }))).optional(),
})

// TypeScript interfaces
interface BackendUser {
  first_name: string
  last_name: string
  phone?: string
  current_city?: string
  applicant_type?: 'high-school' | 'university'
}

interface BackendHighSchoolEducation {
  type: 'high-school'
  high_school_name: string
  gpa?: number
  gpa_scale?: number
  grad_year?: number
  yks_placed?: string
  extracurriculars?: string
}

interface BackendUniversityEducation {
  type: 'university'
  university_name: string
  university_program: string
  gpa?: number
  credits_completed?: number
  expected_graduation?: string
  study_mode?: string
  research_focus?: string
  portfolio_link?: string
}

interface BackendPreferences {
  desired_countries?: string[]
  desired_fields?: string[]
  target_programs?: string[]
  preferred_intake?: string
  preferred_support?: string
  additional_notes?: string
}

interface BackendProfile {
  user: BackendUser | null
  education: BackendHighSchoolEducation | BackendUniversityEducation | null
  preferences: BackendPreferences | null
}

interface FrontendSettings {
  firstName?: string
  lastName?: string
  phone?: string
  currentCity?: string
  applicantType?: 'high-school' | 'university'
  highSchoolName?: string
  highSchoolGPA?: string
  highSchoolGPAScale?: string
  highSchoolGradYear?: string
  yksPlaced?: string
  extracurriculars?: string
  universityName?: string
  universityProgram?: string
  universityGPA?: string
  creditsCompleted?: string
  expectedGraduation?: string
  studyMode?: string
  researchFocus?: string
  portfolioLink?: string
  desiredCountries?: string[]
  desiredField?: string[]
  targetProgram?: string[]
  preferredIntake?: string
  preferredSupport?: string
  additionalNotes?: string
}

// Helper to get access token from cookies using Supabase SSR client
async function getAccessToken(): Promise<string | null> {
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
  
  const { data: { session } } = await supabase.auth.getSession()
  return session?.access_token ?? null
}

// Extracted auth helper - DRY principle
async function withAuth(request: NextRequest): Promise<string> {
  // Try Authorization header first
  const authHeader = request.headers.get("Authorization")
  let accessToken = authHeader?.replace("Bearer ", "")
  
  // Fall back to cookies if no header
  if (!accessToken) {
    const token = await getAccessToken()
    if (token) {
      accessToken = token
    }
  }
  
  if (!accessToken) {
    throw new Error("Unauthorized")
  }
  
  return accessToken
}

// Helper to transform backend data to frontend format
function transformBackendToFrontend(data: BackendProfile): FrontendSettings | null {
  const { user, education, preferences } = data
  
  if (!user) return null

  const result: FrontendSettings = {
    firstName: user.first_name,
    lastName: user.last_name,
    phone: user.phone,
    currentCity: user.current_city,
    applicantType: user.applicant_type,
  }

  // Add education data
  if (education) {
    if (education.type === "high-school") {
      result.highSchoolName = education.high_school_name
      result.highSchoolGPA = education.gpa?.toString()
      result.highSchoolGPAScale = education.gpa_scale?.toString()
      result.highSchoolGradYear = education.grad_year?.toString()
      result.yksPlaced = education.yks_placed
      result.extracurriculars = education.extracurriculars
    } else if (education.type === "university") {
      result.universityName = education.university_name
      result.universityProgram = education.university_program
      result.universityGPA = education.gpa?.toString()
      result.creditsCompleted = education.credits_completed?.toString()
      result.expectedGraduation = education.expected_graduation
      result.studyMode = education.study_mode
      result.researchFocus = education.research_focus
      result.portfolioLink = education.portfolio_link
    }
  }

  // Add preferences data
  if (preferences) {
    result.desiredCountries = preferences.desired_countries
    result.desiredField = preferences.desired_fields
    result.targetProgram = preferences.target_programs
    result.preferredIntake = preferences.preferred_intake
    result.preferredSupport = preferences.preferred_support
    result.additionalNotes = preferences.additional_notes
  }

  return result
}

// GET /api/settings - Fetch user settings via backend
export async function GET(request: NextRequest) {
  try {
    const accessToken = await withAuth(request)

    const response = await fetch(`${BACKEND_URL}/profile`, {
      headers: {
        "Authorization": `Bearer ${accessToken}`,
      },
    })

    if (!response.ok) {
      const errorText = await response.text()
      console.error("Backend /profile GET error:", response.status, errorText)
      
      return NextResponse.json(
        { error: "Failed to load profile. Please try again." },
        { status: response.status >= 500 ? 500 : 400 }
      )
    }

    const data: BackendProfile = await response.json()
    const transformed = transformBackendToFrontend(data)
    
    return NextResponse.json(transformed || {})
  } catch (error) {
    if (error instanceof Error && error.message === "Unauthorized") {
      return NextResponse.json(
        { error: "Unauthorized" },
        { status: 401 }
      )
    }
    
    console.error("Error fetching settings:", error)
    return NextResponse.json(
      { error: "Internal error. Please try again." },
      { status: 500 }
    )
  }
}

// PUT /api/settings - Update user settings via backend
export async function PUT(request: NextRequest) {
  try {
    const accessToken = await withAuth(request)

    const body = await request.json()
    
    // Validate input data before sending to backend
    const validated = SettingsUpdateSchema.parse(body)
    
    const response = await fetch(`${BACKEND_URL}/profile`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${accessToken}`,
      },
      body: JSON.stringify(validated),
    })

    if (!response.ok) {
      const errorText = await response.text()
      console.error("Backend /profile PUT error:", response.status, errorText)
      
      return NextResponse.json(
        { error: "Failed to update profile. Please try again." },
        { status: response.status >= 500 ? 500 : 400 }
      )
    }

    const result = await response.json()
    return NextResponse.json(result)
  } catch (error) {
    if (error instanceof Error && error.message === "Unauthorized") {
      return NextResponse.json(
        { error: "Unauthorized" },
        { status: 401 }
      )
    }
    
    if (error instanceof z.ZodError) {
      console.error("Validation error:", error.issues)
      return NextResponse.json(
        { error: "Invalid input data", details: error.issues },
        { status: 400 }
      )
    }
    
    console.error("Error updating settings:", error)
    return NextResponse.json(
      { error: "Internal error. Please try again." },
      { status: 500 }
    )
  }
}
