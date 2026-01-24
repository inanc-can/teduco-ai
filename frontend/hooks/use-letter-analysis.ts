'use client';

import { useState, useCallback, useEffect, useRef } from 'react';
import { AISuggestion } from '@/lib/types/letters';
import { generateMockSuggestions } from '@/lib/mocks/letter-suggestions';
import { useAnalyzeLetter } from '@/hooks/api/use-letters';

type AutoSaveStatus = 'idle' | 'saving' | 'saved' | 'error';
type AnalysisStatus = 'idle' | 'analyzing' | 'complete' | 'error';

interface UseLetterAnalysisOptions {
  content: string;
  programSlug?: string;
  onAutoSave?: (content: string) => Promise<void>;
  debounceMs?: number;
  useMockData?: boolean; // Toggle between mock and real API
}

interface UseLetterAnalysisReturn {
  suggestions: AISuggestion[];
  autoSaveStatus: AutoSaveStatus;
  analysisStatus: AnalysisStatus;
  isAnalyzing: boolean;
  wordCount: number;
  triggerAnalysis: () => void;
}

export function useLetterAnalysis({
  content,
  programSlug,
  onAutoSave,
  debounceMs = 2500,
  useMockData = false,
}: UseLetterAnalysisOptions): UseLetterAnalysisReturn {
  const [suggestions, setSuggestions] = useState<AISuggestion[]>([]);
  const [autoSaveStatus, setAutoSaveStatus] = useState<AutoSaveStatus>('idle');
  const [analysisStatus, setAnalysisStatus] = useState<AnalysisStatus>('idle');
  
  const analysisTimerRef = useRef<NodeJS.Timeout | undefined>(undefined);
  const autoSaveTimerRef = useRef<NodeJS.Timeout | undefined>(undefined);
  const lastContentRef = useRef<string>(content);
  const lastAnalyzedContentRef = useRef<string>('');
  const lastAnalyzedProgramRef = useRef<string | undefined>(programSlug);

  // API mutation for real analysis
  const { mutate: analyzeWithAPI, isPending: isApiPending } = useAnalyzeLetter();

  // Calculate word count
  const wordCount = content.trim() ? content.trim().split(/\s+/).length : 0;

  // Trigger AI analysis (mock or real)
  const triggerAnalysis = useCallback(() => {
    if (content === lastAnalyzedContentRef.current && programSlug === lastAnalyzedProgramRef.current) {
      console.log('[useLetterAnalysis] Skipping analysis - content and program unchanged');
      return; // Don't re-analyze same content for same program
    }

    console.log('[useLetterAnalysis] Starting analysis for content:', {
      length: content.length,
      preview: content.substring(0, 100) + '...',
      programSlug,
      programChanged: programSlug !== lastAnalyzedProgramRef.current
    });
    
    setAnalysisStatus('analyzing');
    
    if (useMockData) {
      // Use mock data
      setTimeout(() => {
        const newSuggestions = generateMockSuggestions(content, programSlug);
        setSuggestions(newSuggestions);
        setAnalysisStatus('complete');
        lastAnalyzedContentRef.current = content;
        lastAnalyzedProgramRef.current = programSlug;
      }, 800); // Simulate network delay
    } else {
      // Use real API
      console.log('[useLetterAnalysis] Triggering API analysis...', { 
        contentLength: content.length, 
        programSlug 
      });
      
      analyzeWithAPI(
        { content, programSlug },
        {
          onSuccess: (data) => {
            console.log('[useLetterAnalysis] API analysis success:', {
              suggestionsCount: data.suggestions.length,
              wordCount: data.wordCount,
              contentLength: content.length,
              suggestions: data.suggestions.map(s => ({
                id: s.id,
                title: s.title,
                range: s.highlightRange,
                hasReplacement: !!s.replacement,
                replacement: s.replacement
              }))
            });
            
            // Map API response to AISuggestion format
            const mappedSuggestions: AISuggestion[] = data.suggestions.map((sug) => ({
              id: sug.id,
              category: sug.category as AISuggestion['category'],
              severity: sug.severity as AISuggestion['severity'],
              title: sug.title,
              description: sug.description,
              suggestion: sug.suggestion,
              replacement: sug.replacement,
              highlightRange: sug.highlightRange,
            }));
            setSuggestions(mappedSuggestions);
            setAnalysisStatus('complete');
            lastAnalyzedContentRef.current = content;
            lastAnalyzedProgramRef.current = programSlug;
          },
          onError: (error) => {
            console.error('[useLetterAnalysis] API analysis error:', error);
            setAnalysisStatus('error');
            // Clear suggestions on error - no mock fallback
            setSuggestions([]);
          },
        }
      );
    }
  }, [content, programSlug, useMockData, analyzeWithAPI]);

  // Debounced analysis
  useEffect(() => {
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
  }, [content, programSlug, debounceMs, triggerAnalysis]); // Added programSlug to re-trigger analysis when program changes

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

  return {
    suggestions,
    autoSaveStatus,
    analysisStatus,
    isAnalyzing: analysisStatus === 'analyzing' || isApiPending,
    wordCount,
    triggerAnalysis,
  };
}
