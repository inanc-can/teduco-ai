'use client'

import { QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { queryClient } from '@/lib/query-client'
import { useState } from 'react'

export function Providers({ children }: { children: React.ReactNode }) {
  // Create a client instance per component tree
  // This ensures that data is not shared between different requests
  const [client] = useState(() => queryClient)

  return (
    <QueryClientProvider client={client}>
      {children}
      {process.env.NODE_ENV === 'development' && (
        <ReactQueryDevtools 
          initialIsOpen={false}
          position="bottom"
          buttonPosition="bottom-right"
        />
      )}
    </QueryClientProvider>
  )
}
