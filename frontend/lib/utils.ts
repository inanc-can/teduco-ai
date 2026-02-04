import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// ============= Paragraph-Level Caching Utilities =============

export interface Paragraph {
  hash: string;
  text: string;
  startPos: number;
  endPos: number;
  index: number;
}

export interface Suggestion {
  id: string;
  highlightRange?: {
    start: number;
    end: number;
  };
  [key: string]: any;
}

/**
 * Split content into paragraphs with position tracking.
 * Paragraphs are separated by double newlines or single newlines followed by specific patterns.
 */
export function splitIntoParagraphs(content: string): Paragraph[] {
  if (!content.trim()) {
    return [];
  }

  const paragraphs: Paragraph[] = [];
  
  // Split on double newlines, but keep track of positions
  // Also treat single newlines followed by capital letters as paragraph breaks
  const lines = content.split('\n');
  let currentParagraph = '';
  let currentStartPos = 0;
  let currentPos = 0;
  let paragraphIndex = 0;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const trimmedLine = line.trim();
    
    // Check if this should be a new paragraph
    const isNewParagraph = 
      !currentParagraph || // First line
      (i > 0 && lines[i - 1].trim() === '') || // Previous line was empty
      (trimmedLine && /^[A-Z]/.test(trimmedLine) && currentParagraph.length > 100); // New sentence after long paragraph

    if (isNewParagraph && currentParagraph.trim()) {
      // Finish current paragraph
      const paragraphText = currentParagraph.trim();
      const hash = hashParagraphSync(paragraphText);
      
      paragraphs.push({
        hash,
        text: paragraphText,
        startPos: currentStartPos,
        endPos: currentPos - 1,
        index: paragraphIndex++
      });
      
      currentParagraph = '';
      currentStartPos = currentPos + (line === '' ? 1 : 0); // Skip empty lines
    }

    if (line) {
      currentParagraph += (currentParagraph ? '\n' : '') + line;
    }
    
    currentPos += line.length + 1; // +1 for newline character
  }

  // Add final paragraph
  if (currentParagraph.trim()) {
    const paragraphText = currentParagraph.trim();
    const hash = hashParagraphSync(paragraphText);
    
    paragraphs.push({
      hash,
      text: paragraphText,
      startPos: currentStartPos,
      endPos: content.length,
      index: paragraphIndex
    });
  }

  return paragraphs;
}

/**
 * Generate SHA-256 hash for paragraph content.
 * Uses Web Crypto API for fast hashing.
 */
export async function hashParagraph(text: string): Promise<string> {
  // Normalize whitespace before hashing
  const normalized = text.trim().replace(/\s+/g, ' ');
  
  if (typeof window !== 'undefined' && window.crypto?.subtle) {
    // Browser environment
    const msgBuffer = new TextEncoder().encode(normalized);
    const hashBuffer = await crypto.subtle.digest('SHA-256', msgBuffer);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  } else {
    // Fallback to simple hash for SSR
    let hash = 0;
    for (let i = 0; i < normalized.length; i++) {
      const char = normalized.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    return Math.abs(hash).toString(16);
  }
}

/**
 * Synchronous version of hashParagraph for immediate use.
 */
export function hashParagraphSync(text: string): string {
  const normalized = text.trim().replace(/\s+/g, ' ');
  let hash = 0;
  
  for (let i = 0; i < normalized.length; i++) {
    const char = normalized.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash;
  }
  
  return Math.abs(hash).toString(16).padStart(8, '0');
}

/**
 * Assign suggestions to paragraphs based on their position.
 */
export function assignSuggestionsToParagraphs(
  suggestions: Suggestion[],
  paragraphs: Paragraph[]
): Map<string, Suggestion[]> {
  const map = new Map<string, Suggestion[]>();

  for (const suggestion of suggestions) {
    if (!suggestion.highlightRange) continue;

    const suggestionStart = suggestion.highlightRange.start;
    
    // Find which paragraph contains this suggestion
    const paragraph = paragraphs.find(
      p => suggestionStart >= p.startPos && suggestionStart < p.endPos
    );

    if (paragraph) {
      const existing = map.get(paragraph.hash) || [];
      
      // Convert absolute position to paragraph-relative position
      const relativeSuggestion = {
        ...suggestion,
        highlightRange: {
          start: suggestion.highlightRange.start - paragraph.startPos,
          end: suggestion.highlightRange.end - paragraph.startPos
        },
        _originalStart: suggestion.highlightRange.start,
        _originalEnd: suggestion.highlightRange.end,
        _paragraphHash: paragraph.hash
      };
      
      existing.push(relativeSuggestion);
      map.set(paragraph.hash, existing);
    }
  }

  return map;
}

/**
 * Merge cached and fresh paragraph suggestions, adjusting positions.
 */
export function mergeParagraphSuggestions(
  cachedSuggestions: Map<string, Suggestion[]>,
  freshSuggestions: Map<string, Suggestion[]>,
  currentParagraphs: Paragraph[]
): Suggestion[] {
  const merged: Suggestion[] = [];
  const usedIds = new Set<string>();

  // Add fresh suggestions first (priority)
  for (const paragraph of currentParagraphs) {
    const fresh = freshSuggestions.get(paragraph.hash) || [];
    
    for (const suggestion of fresh) {
      if (usedIds.has(suggestion.id)) continue;
      
      // Convert back to absolute positions
      const absoluteSuggestion = {
        ...suggestion,
        highlightRange: suggestion.highlightRange ? {
          start: suggestion.highlightRange.start + paragraph.startPos,
          end: suggestion.highlightRange.end + paragraph.startPos
        } : undefined,
        _cached: false
      };
      
      merged.push(absoluteSuggestion);
      usedIds.add(suggestion.id);
    }
  }

  // Add cached suggestions for unchanged paragraphs
  for (const paragraph of currentParagraphs) {
    // Skip if we have fresh suggestions for this paragraph
    if (freshSuggestions.has(paragraph.hash)) continue;
    
    const cached = cachedSuggestions.get(paragraph.hash) || [];
    
    for (const suggestion of cached) {
      if (usedIds.has(suggestion.id)) continue;
      
      // Convert back to absolute positions using current paragraph positions
      const absoluteSuggestion = {
        ...suggestion,
        highlightRange: suggestion.highlightRange ? {
          start: suggestion.highlightRange.start + paragraph.startPos,
          end: suggestion.highlightRange.end + paragraph.startPos
        } : undefined,
        _cached: true,
        _cacheAge: Date.now() - (suggestion._timestamp || Date.now())
      };
      
      merged.push(absoluteSuggestion);
      usedIds.add(suggestion.id);
    }
  }

  return merged;
}
