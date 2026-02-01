'use client';

import React from 'react';

interface DiffSegment {
  type: 'unchanged' | 'deletion' | 'insertion';
  text: string;
}

interface DiffPreviewProps {
  original: string;
  replacement: string;
  className?: string;
}

/**
 * Component to show inline diff preview with deletions (strikethrough red) and insertions (green)
 * Uses simple word-by-word comparison for clear visualization
 */
export function DiffPreview({ original, replacement, className = '' }: DiffPreviewProps) {
  const segments = generateDiff(original, replacement);
  
  return (
    <div className={`font-mono text-sm leading-relaxed ${className}`}>
      {segments.map((segment, index) => {
        if (segment.type === 'deletion') {
          return (
            <span
              key={index}
              className="bg-red-50 text-red-700 line-through px-0.5"
              title="Will be removed"
            >
              {segment.text}
            </span>
          );
        } else if (segment.type === 'insertion') {
          return (
            <span
              key={index}
              className="bg-green-50 text-green-700 px-0.5 font-medium"
              title="Will be added"
            >
              {segment.text}
            </span>
          );
        } else {
          return (
            <span key={index} className="text-gray-700">
              {segment.text}
            </span>
          );
        }
      })}
    </div>
  );
}

/**
 * Generate diff segments by comparing original and replacement text
 * Simple word-by-word comparison for clear UX
 */
function generateDiff(original: string, replacement: string): DiffSegment[] {
  const segments: DiffSegment[] = [];
  
  // If they're identical, return unchanged
  if (original === replacement) {
    return [{ type: 'unchanged', text: original }];
  }
  
  // Split into words while preserving spaces
  const originalWords = splitPreservingSpaces(original);
  const replacementWords = splitPreservingSpaces(replacement);
  
  // Simple diff: if they have different word counts or different words, show full deletion + insertion
  if (originalWords.length !== replacementWords.length || 
      originalWords.some((word, i) => word !== replacementWords[i])) {
    
    // Check if it's a single-word change (common case: spelling correction)
    if (originalWords.length === replacementWords.length && originalWords.length === 1) {
      segments.push({ type: 'deletion', text: original });
      segments.push({ type: 'insertion', text: replacement });
      return segments;
    }
    
    // For multi-word changes, try to find common prefix/suffix
    let commonPrefixEnd = 0;
    while (
      commonPrefixEnd < originalWords.length &&
      commonPrefixEnd < replacementWords.length &&
      originalWords[commonPrefixEnd] === replacementWords[commonPrefixEnd]
    ) {
      commonPrefixEnd++;
    }
    
    let commonSuffixStart = 0;
    while (
      commonSuffixStart < (originalWords.length - commonPrefixEnd) &&
      commonSuffixStart < (replacementWords.length - commonPrefixEnd) &&
      originalWords[originalWords.length - 1 - commonSuffixStart] ===
        replacementWords[replacementWords.length - 1 - commonSuffixStart]
    ) {
      commonSuffixStart++;
    }
    
    // Add common prefix
    if (commonPrefixEnd > 0) {
      segments.push({
        type: 'unchanged',
        text: originalWords.slice(0, commonPrefixEnd).join('')
      });
    }
    
    // Add deleted middle
    const originalMiddle = originalWords.slice(
      commonPrefixEnd,
      originalWords.length - commonSuffixStart
    );
    if (originalMiddle.length > 0) {
      segments.push({
        type: 'deletion',
        text: originalMiddle.join('')
      });
    }
    
    // Add inserted middle
    const replacementMiddle = replacementWords.slice(
      commonPrefixEnd,
      replacementWords.length - commonSuffixStart
    );
    if (replacementMiddle.length > 0) {
      segments.push({
        type: 'insertion',
        text: replacementMiddle.join('')
      });
    }
    
    // Add common suffix
    if (commonSuffixStart > 0) {
      segments.push({
        type: 'unchanged',
        text: originalWords.slice(originalWords.length - commonSuffixStart).join('')
      });
    }
    
    return segments;
  }
  
  // If we get here, they're identical (shouldn't happen due to early return)
  return [{ type: 'unchanged', text: original }];
}

/**
 * Split text into words while preserving spaces
 * Returns array like: ['Hello', ' ', 'world', ' ', '!']
 */
function splitPreservingSpaces(text: string): string[] {
  const result: string[] = [];
  let current = '';
  let inSpace = false;
  
  for (const char of text) {
    const isSpace = /\s/.test(char);
    
    if (isSpace !== inSpace) {
      if (current) result.push(current);
      current = char;
      inSpace = isSpace;
    } else {
      current += char;
    }
  }
  
  if (current) result.push(current);
  return result;
}
