import { Skeleton } from "@/components/ui/skeleton"

export default function SettingsLoading() {
  return (
    <div className="flex h-full flex-col gap-6 p-6">
      {/* Header skeleton */}
      <div className="space-y-2">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-4 w-96" />
      </div>

      {/* Form skeleton */}
      <div className="max-w-2xl space-y-6">
        {/* Profile section */}
        <div className="space-y-4 rounded-lg border p-6">
          <Skeleton className="h-6 w-32" />
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Skeleton className="h-4 w-20" />
              <Skeleton className="h-10 w-full" />
            </div>
            <div className="space-y-2">
              <Skeleton className="h-4 w-20" />
              <Skeleton className="h-10 w-full" />
            </div>
          </div>
          <div className="space-y-2">
            <Skeleton className="h-4 w-16" />
            <Skeleton className="h-10 w-full" />
          </div>
        </div>

        {/* Documents section */}
        <div className="space-y-4 rounded-lg border p-6">
          <Skeleton className="h-6 w-40" />
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="flex items-center justify-between rounded-lg border p-4">
                <div className="flex items-center gap-3">
                  <Skeleton className="h-10 w-10 rounded" />
                  <div className="space-y-1">
                    <Skeleton className="h-4 w-32" />
                    <Skeleton className="h-3 w-20" />
                  </div>
                </div>
                <Skeleton className="h-8 w-20" />
              </div>
            ))}
          </div>
        </div>

        {/* Save button skeleton */}
        <Skeleton className="h-10 w-32" />
      </div>
    </div>
  )
}
