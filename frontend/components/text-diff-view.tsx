'use client';

import { useMemo } from 'react';
import * as Diff from 'diff';
import { cn } from '@/lib/utils';

interface TextDiffViewProps {
  originalText: string;
  correctedText: string;
  className?: string;
}

export function TextDiffView({ originalText, correctedText, className }: TextDiffViewProps) {
  const diff = useMemo(() => {
    return Diff.diffWords(originalText, correctedText);
  }, [originalText, correctedText]);

  // Generate stable keys for diff parts
  const getPartKey = (part: Diff.Change, index: number) => {
    const type = part.added ? 'add' : part.removed ? 'del' : 'eq';
    const valueHash = part.value.substring(0, 20).replace(/\s/g, '_');
    return `${type}-${index}-${valueHash}`;
  };

  return (
    <div className={cn('space-y-6', className)}>
      {/* Side-by-side view */}
      <div className="grid grid-cols-2 gap-4">
        {/* Original */}
        <div className="space-y-2">
          <h3 className="text-sm font-semibold text-muted-foreground">Original</h3>
          <div className="rounded-md border bg-muted/30 p-4 text-sm leading-relaxed">
            {diff.map((part, index) => {
              if (part.added) return null; // Don't show in original
              return (
                <span
                  key={`orig-${getPartKey(part, index)}`}
                  className={cn(
                    part.removed && 'bg-red-200 dark:bg-red-900/30 text-red-900 dark:text-red-200 line-through'
                  )}
                >
                  {part.value}
                </span>
              );
            })}
          </div>
        </div>

        {/* Corrected */}
        <div className="space-y-2">
          <h3 className="text-sm font-semibold text-muted-foreground">Corrected</h3>
          <div className="rounded-md border bg-muted/30 p-4 text-sm leading-relaxed">
            {diff.map((part, index) => {
              if (part.removed) return null; // Don't show in corrected
              return (
                <span
                  key={`corr-${getPartKey(part, index)}`}
                  className={cn(
                    part.added && 'bg-green-200 dark:bg-green-900/30 text-green-900 dark:text-green-200 font-medium'
                  )}
                >
                  {part.value}
                </span>
              );
            })}
          </div>
        </div>
      </div>

      {/* Unified diff view */}
      <div className="space-y-2">
        <h3 className="text-sm font-semibold text-muted-foreground">Changes</h3>
        <div className="rounded-md border bg-muted/30 p-4 text-sm leading-relaxed">
          {diff.map((part, index) => (
            <span
              key={`uni-${getPartKey(part, index)}`}
              className={cn(
                part.removed && 'bg-red-200 dark:bg-red-900/30 text-red-900 dark:text-red-200 line-through',
                part.added && 'bg-green-200 dark:bg-green-900/30 text-green-900 dark:text-green-200 font-medium'
              )}
            >
              {part.value}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
