/**
 * Text matching utilities for anchor-based position finding
 * 
 * Instead of relying on stale absolute positions, we use surrounding context
 * to fuzzy-match and relocate text even after the document has been edited.
 */

export interface SuggestionAnchor {
  contextBefore?: string;
  contextAfter?: string;
  originalText: string;
}

export interface FoundPosition {
  start: number;
  end: number;
  confidence: 'exact' | 'fuzzy' | 'not-found';
}

/**
 * Find the position of text in content using anchor-based matching
 * 
 * Strategy:
 * 1. Try exact match with full context (contextBefore + originalText + contextAfter)
 * 2. Try exact match with originalText only
 * 3. Try case-insensitive match
 * 4. Try fuzzy match using contextBefore and contextAfter separately
 * 
 * @param content - The current document content
 * @param anchor - The anchor information (context and original text)
 * @returns Position if found, null otherwise
 */
export function findSuggestionPosition(
  content: string,
  anchor: SuggestionAnchor
): FoundPosition | null {
  const { contextBefore, contextAfter, originalText } = anchor;

  if (!originalText) {
    return null;
  }

  // Strategy 1: Exact match with full context
  if (contextBefore && contextAfter) {
    const fullPattern = contextBefore + originalText + contextAfter;
    const fullIndex = content.indexOf(fullPattern);
    
    if (fullIndex >= 0) {
      const start = fullIndex + contextBefore.length;
      const end = start + originalText.length;
      return { start, end, confidence: 'exact' };
    }
  }

  // Strategy 2: Exact match with originalText only
  const exactIndex = content.indexOf(originalText);
  if (exactIndex >= 0) {
    // Verify with context if available
    if (contextBefore || contextAfter) {
      const actualBefore = content.substring(
        Math.max(0, exactIndex - (contextBefore?.length || 20)),
        exactIndex
      );
      const actualAfter = content.substring(
        exactIndex + originalText.length,
        Math.min(content.length, exactIndex + originalText.length + (contextAfter?.length || 20))
      );

      // Check if context matches (allowing some flexibility)
      const beforeMatch = !contextBefore || actualBefore.endsWith(contextBefore);
      const afterMatch = !contextAfter || actualAfter.startsWith(contextAfter);

      if (beforeMatch && afterMatch) {
        return { start: exactIndex, end: exactIndex + originalText.length, confidence: 'exact' };
      }
    } else {
      return { start: exactIndex, end: exactIndex + originalText.length, confidence: 'exact' };
    }
  }

  // Strategy 3: Case-insensitive match
  const lowerContent = content.toLowerCase();
  const lowerOriginal = originalText.toLowerCase();
  const caseInsensitiveIndex = lowerContent.indexOf(lowerOriginal);
  
  if (caseInsensitiveIndex >= 0) {
    return {
      start: caseInsensitiveIndex,
      end: caseInsensitiveIndex + originalText.length,
      confidence: 'fuzzy'
    };
  }

  // Strategy 4: Fuzzy match using context anchors
  if (contextBefore || contextAfter) {
    const matches = findFuzzyMatches(content, originalText, contextBefore, contextAfter);
    if (matches.length > 0) {
      // Return the first match (could be improved with scoring)
      const match = matches[0];
      return { start: match.start, end: match.end, confidence: 'fuzzy' };
    }
  }

  return null;
}

/**
 * Find potential matches using fuzzy matching with context
 */
function findFuzzyMatches(
  content: string,
  target: string,
  contextBefore?: string,
  contextAfter?: string
): Array<{ start: number; end: number; score: number }> {
  const matches: Array<{ start: number; end: number; score: number }> = [];
  const words = target.split(/\s+/);
  
  if (words.length === 0) {
    return matches;
  }

  // Look for sequences of words from the target
  const firstWord = words[0];
  let searchIndex = 0;

  while (searchIndex < content.length) {
    const wordIndex = content.toLowerCase().indexOf(firstWord.toLowerCase(), searchIndex);
    
    if (wordIndex === -1) {
      break;
    }

    // Try to match the full sequence starting from this position
    const potentialMatch = content.substring(wordIndex, wordIndex + target.length + 50);
    const similarity = calculateSimilarity(target, potentialMatch.substring(0, target.length));

    if (similarity > 0.7) {
      // Check context if available
      let score = similarity;
      
      if (contextBefore) {
        const actualBefore = content.substring(Math.max(0, wordIndex - contextBefore.length), wordIndex);
        if (actualBefore.includes(contextBefore.substring(contextBefore.length - 10))) {
          score += 0.1;
        }
      }

      if (contextAfter) {
        const actualAfter = content.substring(wordIndex + target.length, wordIndex + target.length + contextAfter.length);
        if (actualAfter.includes(contextAfter.substring(0, 10))) {
          score += 0.1;
        }
      }

      matches.push({
        start: wordIndex,
        end: wordIndex + target.length,
        score
      });
    }

    searchIndex = wordIndex + 1;
  }

  // Sort by score descending
  return matches.sort((a, b) => b.score - a.score);
}

/**
 * Calculate simple string similarity (0-1)
 * Using Levenshtein distance normalized
 */
function calculateSimilarity(str1: string, str2: string): number {
  const longer = str1.length > str2.length ? str1 : str2;

  if (longer.length === 0) {
    return 1.0;
  }

  const distance = levenshteinDistance(str1.toLowerCase(), str2.toLowerCase());
  return (longer.length - distance) / longer.length;
}

/**
 * Calculate Levenshtein distance between two strings
 */
function levenshteinDistance(str1: string, str2: string): number {
  const matrix: number[][] = [];

  for (let i = 0; i <= str2.length; i++) {
    matrix[i] = [i];
  }

  for (let j = 0; j <= str1.length; j++) {
    matrix[0][j] = j;
  }

  for (let i = 1; i <= str2.length; i++) {
    for (let j = 1; j <= str1.length; j++) {
      if (str2.charAt(i - 1) === str1.charAt(j - 1)) {
        matrix[i][j] = matrix[i - 1][j - 1];
      } else {
        matrix[i][j] = Math.min(
          matrix[i - 1][j - 1] + 1, // substitution
          matrix[i][j - 1] + 1,     // insertion
          matrix[i - 1][j] + 1      // deletion
        );
      }
    }
  }

  return matrix[str2.length][str1.length];
}

/**
 * Check if two text ranges overlap
 */
export function rangesOverlap(
  range1: { start: number; end: number },
  range2: { start: number; end: number }
): boolean {
  return range1.end > range2.start && range1.start < range2.end;
}
