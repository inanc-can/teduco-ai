'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { cn } from '@/lib/utils';
import { PlusIcon, FileTextIcon } from 'lucide-react';
import { useLetters } from '@/hooks/api/use-letters';
import { NewLetterDialog } from '@/components/new-letter-dialog';

export default function ApplicationLettersLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const [dialogOpen, setDialogOpen] = useState(false);
  const { data: letters = [], isLoading } = useLetters();

  const formatLastEdited = (isoDate: string) => {
    const date = new Date(isoDate);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffMins < 60) {
      return `${diffMins}m ago`;
    } else if (diffHours < 24) {
      return `${diffHours}h ago`;
    } else if (diffDays === 1) {
      return 'Yesterday';
    } else if (diffDays < 7) {
      return `${diffDays}d ago`;
    } else {
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    }
  };

  return (
    <div className="flex w-screen overflow-hidden">
      {/* Left Sidebar - Letter Drafts */}
      <aside className="w-64 border-r bg-muted/10 flex flex-col">
        <div className="p-4 border-b">
          <Button className="w-full" size="sm" onClick={() => setDialogOpen(true)}>
            <PlusIcon className="h-4 w-4 mr-2" />
            New Letter
          </Button>
        </div>

        <ScrollArea className="flex-1">
          <div className="p-2 space-y-1">
            {isLoading ? (
              <div className="p-4 text-center text-sm text-muted-foreground">
                Loading letters...
              </div>
            ) : letters.length === 0 ? (
              <div className="p-4 text-center text-sm text-muted-foreground">
                No letters yet. Create one to get started!
              </div>
            ) : (
              letters.map((letter) => {
                const isActive = pathname.includes(letter.id);
                return (
                  <Link
                    key={letter.id}
                    href={`/edit/${letter.id}`}
                    className={cn(
                      'block p-3 rounded-lg hover:bg-muted/50 transition-colors',
                      isActive && 'bg-muted'
                    )}
                  >
                    <div className="flex items-start gap-2">
                      <FileTextIcon className="h-4 w-4 mt-0.5 text-muted-foreground shrink-0" />
                      <div className="flex-1 min-w-0">
                        <h3 className="font-medium text-sm truncate">
                          {letter.title}
                        </h3>
                        {letter.programName && (
                          <p className="text-xs text-muted-foreground truncate">
                            {letter.programName}
                          </p>
                        )}
                        <div className="flex items-center justify-between mt-1">
                          <span className="text-xs text-muted-foreground">
                            {formatLastEdited(letter.updatedAt)}
                          </span>
                          <span className="text-xs text-muted-foreground">
                            {letter.wordCount} words
                          </span>
                        </div>
                      </div>
                    </div>
                  </Link>
                );
              })
            )}
          </div>
        </ScrollArea>
      </aside>

      {/* Main Content */}
      <main className="flex-1">
        {children}
      </main>

      {/* New Letter Dialog */}
      <NewLetterDialog open={dialogOpen} onOpenChange={setDialogOpen} />
    </div>
  );
}
