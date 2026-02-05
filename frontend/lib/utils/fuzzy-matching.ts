/**
 * Fuzzy text matching utilities for position recovery
 * Used when text has been edited between analysis time and application time
 */

import { distance } from 'fastest-levenshtein';

export interface FuzzyMatchResult {
  start: number;
  end: number;
  score: number;
  matchedText: string;
}

/**
 * Find the best match for a target string within content using Levenshtein distance
 * Returns the position with highest similarity score
 */
export function findBestFuzzyMatch(
  content: string,
  target: string,
  contextBefore?: string,
  contextAfter?: string,
  minScore = 0.7
): FuzzyMatchResult | null {
  const targetLen = target.length;
  const contentLen = content.length;
  
  if (targetLen === 0 || contentLen === 0 || targetLen > contentLen) {
    return null;
  }

  // Narrow search window using context if available
  let searchStart = 0;
  let searchEnd = contentLen;

  if (contextBefore) {
    const contextIdx = content.indexOf(contextBefore);
    if (contextIdx !== -1) {
      searchStart = Math.max(0, contextIdx + contextBefore.length - 10);
    }
  }

  if (contextAfter) {
    const contextIdx = content.indexOf(contextAfter, searchStart);
    if (contextIdx !== -1) {
      searchEnd = Math.min(contentLen, contextIdx + 50);
    }
  }

  let bestMatch: FuzzyMatchResult | null = null;
  
  // Slide window approach - check all possible positions
  for (let i = searchStart; i <= searchEnd - targetLen; i++) {
    const candidate = content.substring(i, i + targetLen);
    const dist = distance(target, candidate);
    const score = 1 - (dist / targetLen);
    
    if (score >= minScore && (!bestMatch || score > bestMatch.score)) {
      bestMatch = {
        start: i,
        end: i + targetLen,
        score,
        matchedText: candidate
      };
      
      // Early exit if we found perfect match
      if (score === 1.0) {
        break;
      }
    }
  }

  return bestMatch;
}

/**
 * Calculate similarity between two strings
 * Returns a score from 0 (completely different) to 1 (identical)
 */
export function calculateSimilarity(str1: string, str2: string): number {
  if (str1 === str2) return 1.0;
  if (!str1 || !str2) return 0.0;
  
  const maxLen = Math.max(str1.length, str2.length);
  if (maxLen === 0) return 1.0;
  
  const dist = distance(str1, str2);
  return 1 - (dist / maxLen);
}

/**
 * Validate that a replacement maintains semantic similarity with original
 * Prevents drastic content changes
 */
export function validateSemanticSimilarity(
  original: string,
  replacement: string,
  minSimilarity = 0.5
): boolean {
  // Exact match always valid
  if (original === replacement) return true;
  
  // Empty replacements invalid
  if (!replacement.trim()) return false;
  
  // For short text, be more strict
  if (original.length < 20) {
    return calculateSimilarity(original, replacement) >= 0.6;
  }
  
  // For longer text, check word-level similarity
  const origWords = original.toLowerCase().split(/\s+/).filter(w => w.length > 3);
  const replWords = replacement.toLowerCase().split(/\s+/).filter(w => w.length > 3);
  
  // Count common significant words
  const origSet = new Set(origWords);
  const commonWords = replWords.filter(w => origSet.has(w)).length;
  
  const wordSimilarity = origWords.length > 0 
    ? commonWords / origWords.length 
    : 0;
  
  return wordSimilarity >= minSimilarity;
}
