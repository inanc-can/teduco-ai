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
}

export interface ApplicationLetter {
  id: string;
  userId: string;
  programId: string;
  title: string;
  content: string;
  status: 'draft' | 'final';
  wordCount: number;
  suggestions: AISuggestion[];
  createdAt: string;
  updatedAt: string;
}

export interface LetterDraft {
  id: string;
  title: string;
  programName: string;
  lastEdited: string;
  wordCount: number;
}
