/**
 * Test utilities and helpers
 */

import { ReactElement } from 'react'
import { render, RenderOptions } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

/**
 * Create a React Query wrapper for tests
 */
export function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        cacheTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
  })
}

/**
 * Wrapper component with providers for testing
 */
export function AllTheProviders({ children }: { children: React.ReactNode }) {
  const queryClient = createTestQueryClient()

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
}

/**
 * Custom render with providers
 */
export function renderWithProviders(
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) {
  return render(ui, { wrapper: AllTheProviders, ...options })
}

/**
 * Wait for async operations to complete
 */
export async function waitForLoadingToFinish() {
  const { waitForElementToBeRemoved, screen } = await import('@testing-library/react')
  
  try {
    await waitForElementToBeRemoved(
      () => screen.queryByText(/loading/i),
      { timeout: 3000 }
    )
  } catch {
    // Loading element may not exist, that's ok
  }
}

/**
 * Mock user profile data
 */
export const mockUserProfile = {
  firstName: 'Test',
  lastName: 'User',
  email: 'test@example.com',
  createdAt: '2025-01-01T00:00:00Z',
}

/**
 * Mock authentication token
 */
export const mockAuthToken = 'mock-jwt-token'

/**
 * Mock chat data
 */
export const mockChat = {
  chatId: 'chat-123',
  userId: 'user-123',
  title: 'Test Chat',
  createdAt: '2025-01-01T00:00:00Z',
}

/**
 * Mock message data
 */
export const mockMessage = {
  id: 'msg-123',
  chatId: 'chat-123',
  role: 'user' as const,
  content: 'Test message',
  timestamp: '2025-01-01T00:00:00Z',
}

// Re-export testing library utilities
export * from '@testing-library/react'
export { default as userEvent } from '@testing-library/user-event'
