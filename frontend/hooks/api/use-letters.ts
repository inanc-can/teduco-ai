import { useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import { toast } from 'sonner';

export interface AnalyzeLetterParams {
  content: string;
  programSlug?: string;
}

export interface AnalyzeLetterResponse {
  suggestions: Array<{
    id: string;
    category: string;
    severity: string;
    title: string;
    description: string;
    suggestion: string;
    replacement?: string;
    highlightRange?: { start: number; end: number };
  }>;
  wordCount: number;
  analysisMetadata?: Record<string, unknown>;
}

export function useAnalyzeLetter() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (params: AnalyzeLetterParams) =>
      apiClient.analyzeApplicationLetter(params),
    onSuccess: (data) => {
      // Cache the analysis result
      queryClient.setQueryData(['letter-analysis'], data);
    },
    onError: (error: Error) => {
      toast.error(`Analysis failed: ${error.message}`);
    },
  });
}
