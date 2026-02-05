import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import { toast } from 'sonner';
import type { ApplicationLetter } from '@/lib/types/letters';

export interface AnalyzeLetterParams {
  letterId: string;
  content: string;
  programSlug?: string;
  phase?: 'objective' | 'subjective' | 'both';
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

// ============================================================================
// APPLICATION LETTERS CRUD
// ============================================================================

/**
 * Query key factory for letters
 */
export const lettersKeys = {
  all: ['letters'] as const,
  lists: () => [...lettersKeys.all, 'list'] as const,
  list: (limit: number, offset: number) => [...lettersKeys.lists(), { limit, offset }] as const,
  details: () => [...lettersKeys.all, 'detail'] as const,
  detail: (id: string) => [...lettersKeys.details(), id] as const,
}

/**
 * Hook to fetch all letters for current user
 */
export function useLetters(limit = 50, offset = 0) {
  return useQuery({
    queryKey: lettersKeys.list(limit, offset),
    queryFn: () => apiClient.listLetters(limit, offset),
  })
}

/**
 * Hook to fetch a specific letter by ID
 */
export function useLetter(letterId: string | undefined) {
  return useQuery({
    queryKey: lettersKeys.detail(letterId || ''),
    queryFn: () => apiClient.getLetter(letterId!),
    enabled: !!letterId,
  })
}

/**
 * Hook to create a new letter
 */
export function useCreateLetter() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: {
      title: string
      content?: string
      programId?: string | null
      programName?: string | null
      status?: 'draft' | 'final'
      metadata?: Record<string, any>
    }) => apiClient.createLetter(data),
    onSuccess: (newLetter) => {
      // Add the new letter to the lists cache
      queryClient.setQueryData<ApplicationLetter[]>(
        lettersKeys.lists(),
        (old) => (old ? [newLetter, ...old] : [newLetter])
      )
      // Invalidate to refetch all list variations
      queryClient.invalidateQueries({ queryKey: lettersKeys.lists() })
      toast.success('Letter created successfully')
    },
    onError: (error: Error) => {
      toast.error(`Failed to create letter: ${error.message}`)
    },
  })
}

/**
 * Hook to update a letter
 */
export function useUpdateLetter() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      letterId,
      data,
    }: {
      letterId: string
      data: {
        title?: string
        content?: string
        programId?: string | null
        programName?: string | null
        status?: 'draft' | 'final'
        metadata?: Record<string, any>
      }
    }) => apiClient.updateLetter(letterId, data),
    onSuccess: (updatedLetter) => {
      // Update the detail cache
      queryClient.setQueryData(
        lettersKeys.detail(updatedLetter.id),
        updatedLetter
      )
      // Invalidate lists to refetch with new data
      queryClient.invalidateQueries({ queryKey: lettersKeys.lists() })
      toast.success('Letter updated successfully')
    },
    onError: (error: Error) => {
      toast.error(`Failed to update letter: ${error.message}`)
    },
  })
}

/**
 * Hook to auto-save letter content
 */
export function useAutoSaveLetter() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      letterId,
      content,
      rejectedSuggestionIds,
      appliedSuggestionMetadata,
    }: {
      letterId: string;
      content: string;
      rejectedSuggestionIds?: string[];
      appliedSuggestionMetadata?: Array<{ id: string; appliedAt: string; historyEntryId?: string }>;
    }) =>
      apiClient.autoSaveLetter(letterId, content, rejectedSuggestionIds, appliedSuggestionMetadata),
    onSuccess: (updatedLetter) => {
      // Optimistically update the cache
      queryClient.setQueryData(
        lettersKeys.detail(updatedLetter.id),
        updatedLetter
      )
    },
    onError: (error: Error) => {
      toast.error(`Failed to save: ${error.message}`)
    },
  })
}

/**
 * Hook to delete a letter
 */
export function useDeleteLetter() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (letterId: string) => apiClient.deleteLetter(letterId),
    onSuccess: (_, letterId) => {
      // Remove from detail cache
      queryClient.removeQueries({ queryKey: lettersKeys.detail(letterId) })
      // Invalidate lists to refetch without deleted item
      queryClient.invalidateQueries({ queryKey: lettersKeys.lists() })
      toast.success('Letter deleted successfully')
    },
    onError: (error: Error) => {
      toast.error(`Failed to delete letter: ${error.message}`)
    },
  })
}
