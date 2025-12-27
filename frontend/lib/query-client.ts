import { QueryClient, DefaultOptions } from '@tanstack/react-query'
import { config } from './config'

const queryConfig: DefaultOptions = {
  queries: {
    // Data is considered fresh for 1 minute
    staleTime: config.cache.staleTime,
    
    // Garbage collection time - 5 minutes
    gcTime: config.cache.gcTime,
    
    // Don't refetch on window focus in development to reduce noise
    refetchOnWindowFocus: process.env.NODE_ENV === 'production',
    
    // Retry failed requests once
    retry: 1,
    
    // Retry delay increases exponentially
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  },
  mutations: {
    // Retry mutations once on failure
    retry: 1,
    
    // Retry delay for mutations
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  },
}

export function createQueryClient() {
  return new QueryClient({
    defaultOptions: queryConfig,
  })
}

export const queryClient = createQueryClient()
