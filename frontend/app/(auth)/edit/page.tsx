'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useLetters } from '@/hooks/api/use-letters';
import { Loader2Icon } from 'lucide-react';

export default function ApplicationLettersPage() {
  const router = useRouter();
  const { data: letters = [], isLoading } = useLetters();

  useEffect(() => {
    // Redirect to first letter when data is loaded
    if (!isLoading && letters.length > 0) {
      router.replace(`/edit/${letters[0].id}`);
    }
  }, [letters, isLoading, router]);

  // Show loading state while fetching letters
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <Loader2Icon className="h-8 w-8 animate-spin mx-auto mb-2 text-muted-foreground" />
          <p className="text-muted-foreground">Loading your letters...</p>
        </div>
      </div>
    );
  }

  // Show create prompt if no letters exist
  return (
    <div className="flex items-center justify-center h-full">
      <div className="text-center">
        <h2 className="text-2xl font-semibold mb-2">No Letters Yet</h2>
        <p className="text-muted-foreground">
          Click &ldquo;New Letter&rdquo; to create your first application letter.
        </p>
      </div>
    </div>
  );
}
