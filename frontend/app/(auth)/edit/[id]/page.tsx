'use client';

import { useState, useRef, useEffect } from 'react';
import { use } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';
import {
  CheckCircle2Icon,
  Loader2Icon,
  AlertCircleIcon,
  InfoIcon,
  SparklesIcon,
  UndoIcon,
  RedoIcon,
  CheckIcon,
  XIcon,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useLetterAnalysis } from '@/hooks/use-letter-analysis';
import { useLetter, useAutoSaveLetter } from '@/hooks/api/use-letters';
import { MOCK_PROGRAMS } from '@/lib/mocks/letter-suggestions';
import type { AISuggestion } from '@/lib/types/letters';
import { DiffPreview } from '@/components/diff-preview';
import { findSuggestionPosition, rangesOverlap, type SuggestionAnchor } from '@/lib/utils/text-matching';

export default function LetterEditorPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const resolvedParams = use(params);
  const letterId = resolvedParams.id;
  
  // Fetch letter from database
  const { data: letter, isLoading: isLoadingLetter } = useLetter(letterId);
  const { mutate: autoSave } = useAutoSaveLetter();
  
  const [content, setContent] = useState('');
  const [selectedProgram, setSelectedProgram] = useState<string>(MOCK_PROGRAMS[0].id);
  const [highlightedSuggestionId, setHighlightedSuggestionId] = useState<string | null>(null);
  const [animatedRange, setAnimatedRange] = useState<{start: number, end: number} | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const highlightLayerRef = useRef<HTMLDivElement>(null);

  // Suggestion state tracking: 'pending' | 'applied' | 'rejected'
  type SuggestionStatus = 'pending' | 'applied' | 'rejected';
  const [suggestionStates, setSuggestionStates] = useState<Map<string, SuggestionStatus>>(new Map());
  const [rejectedSuggestionIds, setRejectedSuggestionIds] = useState<string[]>([]);
  const [appliedSuggestionMetadata, setAppliedSuggestionMetadata] = useState<Array<{
    id: string;
    appliedAt: string;
    historyEntryId?: string;
  }>>([]);

  // Initialize content from database
  useEffect(() => {
    if (letter && content === '') {
      setContent(letter.content);
      if (letter.programId) {
        setSelectedProgram(letter.programId);
      }
      // Initialize history with loaded content
      setHistory([letter.content]);
      setHistoryIndex(0);
      
      // Load persisted suggestion states
      if (letter.rejectedSuggestionIds) {
        setRejectedSuggestionIds(letter.rejectedSuggestionIds);
        const newStates = new Map(suggestionStates);
        letter.rejectedSuggestionIds.forEach(id => newStates.set(id, 'rejected'));
        setSuggestionStates(newStates);
      }
      if (letter.appliedSuggestionMetadata) {
        setAppliedSuggestionMetadata(letter.appliedSuggestionMetadata);
        const newStates = new Map(suggestionStates);
        letter.appliedSuggestionMetadata.forEach(meta => newStates.set(meta.id, 'applied'));
        setSuggestionStates(newStates);
      }
    }
  }, [letter]);

  // History management for undo/redo
  const [history, setHistory] = useState<string[]>([]);
  const [historyIndex, setHistoryIndex] = useState(0);
  const [appliedSuggestionIds, setAppliedSuggestionIds] = useState<Set<string>>(new Set());

  // Update content with history tracking
  const updateContent = (newContent: string, addToHistory = true) => {
    setContent(newContent);
    if (addToHistory && newContent !== history[historyIndex]) {
      // Remove any future history when making a new change
      const newHistory = history.slice(0, historyIndex + 1);
      newHistory.push(newContent);
      setHistory(newHistory);
      setHistoryIndex(newHistory.length - 1);
    }
  };

  // Undo handler
  const handleUndo = () => {
    if (historyIndex > 0) {
      const newIndex = historyIndex - 1;
      setHistoryIndex(newIndex);
      setContent(history[newIndex]);
    }
  };

  // Redo handler
  const handleRedo = () => {
    if (historyIndex < history.length - 1) {
      const newIndex = historyIndex + 1;
      setHistoryIndex(newIndex);
      setContent(history[newIndex]);
    }
  };

  const programSlug = MOCK_PROGRAMS.find(p => p.id === selectedProgram)?.slug;

  // Auto-save callback
  const handleAutoSave = async (contentToSave: string) => {
    if (letterId && letter) {
      // Include suggestion states in auto-save
      autoSave({ 
        letterId, 
        content: contentToSave,
        rejectedSuggestionIds,
        appliedSuggestionMetadata
      });
    }
  };

  const {
    suggestions: rawSuggestions,
    overallFeedback,
    autoSaveStatus,
    analysisStatus,
    isAnalyzing,
    wordCount,
    triggerAnalysis,
    clearSuggestions,
    paragraphCacheStats,
  } = useLetterAnalysis({
    content,
    programSlug,
    onAutoSave: handleAutoSave,
    debounceMs: 1500, // Reduced - paragraph caching makes this safe
    useMockData: false,
    enableParagraphCaching: true, // Enable smart paragraph-level caching
  });

  // Debug: Log suggestions when they change
  console.log('[LetterEditor] Suggestions updated:', {
    count: rawSuggestions.length,
    suggestions: rawSuggestions,
    status: analysisStatus
  });

  // Clear stale rejected IDs when fresh analysis completes
  useEffect(() => {
    if (analysisStatus === 'complete' && rawSuggestions.length > 0) {
      // Get current suggestion IDs from fresh analysis
      const currentSuggestionIds = new Set(rawSuggestions.map(s => s.id));
      
      // Filter out rejected IDs that no longer exist in current suggestions
      const validRejectedIds = rejectedSuggestionIds.filter(id => currentSuggestionIds.has(id));
      
      // Only update if there are stale IDs to remove
      if (validRejectedIds.length !== rejectedSuggestionIds.length) {
        console.log('[LetterEditor] Clearing stale rejected IDs:', {
          before: rejectedSuggestionIds,
          after: validRejectedIds,
          removedCount: rejectedSuggestionIds.length - validRejectedIds.length
        });
        setRejectedSuggestionIds(validRejectedIds);
        
        // Update suggestion states map
        const newStates = new Map(suggestionStates);
        rejectedSuggestionIds.forEach(id => {
          if (!currentSuggestionIds.has(id)) {
            newStates.delete(id);
          }
        });
        setSuggestionStates(newStates);
      }
    }
  }, [analysisStatus, rawSuggestions]);

  // Detect overlapping suggestions
  const detectConflicts = (suggestions: AISuggestion[]): Map<string, string[]> => {
    const conflicts = new Map<string, string[]>();
    
    for (let i = 0; i < suggestions.length; i++) {
      const suggA = suggestions[i];
      if (!suggA.highlightRange) continue;
      
      const conflictIds: string[] = [];
      
      for (let j = i + 1; j < suggestions.length; j++) {
        const suggB = suggestions[j];
        if (!suggB.highlightRange) continue;
        
        // Check if ranges overlap: A.end > B.start && A.start < B.end
        const overlaps = (
          suggA.highlightRange.end > suggB.highlightRange.start &&
          suggA.highlightRange.start < suggB.highlightRange.end
        );
        
        if (overlaps) {
          conflictIds.push(suggB.id);
          
          // Add reverse conflict
          if (!conflicts.has(suggB.id)) {
            conflicts.set(suggB.id, []);
          }
          conflicts.get(suggB.id)!.push(suggA.id);
        }
      }
      
      if (conflictIds.length > 0) {
        conflicts.set(suggA.id, conflictIds);
      }
    }
    
    return conflicts;
  };

  // Filter suggestions based on state and detect conflicts
  const filteredSuggestions = rawSuggestions.filter(s => {
    const state = suggestionStates.get(s.id);
    return !state || state === 'pending'; // Show only pending and new suggestions
  });
  
  const suggestionConflicts = detectConflicts(filteredSuggestions);
  const suggestions = filteredSuggestions;

  // Sync scroll between textarea and highlight layer
  const handleScroll = () => {
    if (textareaRef.current && highlightLayerRef.current) {
      highlightLayerRef.current.scrollTop = textareaRef.current.scrollTop;
      highlightLayerRef.current.scrollLeft = textareaRef.current.scrollLeft;
    }
  };

  // Scroll to and highlight suggestion
  const handleSuggestionClick = (suggestion: AISuggestion) => {
    if (!suggestion.highlightRange || !textareaRef.current) return;

    const { start, end } = suggestion.highlightRange;
    textareaRef.current.focus();
    textareaRef.current.setSelectionRange(start, end);
    textareaRef.current.scrollIntoView({ behavior: 'smooth', block: 'center' });

    // Flash highlight
    setHighlightedSuggestionId(suggestion.id);
    setTimeout(() => setHighlightedSuggestionId(null), 2000);
  };

  // Validate replacement to prevent introducing new errors
  const validateReplacement = (original: string, replacement: string): boolean => {
    // Check for empty/whitespace-only replacement
    if (!replacement || !replacement.trim()) {
      console.error('[Validation] Replacement is empty or whitespace-only');
      return false;
    }
    
    const originalTrimmed = original.trim();
    const replacementTrimmed = replacement.trim();
    
    // Check word count - reject if replacement is suspiciously shorter
    const originalWords = originalTrimmed.split(/\s+/).length;
    const replacementWords = replacementTrimmed.split(/\s+/).length;
    
    // More lenient: Only reject if replacement has < 30% of original words AND original has 6+ words
    // This allows legitimate shortenings while blocking obvious content deletion
    if (replacementWords < originalWords * 0.3 && originalWords >= 6) {
      console.error('[Validation] Replacement too short - would delete content:', {
        original: originalTrimmed,
        replacement: replacementTrimmed,
        originalWords,
        replacementWords
      });
      return false;
    }
    
    // Only validate sentence-ending punctuation preservation (. ! ?)
    // Allow changes to commas, semicolons, colons as they may be legitimately removed
    const originalLast = originalTrimmed[originalTrimmed.length - 1];
    const replacementLast = replacementTrimmed[replacementTrimmed.length - 1];
    
    const sentenceEnders = ['.', '!', '?'];
    
    // If original ended with sentence punctuation, replacement should too
    if (sentenceEnders.includes(originalLast) && !sentenceEnders.includes(replacementLast)) {
      console.warn('[Validation] Replacement removed sentence-ending punctuation:', { original, replacement });
      // Just warn, don't block - AI might be combining sentences
    }
    
    return true;
  };

  // Apply single improvement
  const handleImprove = (suggestion: AISuggestion) => {
    if (!suggestion.highlightRange) {
      console.error('[handleImprove] No highlight range provided:', suggestion);
      return;
    }
    
    // Validate replacement text exists and is not empty/whitespace
    if (!suggestion.replacement || !suggestion.replacement.trim()) {
      console.error('[handleImprove] No valid replacement text provided');
      alert('This suggestion cannot be automatically applied. Please make the changes manually.');
      return;
    }

    // Use anchor-based position finding if we have originalText
    let start = suggestion.highlightRange.start;
    let end = suggestion.highlightRange.end;
    
    if (suggestion.originalText && (suggestion.contextBefore || suggestion.contextAfter)) {
      const anchor: SuggestionAnchor = {
        originalText: suggestion.originalText,
        contextBefore: suggestion.contextBefore,
        contextAfter: suggestion.contextAfter
      };
      
      const foundPosition = findSuggestionPosition(content, anchor);
      
      if (foundPosition) {
        start = foundPosition.start;
        end = foundPosition.end;
        
        if (foundPosition.confidence === 'fuzzy') {
          console.log('[handleImprove] Using fuzzy position match:', { start, end });
        }
      } else {
        console.error('[handleImprove] Could not find text using anchor-based matching');
        console.log('[handleImprove] Auto-refreshing suggestions');
        triggerAnalysis();
        return;
      }
    }
    
    // Validate positions
    if (start < 0 || end > content.length || start >= end) {
      console.error('[handleImprove] Invalid highlight range:', { start, end, contentLength: content.length });
      console.log('[handleImprove] Auto-refreshing suggestions due to invalid positions');
      triggerAnalysis();
      return;
    }
    
    const before = content.substring(0, start);
    const after = content.substring(end);
    const original = content.substring(start, end);
    
    // CRITICAL POSITION VERIFICATION: Check if the text at this position matches what AI analyzed
    if (suggestion.originalText && original !== suggestion.originalText) {
      console.error('[handleImprove] Position verification failed - text has changed');
      console.log('[handleImprove] Auto-refreshing suggestions to get updated positions');
      triggerAnalysis();
      return;
    }
    
    console.log('[handleImprove] Applying improvement:', {
      original,
      replacement: suggestion.replacement,
      start,
      end,
      suggestionId: suggestion.id,
      currentContentLength: content.length
    });
    
    // Use the replacement text provided by AI
    const replacement = suggestion.replacement ?? original;
    
    // Validate replacement to prevent introducing new errors
    if (replacement !== original && !validateReplacement(original, replacement)) {
      alert('Cannot apply this correction: It would delete content or introduce errors. Please review the suggestion manually.');
      console.error('[handleImprove] Blocked bad replacement:', { original, replacement });
      return;
    }
    
    const newContent = before + replacement + after;
    
    // Animate the changed text for visual feedback
    setAnimatedRange({ start, end: start + replacement.length });
    setTimeout(() => setAnimatedRange(null), 2000);
    
    updateContent(newContent);
    
    // Mark suggestion as applied and track metadata
    const newStates = new Map(suggestionStates);
    newStates.set(suggestion.id, 'applied');
    setSuggestionStates(newStates);
    
    const newAppliedMetadata = [
      ...appliedSuggestionMetadata,
      {
        id: suggestion.id,
        appliedAt: new Date().toISOString(),
        historyEntryId: historyIndex.toString()
      }
    ];
    setAppliedSuggestionMetadata(newAppliedMetadata);
    
    // CRITICAL: Clear all pending suggestions immediately - they're now stale after text change
    clearSuggestions();
    
    // Debounce re-analysis to allow paragraph caching to work and prevent rapid position changes
    // Wait 2 seconds to let the user see the green flash animation and document to stabilize
    setTimeout(() => {
      triggerAnalysis();
      console.log('[handleImprove] Triggering fresh analysis after 2s debounce');
    }, 2000);
    
    console.log('[handleImprove] Cleared stale suggestions, will re-analyze in 2 seconds');
  };
  
  // Reject a suggestion (dismiss it permanently)
  const handleRejectSuggestion = (suggestionId: string) => {
    const newStates = new Map(suggestionStates);
    newStates.set(suggestionId, 'rejected');
    setSuggestionStates(newStates);
    
    const newRejected = [...rejectedSuggestionIds, suggestionId];
    setRejectedSuggestionIds(newRejected);
    
    console.log('[handleRejectSuggestion] Rejected suggestion:', suggestionId);
  };

  // Apply all improvements
  const handleImproveAll = () => {
    console.log('[handleImproveAll] Starting batch improvements');
    
    // Filter actionable suggestions
    const actionableSuggestions = suggestions.filter(s => {
      const hasRange = !!s.highlightRange;
      const hasReplacement = !!s.replacement;
      const isActionable = s.severity === 'critical' || s.severity === 'warning' || s.severity === 'info';
      
      if (!hasRange || !hasReplacement || !isActionable) {
        console.log('[handleImproveAll] Skipping suggestion:', {
          id: s.id,
          hasRange,
          hasReplacement,
          isActionable,
          title: s.title
        });
      }
      
      return hasRange && hasReplacement && isActionable;
    });
    
    // Detect conflicts between suggestions
    const conflicts: Map<string, string[]> = new Map();
    for (let i = 0; i < actionableSuggestions.length; i++) {
      const suggA = actionableSuggestions[i];
      if (!suggA.highlightRange) continue;
      
      for (let j = i + 1; j < actionableSuggestions.length; j++) {
        const suggB = actionableSuggestions[j];
        if (!suggB.highlightRange) continue;
        
        if (rangesOverlap(suggA.highlightRange, suggB.highlightRange)) {
          if (!conflicts.has(suggA.id)) conflicts.set(suggA.id, []);
          if (!conflicts.has(suggB.id)) conflicts.set(suggB.id, []);
          conflicts.get(suggA.id)!.push(suggB.id);
          conflicts.get(suggB.id)!.push(suggA.id);
        }
      }
    }
    
    // Warn if conflicts detected
    if (conflicts.size > 0) {
      const conflictCount = Math.floor(conflicts.size / 2); // Each conflict counted twice
      const message = `⚠️ Warning: ${conflictCount} suggestion${conflictCount > 1 ? 's have' : ' has'} overlapping text ranges. Applying all may cause unexpected results.\n\nContinue anyway?`;
      
      if (!confirm(message)) {
        console.log('[handleImproveAll] User cancelled due to conflicts');
        return;
      }
    }
    
    // Sort suggestions by start position (descending) to avoid index shifting
    const sortedSuggestions = [...actionableSuggestions]
      .sort((a, b) => (b.highlightRange?.start || 0) - (a.highlightRange?.start || 0));
    
    console.log('[handleImproveAll] Applying', sortedSuggestions.length, 'suggestions');
    
    let newContent = content;
    const appliedIds = new Set<string>();
    
    for (const suggestion of sortedSuggestions) {
      if (!suggestion.highlightRange || !suggestion.replacement) continue;
      
      const { start, end } = suggestion.highlightRange;
      
      // Validate positions
      if (start < 0 || end > newContent.length || start >= end) {
        console.error('[handleImproveAll] Invalid range for suggestion:', suggestion.id);
        continue;
      }
      
      const before = newContent.substring(0, start);
      const after = newContent.substring(end);
      const original = newContent.substring(start, end);
      
      // Validate replacement
      if (!validateReplacement(original, suggestion.replacement)) {
        console.warn('[handleImproveAll] Skipping invalid replacement for:', suggestion.id);
        continue;
      }
      
      console.log('[handleImproveAll] Applying:', {
        id: suggestion.id,
        original,
        replacement: suggestion.replacement
      });
      
      newContent = before + suggestion.replacement + after;
      appliedIds.add(suggestion.id);
      
      // Mark as applied
      const newStates = new Map(suggestionStates);
      newStates.set(suggestion.id, 'applied');
      setSuggestionStates(newStates);
    }
    
    console.log('[handleImproveAll] Applied', appliedIds.size, 'improvements');
    
    updateContent(newContent);
    setAppliedSuggestionIds(prev => new Set([...prev, ...appliedIds]));
    
    // Update applied metadata
    const newAppliedMetadata = [
      ...appliedSuggestionMetadata,
      ...Array.from(appliedIds).map(id => ({
        id,
        appliedAt: new Date().toISOString(),
        historyEntryId: historyIndex.toString()
      }))
    ];
    setAppliedSuggestionMetadata(newAppliedMetadata);
  };

  // Group suggestions by category
  const suggestionsByCategory = suggestions.reduce((acc, suggestion) => {
    if (!acc[suggestion.category]) {
      acc[suggestion.category] = [];
    }
    acc[suggestion.category].push(suggestion);
    return acc;
  }, {} as Record<string, AISuggestion[]>);

  const categoryLabels = {
    critical: 'Critical Issues',
    grammar: 'Grammar & Style',
    tone: 'Tone & Voice',
    structure: 'Structure',
    'program-alignment': 'Program Alignment',
    qualifications: 'Qualifications',
    motivation: 'Motivation & Goals',
  };

  const categoryIcons = {
    critical: '🚨',
    grammar: '📝',
    tone: '🎯',
    structure: '📋',
    'program-alignment': '🎓',
    qualifications: '⭐',
    motivation: '💡',
  };

  // Show loading state while fetching letter
  if (isLoadingLetter) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <Loader2Icon className="h-8 w-8 animate-spin mx-auto mb-2 text-muted-foreground" />
          <p className="text-muted-foreground">Loading your letter...</p>
        </div>
      </div>
    );
  }

  // If letter not found after loading, show a more helpful message
  if (!letter && !isLoadingLetter) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center space-y-4">
          <AlertCircleIcon className="h-12 w-12 text-muted-foreground mx-auto" />
          <div>
            <h2 className="text-xl font-semibold mb-2">Letter Not Found</h2>
            <p className="text-muted-foreground">
              This letter may have been deleted or doesn&apos;t exist.
            </p>
            <p className="text-sm text-muted-foreground mt-2">
              Select another letter from the sidebar or create a new one.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen">
      {/* Left Column - Editor */}
      <div className="flex-1 flex flex-col border-r">
        {/* Header */}
        <div className="border-b p-4 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-semibold">{letter?.title || 'Application Letter'}</h1>
              <div className="flex items-center gap-1">
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={handleUndo}
                  disabled={historyIndex === 0}
                  title="Undo"
                >
                  <UndoIcon className="h-4 w-4" />
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={handleRedo}
                  disabled={historyIndex === history.length - 1}
                  title="Redo"
                >
                  <RedoIcon className="h-4 w-4" />
                </Button>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {autoSaveStatus === 'saving' && (
                <span className="text-sm text-muted-foreground flex items-center gap-1">
                  <Loader2Icon className="h-3 w-3 animate-spin" />
                  Saving...
                </span>
              )}
              {autoSaveStatus === 'saved' && (
                <span className="text-sm text-green-600 flex items-center gap-1">
                  <CheckCircle2Icon className="h-3 w-3" />
                  Saved
                </span>
              )}
              {autoSaveStatus === 'error' && (
                <span className="text-sm text-red-600 flex items-center gap-1">
                  <AlertCircleIcon className="h-3 w-3" />
                  Error saving
                </span>
              )}
            </div>
          </div>

          <Select value={selectedProgram} onValueChange={setSelectedProgram}>
            <SelectTrigger className="w-full">
              <SelectValue placeholder="Select program" />
            </SelectTrigger>
            <SelectContent>
              {MOCK_PROGRAMS.map((program) => (
                <SelectItem key={program.id} value={program.id}>
                  <div className="flex flex-col items-start">
                    <span className="font-medium">{program.name}</span>
                    <span className="text-xs text-muted-foreground">
                      {program.university} • {program.level}
                    </span>
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Editor Area */}
        <div className="flex-1 p-4 relative overflow-hidden">
          <div className="h-full relative">
            {/* Highlight Layer (behind textarea) */}
            <div
              ref={highlightLayerRef}
              className="absolute inset-0 pointer-events-none overflow-hidden whitespace-pre-wrap overflow-wrap-break-word font-mono text-sm leading-relaxed p-3 border rounded-md"
              style={{
                color: 'transparent',
                caretColor: 'transparent',
              }}
            >
              {(() => {
                // Sort highlights by start position
                const highlights = suggestions
                  .filter(s => s.highlightRange)
                  .map(s => ({
                    ...s.highlightRange!,
                    severity: s.severity,
                    id: s.id,
                  }))
                  .sort((a, b) => a.start - b.start);

                // Debug: Log what we're highlighting
                if (highlights.length > 0) {
                  console.log('[Highlights] Rendering highlights:', highlights.map(h => ({
                    id: h.id,
                    start: h.start,
                    end: h.end,
                    text: content.substring(h.start, h.end),
                    severity: h.severity
                  })));
                }

                if (highlights.length === 0) {
                  return content;
                }

                const segments = [];
                let lastEnd = 0;

                highlights.forEach((highlight, index) => {
                  // Validate highlight range
                  if (highlight.start < 0 || highlight.end > content.length || highlight.start >= highlight.end) {
                    console.error('[Highlights] Invalid highlight range:', {
                      id: highlight.id,
                      start: highlight.start,
                      end: highlight.end,
                      contentLength: content.length
                    });
                    return; // Skip this highlight
                  }
                  
                  // Add unhighlighted text before this highlight
                  if (highlight.start > lastEnd) {
                    segments.push(
                      <span key={`text-${index}`}>
                        {content.substring(lastEnd, highlight.start)}
                      </span>
                    );
                  }

                  // Add highlighted text
                  const isFlashing = highlightedSuggestionId === highlight.id;
                  
                  segments.push(
                    <span
                      key={`highlight-${highlight.id}`}
                      className={cn(
                        'relative transition-all duration-300',
                        highlight.severity === 'warning' && 'bg-yellow-200/40',
                        highlight.severity === 'info' && 'bg-blue-200/40',
                        highlight.severity === 'success' && 'bg-green-200/40',
                        isFlashing && 'animate-pulse bg-opacity-80'
                      )}
                      style={{
                        borderBottom: `2px ${
                          highlight.severity === 'warning'
                            ? 'dashed #eab308'
                            : highlight.severity === 'info'
                            ? 'dashed #3b82f6'
                            : 'dashed #22c55e'
                        }`,
                      }}
                    >
                      {content.substring(highlight.start, highlight.end)}
                    </span>
                  );

                  lastEnd = Math.max(lastEnd, highlight.end);
                });

                // Add remaining text after last highlight
                if (lastEnd < content.length) {
                  segments.push(
                    <span key="text-end">{content.substring(lastEnd)}</span>
                  );
                }

                return segments;
              })()}
            </div>

            {/* Animation Layer (for showing changes) */}
            {animatedRange && (
              <div
                className="absolute inset-0 pointer-events-none overflow-hidden whitespace-pre-wrap overflow-wrap-break-word font-mono text-sm leading-relaxed p-3 border rounded-md"
                style={{
                  color: 'transparent',
                  caretColor: 'transparent',
                }}
              >
                <span>{content.substring(0, animatedRange.start)}</span>
                <span className="animate-flash-green">
                  {content.substring(animatedRange.start, animatedRange.end)}
                </span>
                <span>{content.substring(animatedRange.end)}</span>
              </div>
            )}

            {/* Textarea */}
            <Textarea
              ref={textareaRef}
              value={content}
              onChange={(e) => updateContent(e.target.value)}
              onScroll={handleScroll}
              placeholder="Start writing your application letter here..."
              className="h-full !min-h-full resize-none bg-transparent relative z-10 font-mono text-sm leading-relaxed"
              style={{
                caretColor: 'currentColor',
              }}
            />
          </div>
        </div>

        {/* Footer */}
        <div className="border-t p-3 flex items-center justify-between text-sm text-muted-foreground">
          <span>{wordCount} words</span>
          <div className="flex items-center gap-3">
            {autoSaveStatus === 'saving' && (
              <span className="flex items-center gap-1 text-blue-500">
                <Loader2Icon className="h-3 w-3 animate-spin" />
                Saving...
              </span>
            )}
            {autoSaveStatus === 'saved' && (
              <span className="flex items-center gap-1 text-green-500">
                <CheckCircle2Icon className="h-3 w-3" />
                Saved
              </span>
            )}
            {isAnalyzing && (
              <span className="flex items-center gap-1 text-purple-500">
                <Loader2Icon className="h-3 w-3 animate-spin" />
                Analyzing...
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Right Column - AI Suggestions */}
      <div className="w-96 flex flex-col bg-muted/5 h-screen">
        <div className="border-b p-4 flex-shrink-0">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <SparklesIcon className="h-5 w-5 text-primary" />
              <h2 className="font-semibold">AI Writing Assistant</h2>
            </div>
            <Button 
              size="sm" 
              variant="outline"
              onClick={() => triggerAnalysis(true)}
              disabled={isAnalyzing || !content.trim()}
            >
              <SparklesIcon className="h-3 w-3 mr-1" />
              Analyze
            </Button>
          </div>
          <p className="text-xs text-muted-foreground">
            {suggestions.length > 0
              ? `${suggestions.length} suggestion${suggestions.length !== 1 ? 's' : ''} found`
              : 'Type to get suggestions'}
          </p>
        </div>

        <div className="flex-1 overflow-y-auto">
          <div className="p-4">
            {/* Overall Assessment - with loading skeleton */}
            {isAnalyzing ? (
              <Card className="mb-4 border-primary/20 bg-primary/5">
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-semibold flex items-center gap-2">
                    <SparklesIcon className="h-4 w-4 text-primary" />
                    <Skeleton className="h-4 w-32" />
                  </CardTitle>
                </CardHeader>
                <CardContent className="pt-0 space-y-2">
                  <Skeleton className="h-3 w-full" />
                  <Skeleton className="h-3 w-full" />
                  <Skeleton className="h-3 w-3/4" />
                </CardContent>
              </Card>
            ) : overallFeedback ? (
              <Card className="mb-4 border-primary/20 bg-primary/5">
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-semibold flex items-center gap-2">
                    <SparklesIcon className="h-4 w-4 text-primary" />
                    Overall Assessment
                  </CardTitle>
                </CardHeader>
                <CardContent className="pt-0">
                  <p className="text-sm text-foreground/90 leading-relaxed">
                    {overallFeedback}
                  </p>
                </CardContent>
              </Card>
            ) : null}

            {isAnalyzing && suggestions.length === 0 ? (
              <div className="space-y-2">
                {[1, 2, 3].map((i) => (
                  <Card key={i} className="animate-pulse">
                    <CardHeader className="p-3 pb-2">
                      <div className="flex items-start gap-2">
                        <Skeleton className="h-5 w-5 rounded-full" />
                        <div className="flex-1 space-y-2">
                          <Skeleton className="h-4 w-3/4" />
                          <Skeleton className="h-3 w-1/2" />
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent className="p-3 pt-0 space-y-2">
                      <Skeleton className="h-3 w-full" />
                      <Skeleton className="h-3 w-5/6" />
                      <div className="flex gap-2 mt-2">
                        <Skeleton className="h-8 flex-1" />
                        <Skeleton className="h-8 flex-1" />
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            ) : suggestions.length === 0 ? (
              <Card>
                <CardContent className="pt-6 text-center text-sm text-muted-foreground">
                  {content.trim().length === 0 ? (
                    <>
                      <InfoIcon className="h-8 w-8 mx-auto mb-2 opacity-50" />
                      <p>Start writing to receive AI-powered suggestions</p>
                    </>
                  ) : isAnalyzing ? (
                    <>
                      <Loader2Icon className="h-8 w-8 mx-auto mb-2 animate-spin opacity-50" />
                      <p>Analyzing your letter...</p>
                    </>
                  ) : analysisStatus === 'idle' ? (
                    <>
                      <Loader2Icon className="h-8 w-8 mx-auto mb-2 animate-spin opacity-50" />
                      <p>Waiting for analysis...</p>
                    </>
                  ) : analysisStatus === 'error' ? (
                    <>
                      <AlertCircleIcon className="h-8 w-8 mx-auto mb-2 text-orange-500 opacity-50" />
                      <p className="font-medium text-orange-600 mb-2">Analysis temporarily unavailable</p>
                      <p className="text-xs mb-3">The AI service is busy. Your analysis will retry automatically in a few seconds, or click below to try again.</p>
                      <Button 
                        size="sm" 
                        variant="outline"
                        onClick={() => triggerAnalysis(true)}
                      >
                        Retry Now
                      </Button>
                    </>
                  ) : (
                    <>
                      <CheckCircle2Icon className="h-8 w-8 mx-auto mb-2 text-green-500 opacity-50" />
                      <p>Great work! No major issues found.</p>
                    </>
                  )}
                </CardContent>
              </Card>
            ) : (
              <Accordion type="multiple" defaultValue={Object.keys(suggestionsByCategory)} className="space-y-2">
                {Object.entries(suggestionsByCategory).map(([category, categorySuggestions]) => (
                  <AccordionItem
                    key={category}
                    value={category}
                    className="border rounded-lg px-3"
                  >
                    <AccordionTrigger className="hover:no-underline py-3">
                      <div className="flex items-center gap-2">
                        <span className="text-lg">{categoryIcons[category as keyof typeof categoryIcons]}</span>
                        <span className="font-medium text-sm">
                          {categoryLabels[category as keyof typeof categoryLabels]}
                        </span>
                        <Badge variant="secondary" className="ml-1">
                          {categorySuggestions.length}
                        </Badge>
                      </div>
                    </AccordionTrigger>
                    <AccordionContent className="space-y-3 pt-2 pb-4">
                      {categorySuggestions.map((suggestion) => {
                        const suggestionState = suggestionStates.get(suggestion.id);
                        const isApplied = suggestionState === 'applied';
                        const conflictingIds = suggestionConflicts.get(suggestion.id) || [];
                        const hasConflicts = conflictingIds.length > 0;
                        
                        // Debug: Log replacement value for problematic suggestions
                        if (suggestion.replacement !== undefined && suggestion.replacement !== null) {
                          const trimmed = suggestion.replacement.trim();
                          if (!trimmed) {
                            console.warn('[Suggestion Debug] Empty/whitespace replacement:', {
                              id: suggestion.id,
                              title: suggestion.title,
                              replacement: JSON.stringify(suggestion.replacement),
                              length: suggestion.replacement.length
                            });
                          }
                        }
                        
                        return (
                        <Card
                          key={suggestion.id}
                          className={cn(
                            'transition-colors',
                            isApplied && 'bg-green-50/50 border-green-200',
                            hasConflicts && !isApplied && 'border-orange-200 bg-orange-50/30',
                            !isApplied && !hasConflicts && 'cursor-pointer hover:border-primary/50',
                            highlightedSuggestionId === suggestion.id && 'border-primary'
                          )}
                          onClick={() => !isApplied && handleSuggestionClick(suggestion)}
                        >
                          <CardHeader className="p-3 pb-2">
                            <div className="flex items-start gap-2">
                              {isApplied ? (
                                <Badge variant="default" className="bg-green-600 hover:bg-green-700 text-xs">
                                  Applied ✓
                                </Badge>
                              ) : (
                              <Badge
                                variant={
                                  suggestion.severity === 'critical'
                                    ? 'destructive'
                                    : suggestion.severity === 'warning'
                                    ? 'destructive'
                                    : suggestion.severity === 'success'
                                    ? 'default'
                                    : 'secondary'
                                }
                                className={cn(
                                  "text-xs",
                                  suggestion.severity === 'critical' && "bg-red-600 hover:bg-red-700"
                                )}
                              >
                                {suggestion.severity}
                              </Badge>
                              )}
                              <CardTitle className="text-sm font-medium flex-1">
                                {suggestion.title}
                              </CardTitle>
                              {suggestion.confidence !== undefined && (
                                <span 
                                  className="text-xs text-muted-foreground" 
                                  title={`AI Confidence: ${Math.round(suggestion.confidence * 100)}%`}
                                >
                                  {suggestion.confidence >= 0.9 ? '●' : suggestion.confidence >= 0.7 ? '◐' : '○'}
                                </span>
                              )}
                            </div>
                          </CardHeader>
                          <CardContent className="p-3 pt-0 space-y-2">
                            {hasConflicts && (
                              <div className="bg-orange-50 border border-orange-200 p-2 rounded text-xs text-orange-700">
                                <strong>⚠️ Conflicts with other suggestions</strong>
                                <p className="mt-1 text-xs">Applying this may affect {conflictingIds.length} other suggestion{conflictingIds.length > 1 ? 's' : ''}.</p>
                              </div>
                            )}
                            <p className="text-xs text-muted-foreground">
                              {suggestion.description}
                            </p>
                            {suggestion.reasoning && (
                              <div className="bg-purple-50 dark:bg-purple-950/30 p-2 rounded text-xs border border-purple-200 dark:border-purple-800">
                                <strong className="text-purple-700 dark:text-purple-300">💡 Why?</strong>{' '}
                                <span className="text-purple-900 dark:text-purple-100">{suggestion.reasoning}</span>
                              </div>
                            )}
                            {!isApplied && (
                              <>
                                <div className="bg-muted/50 p-2 rounded text-xs">
                                  <strong className="text-primary">Suggestion:</strong>{' '}
                                  {suggestion.suggestion}
                                </div>
                                {suggestion.replacement && suggestion.replacement.trim() && (
                                  <div className="bg-blue-50 dark:bg-blue-950 p-2 rounded text-xs border border-blue-200 dark:border-blue-800">
                                    <strong className="text-blue-700 dark:text-blue-300">Replace with:</strong>{' '}
                                    <span className="font-mono">{suggestion.replacement}</span>
                                  </div>
                                )}
                                {suggestion.replacement && suggestion.replacement.trim() && suggestion.highlightRange && (
                                  <DiffPreview 
                                    original={content.substring(suggestion.highlightRange.start, suggestion.highlightRange.end)}
                                    replacement={suggestion.replacement}
                                    className="my-2 p-2 bg-white dark:bg-gray-900 rounded border"
                                  />
                                )}
                              </>
                            )}
                            {!isApplied && (suggestion.severity === 'critical' || suggestion.severity === 'warning' || suggestion.severity === 'info') && (
                              <div className="flex gap-2 mt-2">
                                {suggestion.replacement && suggestion.replacement.trim() && suggestion.highlightRange ? (
                                  <>
                                    <Button 
                                      size="sm" 
                                      variant={suggestion.severity === 'critical' ? 'default' : 'outline'}
                                      className={cn(
                                        "flex-1",
                                        suggestion.severity === 'critical' && "bg-red-600 hover:bg-red-700"
                                      )}
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        handleImprove(suggestion);
                                      }}
                                    >
                                      <CheckIcon className="h-3 w-3 mr-1" />
                                      Accept
                                    </Button>
                                    <Button 
                                      size="sm" 
                                      variant="ghost"
                                      className="flex-1"
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        handleRejectSuggestion(suggestion.id);
                                      }}
                                    >
                                      <XIcon className="h-3 w-3 mr-1" />
                                      Reject
                                    </Button>
                                  </>
                                ) : (
                                  <Button 
                                    size="sm" 
                                    variant="ghost"
                                    className="w-full"
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      handleRejectSuggestion(suggestion.id);
                                    }}
                                  >
                                    <XIcon className="h-3 w-3 mr-1" />
                                    Dismiss
                                  </Button>
                                )}
                              </div>
                            )}
                          </CardContent>
                        </Card>
                        );
                      })}
                    </AccordionContent>
                  </AccordionItem>
                ))}
              </Accordion>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
