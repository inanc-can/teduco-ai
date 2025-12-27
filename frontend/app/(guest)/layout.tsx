import { ErrorBoundary } from "@/components/error-boundary"

export default function GuestLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-background">
      <div className="w-full max-w-md px-4">
        <ErrorBoundary>
          {children}
        </ErrorBoundary>
      </div>
    </div>
  )
}
