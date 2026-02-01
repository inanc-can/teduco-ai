export interface Program {
  id: string;
  name: string;
  slug: string;
  university: string;
  level: 'bachelor' | 'master' | 'phd';
}

export interface HighlightRange {
  start: number;
  end: number;
}

export interface AISuggestion {
  id: string;
  category: 'critical' | 'grammar' | 'tone' | 'structure' | 'program-alignment' | 'qualifications' | 'motivation';
  severity: 'critical' | 'warning' | 'info' | 'success';
  title: string;
  description: string;
  suggestion: string;
  replacement?: string;
  highlightRange?: HighlightRange;
  confidence?: number; // 0.0-1.0
  contextBefore?: string; // 20 chars before for position recovery
  contextAfter?: string; // 20 chars after for position recovery
  originalText?: string; // The original text that was analyzed by AI
  reasoning?: string; // Educational explanation of WHY this change improves writing
}

export interface ApplicationLetter {
  id: string;
  userId: string;
  programId?: string | null;
  programName?: string | null;
  title: string;
  content: string;
  status: 'draft' | 'final';
  wordCount: number;
  metadata: Record<string, any>;
  createdAt: string;
  updatedAt: string;
  rejectedSuggestionIds?: string[];
  appliedSuggestionMetadata?: Array<{
    id: string;
    appliedAt: string;
    historyEntryId?: string;
  }>;
}

export interface ApplicationLetterWithSuggestions extends ApplicationLetter {
  suggestions: AISuggestion[];
  overallFeedback?: string;
}

export interface LetterDraft {
  id: string;
  title: string;
  programName: string;
  lastEdited: string;
  wordCount: number;
}
