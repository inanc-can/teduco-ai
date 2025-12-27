import { ApiError } from './api-client'

export type ErrorCategory = 
  | 'auth'
  | 'network'
  | 'validation'
  | 'server'
  | 'timeout'
  | 'unknown'

export interface ErrorInfo {
  category: ErrorCategory
  userMessage: string
  technicalMessage: string
  canRetry: boolean
  statusCode?: number
}

/**
 * Classify and format errors for user display
 */
export function handleError(error: unknown): ErrorInfo {
  // Handle ApiError
  if (error instanceof ApiError) {
    return {
      category: categorizeApiError(error),
      userMessage: getUserFriendlyMessage(error),
      technicalMessage: error.message,
      canRetry: canRetryError(error),
      statusCode: error.statusCode,
    }
  }

  // Handle network errors
  if (error instanceof TypeError && error.message.includes('fetch')) {
    return {
      category: 'network',
      userMessage: 'Network connection failed. Please check your internet connection.',
      technicalMessage: error.message,
      canRetry: true,
    }
  }

  // Handle unknown errors
  return {
    category: 'unknown',
    userMessage: 'An unexpected error occurred. Please try again.',
    technicalMessage: error instanceof Error ? error.message : String(error),
    canRetry: true,
  }
}

/**
 * Categorize API errors by status code
 */
function categorizeApiError(error: ApiError): ErrorCategory {
  const { statusCode, code } = error

  // Timeout
  if (code === 'TIMEOUT' || statusCode === 408) {
    return 'timeout'
  }

  // Network error
  if (code === 'NETWORK_ERROR' || statusCode === 0) {
    return 'network'
  }

  // Auth errors
  if (statusCode === 401 || statusCode === 403) {
    return 'auth'
  }

  // Validation errors
  if (statusCode === 400 || statusCode === 422) {
    return 'validation'
  }

  // Server errors
  if (statusCode && statusCode >= 500) {
    return 'server'
  }

  return 'unknown'
}

/**
 * Get user-friendly error messages
 */
function getUserFriendlyMessage(error: ApiError): string {
  const { statusCode, code, message } = error

  // Use custom message if available
  if (message && !message.includes('HTTP')) {
    return message
  }

  // Fallback to generic messages by status code
  switch (statusCode) {
    case 400:
      return 'Invalid request. Please check your input and try again.'
    case 401:
      return 'You need to sign in to continue.'
    case 403:
      return 'You don\'t have permission to perform this action.'
    case 404:
      return 'The requested resource was not found.'
    case 408:
      return 'Request timed out. Please try again.'
    case 422:
      return 'Invalid data provided. Please check your input.'
    case 429:
      return 'Too many requests. Please wait a moment and try again.'
    case 500:
      return 'Server error. Our team has been notified.'
    case 502:
    case 503:
      return 'Service temporarily unavailable. Please try again later.'
    case 504:
      return 'Gateway timeout. Please try again.'
    default:
      return 'An error occurred. Please try again.'
  }
}

/**
 * Determine if an error can be retried
 */
function canRetryError(error: ApiError): boolean {
  const { statusCode, code } = error

  // Can retry timeouts and network errors
  if (code === 'TIMEOUT' || code === 'NETWORK_ERROR') {
    return true
  }

  // Can retry server errors (500+)
  if (statusCode && statusCode >= 500) {
    return true
  }

  // Can retry 408 (timeout) and 429 (rate limit)
  if (statusCode === 408 || statusCode === 429) {
    return true
  }

  // Don't retry client errors (400-499)
  return false
}

/**
 * Log errors for debugging and monitoring
 */
export function logError(error: unknown, context?: Record<string, any>) {
  const errorInfo = handleError(error)

  // In development, log to console
  if (process.env.NODE_ENV === 'development') {
    console.error('[Error]', {
      ...errorInfo,
      context,
      timestamp: new Date().toISOString(),
    })
  }

  // In production, send to error tracking service (e.g., Sentry)
  // if (process.env.NODE_ENV === 'production') {
  //   Sentry.captureException(error, {
  //     extra: { ...errorInfo, context },
  //   })
  // }
}
