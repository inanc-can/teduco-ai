'use client';

import { useState, useRef } from 'react';
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
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useLetterAnalysis } from '@/hooks/use-letter-analysis';
import { MOCK_PROGRAMS } from '@/lib/mocks/letter-suggestions';
import type { AISuggestion } from '@/lib/types/letters';

const SAMPLE_LETTER = `Dear Admissions Committee,

I am writing to express my interest in the Informatics Bachelor program at Technical University of Munich. I am very passionate about computer science and believe that TUM would be an excellent fit for my academic goals.

Throughout my high school education, I have consistently excelled in mathematics and science courses. I think I would be a good fit for this program because of my strong analytical skills and dedication to learning.

I have completed several online programming courses and worked on a few personal projects. I am eager to expand my knowledge and contribute to the field of computer science.

Thank you for considering my application.`;

export default function LetterEditorPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  // Future: use id from params to load specific letter
  use(params);
  const [content, setContent] = useState(SAMPLE_LETTER);
  const [selectedProgram, setSelectedProgram] = useState<string>(MOCK_PROGRAMS[0].id);
  const [highlightedSuggestionId, setHighlightedSuggestionId] = useState<string | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const highlightLayerRef = useRef<HTMLDivElement>(null);

  // History management for undo/redo
  const [history, setHistory] = useState<string[]>([SAMPLE_LETTER]);
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

  const {
    suggestions: rawSuggestions,
    autoSaveStatus,
    analysisStatus,
    isAnalyzing,
    wordCount,
    triggerAnalysis,
  } = useLetterAnalysis({
    content,
    programSlug,
    debounceMs: 2500,
    useMockData: false, // Use real API for AI analysis
  });

  // Debug: Log suggestions when they change
  console.log('[LetterEditor] Suggestions updated:', {
    count: rawSuggestions.length,
    suggestions: rawSuggestions,
    status: analysisStatus
  });

  // Filter out applied suggestions
  const suggestions = rawSuggestions.filter(s => !appliedSuggestionIds.has(s.id));

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

  // Apply single improvement
  const handleImprove = (suggestion: AISuggestion) => {
    if (!suggestion.highlightRange) {
      console.error('[handleImprove] No highlight range provided:', suggestion);
      return;
    }

    const { start, end } = suggestion.highlightRange;
    
    // Validate positions
    if (start < 0 || end > content.length || start >= end) {
      console.error('[handleImprove] Invalid highlight range:', { start, end, contentLength: content.length });
      alert('Cannot apply improvement: The text has changed since this suggestion was generated. Please wait for new analysis.');
      return;
    }
    
    const before = content.substring(0, start);
    const after = content.substring(end);
    const original = content.substring(start, end);
    
    console.log('[handleImprove] Applying improvement:', {
      original,
      replacement: suggestion.replacement,
      start,
      end,
      suggestionId: suggestion.id,
      currentContentLength: content.length
    });
    
    // Use the replacement text provided by AI
    // If no replacement is provided, keep the original text (for informational suggestions)
    const replacement = suggestion.replacement ?? original;
    
    const newContent = before + replacement + after;
    updateContent(newContent);
    
    // Mark this suggestion as applied so it can be filtered out
    setAppliedSuggestionIds(prev => new Set([...prev, suggestion.id]));
    
    // IMPORTANT: Clear all suggestions after applying one improvement
    // because the text positions of other suggestions are now invalid
    // The debounce will trigger a new analysis with updated positions
    console.log('[handleImprove] Content modified - new analysis will be triggered in 2.5s');
  };

  // Apply all improvements
  const handleImproveAll = () => {
    console.log('[handleImproveAll] Starting batch improvements');
    
    // Sort suggestions by start position (descending) to avoid index shifting
    const sortedSuggestions = [...suggestions]
      .filter(s => {
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
      })
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
      
      console.log('[handleImproveAll] Applying:', {
        id: suggestion.id,
        original,
        replacement: suggestion.replacement
      });
      
      // Use the replacement text provided by AI
      const replacement = suggestion.replacement;
      
      newContent = before + replacement + after;
      appliedIds.add(suggestion.id);
    }
    
    console.log('[handleImproveAll] Applied', appliedIds.size, 'improvements');
    
    updateContent(newContent);
    setAppliedSuggestionIds(prev => new Set([...prev, ...appliedIds]));
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

  return (
    <div className="flex h-screen">
      {/* Left Column - Editor */}
      <div className="flex-1 flex flex-col border-r">
        {/* Header */}
        <div className="border-b p-4 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-semibold">Application Letter</h1>
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
                        'relative',
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

            {/* Textarea */}
            <Textarea
              ref={textareaRef}
              value={content}
              onChange={(e) => updateContent(e.target.value)}
              onScroll={handleScroll}
              placeholder="Start writing your application letter here..."
              className="h-full resize-none bg-transparent relative z-10 font-mono text-sm leading-relaxed"
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
            {suggestions.length > 0 && (
              <Button 
                size="sm" 
                variant="outline"
                onClick={handleImproveAll}
              >
                Improve All
              </Button>
            )}
          </div>
          <p className="text-xs text-muted-foreground">
            {suggestions.length > 0
              ? `${suggestions.length} suggestion${suggestions.length !== 1 ? 's' : ''} found`
              : 'Type to get suggestions'}
          </p>
        </div>

        <div className="flex-1 overflow-y-auto">
          <div className="p-4">
            {suggestions.length === 0 ? (
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
                  ) : analysisStatus === 'error' ? (
                    <>
                      <AlertCircleIcon className="h-8 w-8 mx-auto mb-2 text-destructive opacity-50" />
                      <p className="font-medium text-destructive mb-2">AI connection seems to not work</p>
                      <p className="text-xs mb-3">Unable to analyze your letter. Please check your connection or try again.</p>
                      <Button 
                        size="sm" 
                        variant="outline"
                        onClick={() => triggerAnalysis()}
                      >
                        Retry Analysis
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
                      {categorySuggestions.map((suggestion) => (
                        <Card
                          key={suggestion.id}
                          className={cn(
                            'cursor-pointer transition-colors hover:border-primary/50',
                            highlightedSuggestionId === suggestion.id && 'border-primary'
                          )}
                          onClick={() => handleSuggestionClick(suggestion)}
                        >
                          <CardHeader className="p-3 pb-2">
                            <div className="flex items-start gap-2">
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
                              <CardTitle className="text-sm font-medium flex-1">
                                {suggestion.title}
                              </CardTitle>
                            </div>
                          </CardHeader>
                          <CardContent className="p-3 pt-0 space-y-2">
                            <p className="text-xs text-muted-foreground">
                              {suggestion.description}
                            </p>
                            <div className="bg-muted/50 p-2 rounded text-xs">
                              <strong className="text-primary">Suggestion:</strong>{' '}
                              {suggestion.suggestion}
                            </div>
                            {suggestion.replacement && (
                              <div className="bg-blue-50 dark:bg-blue-950 p-2 rounded text-xs border border-blue-200 dark:border-blue-800">
                                <strong className="text-blue-700 dark:text-blue-300">Replace with:</strong>{' '}
                                <span className="font-mono">{suggestion.replacement}</span>
                              </div>
                            )}
                            {(suggestion.severity === 'critical' || suggestion.severity === 'warning' || suggestion.severity === 'info') && (
                              <Button 
                                size="sm" 
                                variant={suggestion.severity === 'critical' ? 'destructive' : 'outline'}
                                className="w-full mt-2"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleImprove(suggestion);
                                }}
                                disabled={!suggestion.replacement}
                              >
                                {suggestion.replacement ? (suggestion.severity === 'critical' ? 'Fix Critical Issue' : 'Improve') : 'No fix available'}
                              </Button>
                            )}
                          </CardContent>
                        </Card>
                      ))}
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
