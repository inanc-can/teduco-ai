import { NextRequest, NextResponse } from "next/server"

// Mock user data store (in production, use a real database)
let mockUserData = {
  firstName: "Ayşe",
  lastName: "Yılmaz",
  email: "ayse@example.com",
  phone: "0505 123 45 67",
  currentCity: "Istanbul",
  applicantType: "university" as const,
  desiredCountries: ["Germany", "Netherlands"],
  desiredField: ["Computer Science", "Engineering"],
  targetProgram: ["Master's"],
  preferredIntake: "Fall 2025",
  universityName: "Boğaziçi University",
  universityProgram: "Computer Engineering",
  universityGPA: "3.5",
  creditsCompleted: "120",
  expectedGraduation: "June 2025",
  researchFocus: "Machine learning and AI applications",
  portfolioLink: "https://github.com/example",
  documents: ["transcript", "language", "statement"],
  preferredSupport: "Study plan and scholarship search",
  additionalNotes: "Interested in AI research programs",
}

// GET /api/settings - Fetch user settings
export async function GET() {
  try {
    // In production, fetch from database based on authenticated user
    // For now, return mock data
    return NextResponse.json(mockUserData)
  } catch (error) {
    console.error("Error fetching settings:", error)
    return NextResponse.json(
      { error: "Failed to fetch settings" },
      { status: 500 }
    )
  }
}

// PUT /api/settings - Update user settings
export async function PUT(request: NextRequest) {
  try {
    const body = await request.json()
    
    // In production, validate and save to database
    // For now, update mock data
    mockUserData = { ...mockUserData, ...body }
    
    return NextResponse.json({ 
      success: true, 
      data: mockUserData 
    })
  } catch (error) {
    console.error("Error updating settings:", error)
    return NextResponse.json(
      { error: "Failed to update settings" },
      { status: 500 }
    )
  }
}
