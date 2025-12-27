/**
 * TypeScript types for API requests and responses
 * These types match the backend response schemas (camelCase)
 */

// User Profile Types
export interface UserProfile {
  firstName: string
  lastName: string
  phone?: string
  applicantType?: 'high-school' | 'university'
  currentCity?: string
  onboardingCompleted: boolean
  
  // High School Education
  highSchoolName?: string
  highSchoolGpa?: number
  highSchoolGpaScale?: number
  highSchoolGradYear?: number
  yksPlaced?: boolean
  
  // University Education
  universityName?: string
  universityProgram?: string
  universityGpa?: number
  creditsCompleted?: number
  expectedGraduation?: string
  studyMode?: string
  researchFocus?: string
  portfolioLink?: string
  
  // Preferences
  targetCountries?: string[]
  targetPrograms?: string[]
  studyLevel?: string
  budget?: string
  timeline?: string
}

// Document Types
export interface Document {
  documentId: string
  userId: string
  docType: 'transcript' | 'language' | 'statement' | 'other'
  storagePath: string
  mimeType: string
  uploadedAt: string
  createdAt?: string
}

// Chat Types
export interface Chat {
  chatId: string
  userId: string
  title: string
  emoji: string
  isPinned: boolean
  createdAt: string
  updatedAt: string
}

// Message Types
export interface Message {
  messageId: string
  chatId: string
  userId: string
  content: string
  role: 'user' | 'assistant' | 'system'
  metadata?: Record<string, unknown>
  createdAt: string
}

// Settings (alias for UserProfile)
export type Settings = UserProfile

// Update Types (partial versions for PATCH requests)
export type UserProfileUpdate = Partial<UserProfile>
export type SettingsUpdate = Partial<Settings>
export type ChatUpdate = Partial<Pick<Chat, 'title' | 'emoji' | 'isPinned'>>

// Request Types
export interface MessageCreate {
  content: string
  metadata?: Record<string, unknown>
}

export interface ChatCreate {
  title?: string
  emoji?: string
  initialMessage?: string
}

// Generic unknown type for flexible contexts
export type UnknownRecord = Record<string, unknown>
