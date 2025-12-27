/**
 * Centralized API client for backend communication
 * Provides type-safe methods for all backend endpoints
 */

import { OnboardingFormValues } from "./schemas/onboarding"
import { supabase, getCachedSession } from './supabase'
import { config } from './config'
import { logger, createTimer } from './logger'

export class ApiError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public code?: string
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

interface RequestOptions extends RequestInit {
  timeout?: number
  skipAuth?: boolean
}

class ApiClient {
  private baseUrl: string
  private timeout: number

  constructor() {
    this.baseUrl = config.api.baseUrl
    this.timeout = config.api.timeout
  }

  /**
   * Get authentication headers from Supabase session
   */
  private async getAuthHeaders(): Promise<HeadersInit> {
    const session = await getCachedSession()
    
    // If no session, try to refresh it
    if (!session) {
      const { data: { session: refreshedSession } } = await supabase.auth.refreshSession()
      if (refreshedSession) {
        return {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${refreshedSession.access_token}`,
        }
      }
    }
    
    return {
      'Content-Type': 'application/json',
      ...(session?.access_token && {
        Authorization: `Bearer ${session.access_token}`,
      }),
    }
  }

  /**
   * Create a fetch request with timeout
   */
  private async fetchWithTimeout(
    url: string,
    options: RequestInit,
    timeout: number
  ): Promise<Response> {
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), timeout)

    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
      })
      clearTimeout(timeoutId)
      return response
    } catch (error) {
      clearTimeout(timeoutId)
      if (error instanceof Error && error.name === 'AbortError') {
        throw new ApiError('Request timeout', 408, 'TIMEOUT')
      }
      throw error
    }
  }

  /**
   * Base request method with error handling
   */
  private async request<T>(
    endpoint: string,
    options: RequestOptions = {}
  ): Promise<T> {
    const { timeout = this.timeout, skipAuth = false, ...fetchOptions } = options
    const method = fetchOptions.method || 'GET'
    const timer = createTimer(`${method} ${endpoint}`)

    try {
      // Log request
      logger.logRequest(method, endpoint, fetchOptions.body)

      // Build headers
      let mergedHeaders: Record<string, string>
      
      if (fetchOptions.headers) {
        // If headers are provided, use them as-is (for FormData uploads)
        mergedHeaders = fetchOptions.headers as Record<string, string>
      } else if (skipAuth) {
        // No auth needed
        mergedHeaders = { 'Content-Type': 'application/json' }
      } else {
        // Get default auth headers
        mergedHeaders = await this.getAuthHeaders() as Record<string, string>
      }

      // All requests go directly to the backend
      const url = `${this.baseUrl}${endpoint}`
      
      const response = await this.fetchWithTimeout(
        url,
        {
          ...fetchOptions,
          headers: mergedHeaders,
        },
        timeout
      )

      const duration = timer.end()

      // Handle non-OK responses
      if (!response.ok) {
        let errorMessage = 'An error occurred'
        let errorCode = 'UNKNOWN_ERROR'
        let errorDetails: any = null

        try {
          const errorData = await response.json()
          
          // Handle different error response formats
          if (Array.isArray(errorData.detail)) {
            // FastAPI validation errors (array of objects)
            errorMessage = errorData.detail
              .map((err: any) => `${err.loc?.join('.') || 'field'}: ${err.msg}`)
              .join('; ')
            errorDetails = errorData.detail
          } else if (typeof errorData.detail === 'string') {
            errorMessage = errorData.detail
          } else if (errorData.message) {
            errorMessage = errorData.message
          } else if (errorData.error) {
            errorMessage = errorData.error
          }
          
          errorCode = errorData.code || errorCode
        } catch (parseError) {
          // Failed to parse error response
          errorMessage = response.statusText || errorMessage
        }

        const error = new ApiError(errorMessage, response.status, errorCode)
        logger.logApiError(method, endpoint, error, duration)
        
        // Handle authentication errors
        if (response.status === 401) {
          // Token is invalid or expired - try to refresh session
          if (typeof window !== 'undefined') {
            try {
              const { data: { session: refreshedSession }, error: refreshError } = await supabase.auth.refreshSession()
              if (!refreshError && refreshedSession) {
                // Session refreshed successfully - retry the request won't happen automatically
                // User will need to retry their action
                logger.info('Session refreshed after 401 error')
              } else {
                // Cannot refresh - redirect to login
                window.location.href = '/login'
              }
            } catch {
              // Refresh failed - redirect to login  
              window.location.href = '/login'
            }
          }
        }
        
        throw error
      }

      // Handle 204 No Content
      if (response.status === 204) {
        logger.logResponse(method, endpoint, 204, duration)
        return {} as T
      }

      // Parse JSON response
      const data = await response.json()
      logger.logResponse(method, endpoint, response.status, duration, data)
      return data
    } catch (error) {
      const duration = timer.end()

      // Re-throw ApiErrors
      if (error instanceof ApiError) {
        throw error
      }

      // Handle network errors
      if (error instanceof TypeError) {
        const netError = new ApiError(
          'Network error. Please check your connection.',
          0,
          'NETWORK_ERROR'
        )
        logger.logApiError(method, endpoint, netError, duration)
        throw netError
      }

      // Handle other errors
      const genericError = new ApiError(
        error instanceof Error ? error.message : 'An unexpected error occurred',
        500,
        'INTERNAL_ERROR'
      )
      logger.logApiError(method, endpoint, genericError, duration)
      throw genericError
    }
  }

  /**
   * GET request
   */
  async get<T>(endpoint: string, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: 'GET' })
  }

  /**
   * POST request
   */
  async post<T>(
    endpoint: string,
    data?: unknown,
    options?: RequestOptions
  ): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    })
  }

  /**
   * POST request with FormData (for file uploads)
   */
  async postFormData<T>(
    endpoint: string,
    formData: FormData,
    options?: RequestOptions
  ): Promise<T> {
    const session = await getCachedSession()
    
    // Build headers without Content-Type (browser will set it with boundary)
    const headers: Record<string, string> = {}
    if (session?.access_token) {
      headers['Authorization'] = `Bearer ${session.access_token}`
    }

    return this.request<T>(endpoint, {
      ...options,
      method: 'POST',
      body: formData,
      headers,
    })
  }

  /**
   * PUT request
   */
  async put<T>(
    endpoint: string,
    data?: unknown,
    options?: RequestOptions
  ): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    })
  }

  /**
   * PATCH request
   */
  async patch<T>(
    endpoint: string,
    data?: unknown,
    options?: RequestOptions
  ): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'PATCH',
      body: data ? JSON.stringify(data) : undefined,
    })
  }

  /**
   * DELETE request
   */
  async delete<T>(endpoint: string, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: 'DELETE' })
  }

  // ======================
  // Chat API Methods
  // ======================

  async getChats() {
    return this.get<any[]>('/chats')
  }

  async getChat(chatId: string) {
    return this.get<any>(`/chats/${chatId}`)
  }

  async createChat(data: { title?: string }) {
    return this.post<any>('/chats', data)
  }

  async updateChat(chatId: string, data: { title?: string; emoji?: string; is_pinned?: boolean }) {
    return this.put<any>(`/chats/${chatId}`, data)
  }

  async deleteChat(chatId: string) {
    return this.delete(`/chats/${chatId}`)
  }

  async getMessages(chatId: string) {
    return this.get<any[]>(`/chats/${chatId}/messages`)
  }

  async sendMessage(data: { chatId: string; message: string; files?: File[] }) {
    if (data.files && data.files.length > 0) {
      const formData = new FormData()
      formData.append('content', data.message)
      data.files.forEach((file) => formData.append('files', file))
      
      return this.postFormData<any>(
        `/chats/${data.chatId}/messages`,
        formData
      )
    }

    return this.post<any>(`/chats/${data.chatId}/messages`, {
      content: data.message,
    })
  }

  // ======================
  // Document API Methods
  // ======================

  /**
   * Map frontend document types to database enum values
   * Database enum: 'transcript', 'language', 'statement', 'other'
   */
  private mapDocType(docType?: string): string {
    if (!docType) return 'other'
    
    const mapping: Record<string, string> = {
      'transcript': 'transcript',
      'language': 'language',
      'statement': 'statement',
      'diploma': 'other',        // High school diploma
      'osym': 'other',           // ÖSYM placement
      'course': 'other',         // Course descriptions
      'rec': 'other',            // Recommendation letters
      'portfolio': 'other',      // Portfolio/work samples
    }
    
    return mapping[docType] || 'other'
  }

  async getDocuments() {
    return this.get<any[]>('/documents')
  }

  async uploadDocument(file: File, docType?: string) {
    const formData = new FormData()
    formData.append('file', file)
    // Map frontend doc type to database enum value
    formData.append('doc_type', this.mapDocType(docType))
    
    return this.postFormData<any>('/documents', formData)
  }

  async deleteDocument(documentId: string) {
    return this.delete(`/documents/${documentId}`)
  }

  async getDocumentSignedUrl(documentId: string, expiresIn: number = 3600) {
    return this.get<{ signedUrl: string }>(`/documents/${documentId}/signed-url?expires_sec=${expiresIn}`)
  }

  // ======================
  // Settings API Methods
  // ======================

  async getSettings() {
    return this.get<any>('/settings')
  }

  async updateSettings(data: any) {
    return this.patch<any>('/settings', data)
  }

  // ======================
  // User API Methods
  // ======================

  async getUserProfile() {
    return this.get<any>('/profile')
  }

  async updateUserProfile(data: any) {
    return this.patch<any>('/profile', data)
  }

  async getOnboardingStatus() {
    return this.get<any>('/onboarding')
  }

  async completeOnboarding(data: OnboardingFormValues) {
    return this.post<any>('/onboarding', data)
  }

  // ======================
  // Legacy API Methods (for backwards compatibility)
  // ======================

  async createUser(data: any) {
    return this.post<any>('/users', data)
  }

  async deleteUser(userId: number) {
    return this.delete(`/users/${userId}`)
  }

  async createUniversity(data: any) {
    return this.post<any>('/universities', data)
  }

  async linkUniversityToUser(userId: number, uniId: number) {
    return this.post<void>(`/users/${userId}/universities/${uniId}`)
  }

  async submitOnboarding(data: OnboardingFormValues) {
    return this.post<any>('/onboarding', data)
  }
}

export const apiClient = new ApiClient()

// Legacy API exports for backwards compatibility
export const api = {
  users: {
    create: (data: any) => apiClient.createUser(data),
    delete: (userId: number) => apiClient.deleteUser(userId),
  },
  universities: {
    create: (data: any) => apiClient.createUniversity(data),
    linkToUser: (userId: number, uniId: number) => 
      apiClient.linkUniversityToUser(userId, uniId),
  },
  onboarding: {
    submit: (data: OnboardingFormValues) => apiClient.submitOnboarding(data),
  },
}

// Helper to check if error is ApiError
export function isApiError(error: unknown): error is ApiError {
  return error instanceof ApiError
}

// Helper to format error message for UI
export function getErrorMessage(error: unknown): string {
  if (isApiError(error)) {
    return error.message
  }
  if (error instanceof Error) {
    return error.message
  }
  return 'An unexpected error occurred'
}

export type { RequestOptions }
