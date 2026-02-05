'use client';

import { useState, useCallback, useEffect, useRef } from 'react';
import { LRUCache } from 'lru-cache';
import { AISuggestion } from '@/lib/types/letters';
import { generateMockSuggestions } from '@/lib/mocks/letter-suggestions';
import { useAnalyzeLetter } from '@/hooks/api/use-letters';
import { 
  splitIntoParagraphs, 
  assignSuggestionsToParagraphs, 
  mergeParagraphSuggestions,
  type Paragraph
} from '@/lib/utils';

type AutoSaveStatus = 'idle' | 'saving' | 'saved' | 'error';
type AnalysisStatus = 'idle' | 'analyzing' | 'complete' | 'error';

interface ParagraphCache {
  suggestions: AISuggestion[];
  timestamp: number;
}

interface UseLetterAnalysisOptions {
  letterId: string; // Required for API authorization
  content: string;
  programSlug?: string;
  onAutoSave?: (content: string) => Promise<void>;
  debounceMs?: number;
  useMockData?: boolean; // Toggle between mock and real API
  enableParagraphCaching?: boolean; // Enable smart paragraph-level caching
  autoAnalyze?: boolean; // Enable automatic analysis on content change (default: true)
}

interface UseLetterAnalysisReturn {
  suggestions: AISuggestion[];
  overallFeedback: string | null;
  autoSaveStatus: AutoSaveStatus;
  analysisStatus: AnalysisStatus;
  isAnalyzing: boolean;
  isStale: boolean;
  wordCount: number;
  triggerAnalysis: (force?: boolean) => void;
  clearSuggestions: () => void;
  paragraphCacheStats?: {
    totalParagraphs: number;
    cachedParagraphs: number;
    analyzedParagraphs: number;
  };
}

const PARAGRAPH_CACHE_TTL = 5 * 60 * 1000; // 5 minutes

export function useLetterAnalysis({
  letterId,
  content,
  programSlug,
  onAutoSave,
  debounceMs = 1500, // Reduced from 3500ms - paragraph caching makes this safe
  useMockData = false,
  enableParagraphCaching = true,
  autoAnalyze = false, // Default to false - on-demand analysis only
}: UseLetterAnalysisOptions): UseLetterAnalysisReturn {
  const [suggestions, setSuggestions] = useState<AISuggestion[]>([]);
  const [overallFeedback, setOverallFeedback] = useState<string | null>(null);
  const [autoSaveStatus, setAutoSaveStatus] = useState<AutoSaveStatus>('idle');
  const [analysisStatus, setAnalysisStatus] = useState<AnalysisStatus>('idle');
  const [paragraphCacheStats, setParagraphCacheStats] = useState<{
    totalParagraphs: number;
    cachedParagraphs: number;
    analyzedParagraphs: number;
  }>();
  
  const analysisTimerRef = useRef<NodeJS.Timeout | undefined>(undefined);
  const autoSaveTimerRef = useRef<NodeJS.Timeout | undefined>(undefined);
  const lastContentRef = useRef<string>(content);
  const lastAnalyzedContentRef = useRef<string>('');
  const lastAnalyzedProgramRef = useRef<string | undefined>(programSlug);
  
  // Paragraph-level caching with LRU cache to prevent memory leaks
  const paragraphCacheRef = useRef<LRUCache<string, ParagraphCache>>(
    new LRUCache<string, ParagraphCache>({
      max: 100, // Max 100 cached paragraphs
      ttl: PARAGRAPH_CACHE_TTL, // 5 minutes TTL
      updateAgeOnGet: true, // Refresh TTL on access
    })
  );
  const lastParagraphsRef = useRef<Paragraph[]>([]);
  const triggerAnalysisRef = useRef<(() => void) | null>(null);

  // API mutation for real analysis
  const { mutate: analyzeWithAPI, isPending: isApiPending } = useAnalyzeLetter();

  // Calculate word count
  const wordCount = content.trim() ? content.trim().split(/\s+/).length : 0;

  // Handle analysis errors with rate limiting retry logic
  const handleAnalysisError = useCallback((error: unknown) => {
    console.error('[useLetterAnalysis] API analysis error:', error);
    
    const errorMessage = error instanceof Error ? error.message : String(error);
    const isRateLimit = errorMessage.includes('rate_limit_exceeded') || errorMessage.includes('Rate limit');
    
    if (isRateLimit) {
      console.warn('[useLetterAnalysis] Rate limit hit - suggestions will retry automatically');
      const waitTimeMatch = errorMessage.match(/try again in ([\d.]+)s/);
      const waitTime = waitTimeMatch ? parseFloat(waitTimeMatch[1]) * 1000 : 3000;
      
      setTimeout(() => {
        console.log('[useLetterAnalysis] Retrying analysis after rate limit...');
        triggerAnalysisRef.current?.();
      }, waitTime + 500);
      
      setAnalysisStatus('analyzing');
    } else {
      setAnalysisStatus('error');
      setSuggestions([]);
    }
  }, [])

  // Trigger AI analysis (mock or real) with paragraph-level caching
  const triggerAnalysis = useCallback((force = false) => {
    if (!force && content === lastAnalyzedContentRef.current && programSlug === lastAnalyzedProgramRef.current) {
      console.log('[useLetterAnalysis] Skipping analysis - content and program unchanged');
      return;
    }
    
    if (force) {
      console.log('[useLetterAnalysis] Forcing re-analysis (manual trigger)');
    }

    // Split content into paragraphs
    const currentParagraphs = splitIntoParagraphs(content);
    const lastParagraphs = lastParagraphsRef.current;

    // Detect changed paragraphs
    const lastHashes = new Set(lastParagraphs.map(p => p.hash));
    
    const changedHashes = new Set<string>();
    const unchangedHashes = new Set<string>();
    
    for (const para of currentParagraphs) {
      if (!lastHashes.has(para.hash)) {
        changedHashes.add(para.hash);
      } else {
        unchangedHashes.add(para.hash);
      }
    }

    console.log('[useLetterAnalysis] Paragraph analysis:', {
      total: currentParagraphs.length,
      changed: changedHashes.size,
      unchanged: unchangedHashes.size,
      cachingEnabled: enableParagraphCaching,
      programSlug,
    });

    // LRU cache automatically handles TTL and size limits
    // No manual cleanup needed

    setAnalysisStatus('analyzing');
    
    if (useMockData) {
      // Mock with paragraph caching simulation
      setTimeout(() => {
        const now = Date.now();
        const newSuggestions = generateMockSuggestions(content, programSlug);
        
        if (enableParagraphCaching && changedHashes.size < currentParagraphs.length) {
          // Cache suggestions per paragraph
          const suggestionMap = assignSuggestionsToParagraphs(newSuggestions, currentParagraphs);
          
          for (const [hash, sug] of suggestionMap.entries()) {
            paragraphCacheRef.current.set(hash, {
              suggestions: sug as AISuggestion[],
              timestamp: now
            });
          }
          
          lastParagraphsRef.current = currentParagraphs;
        }
        
        setSuggestions(newSuggestions);
        setAnalysisStatus('complete');
        lastAnalyzedContentRef.current = content;
        lastAnalyzedProgramRef.current = programSlug;
        
        setParagraphCacheStats({
          totalParagraphs: currentParagraphs.length,
          cachedParagraphs: unchangedHashes.size,
          analyzedParagraphs: changedHashes.size
        });
      }, 800);
    } else {
      // Real API with paragraph caching
      const shouldUseCache = enableParagraphCaching && 
                            changedHashes.size > 0 && 
                            unchangedHashes.size > 0 &&
                            changedHashes.size < currentParagraphs.length;

      if (shouldUseCache) {
        console.log('[useLetterAnalysis] Using paragraph cache - analyzing only changed paragraphs');
        
        // Build cached suggestion map
        const cachedSuggestionMap = new Map<string, AISuggestion[]>();
        for (const hash of unchangedHashes) {
          const cached = paragraphCacheRef.current.get(hash);
          if (cached) {
            cachedSuggestionMap.set(hash, cached.suggestions);
          }
        }

        // Extract only changed paragraphs for analysis
        const changedParagraphs = currentParagraphs.filter(p => changedHashes.has(p.hash));
        const analyzableContent = changedParagraphs.map(p => p.text).join('\n\n');
        
        // Analyze only changed content
        analyzeWithAPI(
          { letterId, content: analyzableContent, programSlug, phase: 'both' },
          {
            onSuccess: (data) => {
              console.log('[useLetterAnalysis] Partial analysis complete:', {
                newSuggestions: data.suggestions.length,
                cachedParagraphs: cachedSuggestionMap.size
              });

              const mappedSuggestions: AISuggestion[] = data.suggestions.map((sug) => ({
                id: sug.id,
                category: sug.category as AISuggestion['category'],
                severity: sug.severity as AISuggestion['severity'],
                title: sug.title,
                description: sug.description,
                suggestion: sug.suggestion,
                replacement: sug.replacement,
                type: sug.type as AISuggestion['type'],
                highlightRange: sug.highlightRange,
                originalText: sug.originalText,
                reasoning: sug.reasoning,
                confidence: sug.confidence,
              }));

              // Assign new suggestions to changed paragraphs
              const freshSuggestionMap = assignSuggestionsToParagraphs(
                mappedSuggestions,
                changedParagraphs
              );

              // Update cache for changed paragraphs
              const now = Date.now();
              for (const [hash, sugg] of freshSuggestionMap.entries()) {
                paragraphCacheRef.current.set(hash, {
                  suggestions: sugg as AISuggestion[],
                  timestamp: now
                });
              }

              // Merge cached and fresh suggestions
              const merged = mergeParagraphSuggestions(
                cachedSuggestionMap,
                freshSuggestionMap,
                currentParagraphs
              );

              setSuggestions(merged as AISuggestion[]);
              if (data.overallFeedback) {
                setOverallFeedback(data.overallFeedback);
              }
              setAnalysisStatus('complete');
              lastAnalyzedContentRef.current = content;
              lastAnalyzedProgramRef.current = programSlug;
              lastParagraphsRef.current = currentParagraphs;

              setParagraphCacheStats({
                totalParagraphs: currentParagraphs.length,
                cachedParagraphs: unchangedHashes.size,
                analyzedParagraphs: changedHashes.size
              });
            },
            onError: handleAnalysisError
          }
        );
      } else {
        // Full analysis (no cache benefit)
        console.log('[useLetterAnalysis] Full analysis - no cache benefit');
        
        analyzeWithAPI(
          { letterId, content, programSlug, phase: 'both' },
          {
            onSuccess: (data) => {
              console.log('[useLetterAnalysis] Analysis complete:', { 
                suggestions: data.suggestions.length,
                phase: data.analysisMetadata?.phase,
                cached: data.analysisMetadata?.cached
              });
              
              const mappedSuggestions: AISuggestion[] = data.suggestions.map((sug) => ({
                id: sug.id,
                category: sug.category as AISuggestion['category'],
                severity: sug.severity as AISuggestion['severity'],
                title: sug.title,
                description: sug.description,
                suggestion: sug.suggestion,
                replacement: sug.replacement,
                type: sug.type as AISuggestion['type'],
                highlightRange: sug.highlightRange,
                originalText: sug.originalText,
                reasoning: sug.reasoning,
                confidence: sug.confidence,
              }));

              // Cache all paragraphs
              const now = Date.now();
              const suggestionMap = assignSuggestionsToParagraphs(mappedSuggestions, currentParagraphs);
              for (const [hash, sugg] of suggestionMap.entries()) {
                paragraphCacheRef.current.set(hash, {
                  suggestions: sugg as AISuggestion[],
                  timestamp: now
                });
              }

              setSuggestions(mappedSuggestions);
              if (data.overallFeedback) {
                setOverallFeedback(data.overallFeedback);
              }
              setAnalysisStatus('complete');
              lastAnalyzedContentRef.current = content;
              lastAnalyzedProgramRef.current = programSlug;
              lastParagraphsRef.current = currentParagraphs;

              setParagraphCacheStats({
                totalParagraphs: currentParagraphs.length,
                cachedParagraphs: 0,
                analyzedParagraphs: currentParagraphs.length
              });
            },
            onError: handleAnalysisError
          }
        );
      }
    }
  }, [content, programSlug, useMockData, enableParagraphCaching, analyzeWithAPI, handleAnalysisError]);

  // Store triggerAnalysis in ref for use by handleAnalysisError
  useEffect(() => {
    triggerAnalysisRef.current = triggerAnalysis;
  }, [triggerAnalysis]);

  // Debounced analysis
  useEffect(() => {
    // Skip debounce if auto-analyze is disabled
    if (!autoAnalyze) {
      return;
    }

    // Clear existing timer
    if (analysisTimerRef.current) {
      clearTimeout(analysisTimerRef.current);
    }

    if (!content.trim()) {
      analysisTimerRef.current = setTimeout(() => {
        setSuggestions([]);
        setAnalysisStatus('idle');
      }, 0);
      return;
    }

    // Set new timer for analysis
    analysisTimerRef.current = setTimeout(() => {
      triggerAnalysis();
    }, debounceMs);

    return () => {
      if (analysisTimerRef.current) {
        clearTimeout(analysisTimerRef.current);
      }
    };
  }, [content, programSlug, debounceMs, triggerAnalysis, autoAnalyze]); // Added autoAnalyze to re-evaluate when it changes

  // Auto-save logic
  useEffect(() => {
    if (content === lastContentRef.current) {
      return; // No changes
    }

    lastContentRef.current = content;

    // Clear existing timer
    if (autoSaveTimerRef.current) {
      clearTimeout(autoSaveTimerRef.current);
    }

    if (!content.trim()) {
      autoSaveTimerRef.current = setTimeout(() => {
        setAutoSaveStatus('idle');
      }, 0);
      return;
    }

    // Set new timer for auto-save
    autoSaveTimerRef.current = setTimeout(async () => {
      setAutoSaveStatus('saving');
      try {
        if (onAutoSave) {
          await onAutoSave(content);
        } else {
          // Mock auto-save
          await new Promise(resolve => setTimeout(resolve, 300));
        }
        setAutoSaveStatus('saved');
        
        // Reset to idle after 2 seconds
        setTimeout(() => {
          setAutoSaveStatus('idle');
        }, 2000);
      } catch (error) {
        console.error('Auto-save failed:', error);
        setAutoSaveStatus('error');
      }
    }, 1500); // Auto-save after 1.5 seconds of no typing

    return () => {
      if (autoSaveTimerRef.current) {
        clearTimeout(autoSaveTimerRef.current);
      }
    };
  }, [content, onAutoSave]);

  // Clear suggestions manually (used after applying a suggestion to invalidate stale positions)
  const clearSuggestions = useCallback(() => {
    setSuggestions([]);
    setOverallFeedback(null);
    // Note: We keep paragraph cache intact - it will be invalidated naturally on next analysis
    console.log('[useLetterAnalysis] Suggestions cleared - paragraph cache preserved');
  }, []);

  return {
    suggestions,
    overallFeedback,
    autoSaveStatus,
    analysisStatus,
    isAnalyzing: analysisStatus === 'analyzing' || isApiPending,
    isStale: content.trim() !== lastAnalyzedContentRef.current.trim() || programSlug !== lastAnalyzedProgramRef.current,
    wordCount,
    triggerAnalysis,
    clearSuggestions,
    paragraphCacheStats: enableParagraphCaching ? paragraphCacheStats : undefined,
  };
}
