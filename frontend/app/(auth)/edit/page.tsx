'use client';

import { redirect } from 'next/navigation';
import { MOCK_LETTER_DRAFTS } from '@/lib/mocks/letter-suggestions';

export default function ApplicationLettersPage() {
  // Redirect to first letter
  if (MOCK_LETTER_DRAFTS.length > 0) {
    redirect(`/edit/${MOCK_LETTER_DRAFTS[0].id}`);
  }

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
