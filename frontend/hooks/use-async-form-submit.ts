import { useState } from 'react'
import { toast } from 'sonner'

interface UseAsyncFormSubmitOptions<T> {
  onSubmit: (data?: T) => Promise<void>
  onError?: (error: Error) => void
  errorMessage?: string
}

/**
 * Reusable hook for handling async form submissions with loading state and error handling
 * 
 * @example
 * const { isLoading, handleSubmit } = useAsyncFormSubmit({
 *   onSubmit: async (data) => {
 *     await apiClient.login(data)
 *   },
 *   errorMessage: 'Failed to login'
 * })
 */
export function useAsyncFormSubmit<T = void>({
  onSubmit,
  onError,
  errorMessage = 'An error occurred',
}: UseAsyncFormSubmitOptions<T>) {
  const [isLoading, setIsLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent, data?: T) => {
    e.preventDefault()
    setIsLoading(true)

    try {
      await onSubmit(data)
    } catch (error) {
      const err = error instanceof Error ? error : new Error(errorMessage)
      
      if (onError) {
        onError(err)
      } else {
        toast.error(err.message || errorMessage)
      }
      
      console.error('Form submission error:', error)
    } finally {
      setIsLoading(false)
    }
  }

  return {
    isLoading,
    handleSubmit,
    setIsLoading,
  }
}
