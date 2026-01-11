/**
 * Centralized configuration for the application
 */

export const config = {
  // API Configuration
  api: {
    // Use an internal backend hostname when running on the server inside the container (NEXT_INTERNAL_BACKEND_URL).
    // In the browser, use NEXT_PUBLIC_BACKEND_URL which should point to the externally reachable backend (e.g., http://localhost:8000).
    baseUrl:
      (typeof window === 'undefined'
        ? process.env.NEXT_INTERNAL_BACKEND_URL || process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
        : process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'),
    timeout: 30000, // 30 seconds
  },

  // Supabase Configuration
  supabase: {
    url: process.env.NEXT_PUBLIC_SUPABASE_URL!,
    anonKey: process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_DEFAULT_KEY!,
  },

  // Feature Flags
  features: {
    enableFileUpload: true,
    enableAudioRecording: true,
    enableRealTimeUpdates: true,
  },

  // File Upload Limits
  upload: {
    maxFileSize: 10 * 1024 * 1024, // 10MB
    allowedFileTypes: [
      'application/pdf',
      'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'text/plain',
      'image/jpeg',
      'image/png',
    ],
  },

  // Cache Configuration
  cache: {
    staleTime: 1000 * 60, // 1 minute
    gcTime: 1000 * 60 * 5, // 5 minutes (garbage collection time)
  },
} as const

export type AppConfig = typeof config
