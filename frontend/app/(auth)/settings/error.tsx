'use client'

import { useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { AlertCircle } from 'lucide-react'

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    // Log the error to an error reporting service
    console.error('Settings error:', error)
  }, [error])

  return (
    <div className="flex h-full flex-col items-center justify-center gap-4 p-6">
      <div className="flex flex-col items-center gap-2 text-center">
        <AlertCircle className="h-12 w-12 text-destructive" />
        <h2 className="text-2xl font-bold">Unable to load settings</h2>
        <p className="text-muted-foreground max-w-md">
          We couldn&apos;t load your settings. Please try again or contact support if the problem persists.
        </p>
        {error.message && (
          <p className="text-sm text-muted-foreground mt-2 font-mono">
            {error.message}
          </p>
        )}
      </div>
      <div className="flex gap-2">
        <Button onClick={reset}>Try again</Button>
        <Button variant="outline" onClick={() => window.location.href = '/settings'}>
          Reload page
        </Button>
      </div>
    </div>
  )
}
