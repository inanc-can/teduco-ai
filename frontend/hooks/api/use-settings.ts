import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/lib/api-client'
import { toast } from 'sonner'
import { config } from '@/lib/config'
import type { Settings, SettingsUpdate } from '@/lib/types/api'

// Query keys
export const settingsKeys = {
  all: ['settings'] as const,
  detail: () => [...settingsKeys.all, 'detail'] as const,
}

/**
 * Fetch user settings
 */
export function useSettings() {
  return useQuery<Settings>({
    queryKey: settingsKeys.detail(),
    queryFn: () => apiClient.getSettings(),
    staleTime: config.cache.userProfile.staleTime,
    gcTime: config.cache.userProfile.gcTime,
  })
}

/**
 * Update user settings with optimistic updates
 */
export function useUpdateSettings() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: SettingsUpdate) => apiClient.updateSettings(data),
    onMutate: async (newSettings) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: settingsKeys.detail() })

      // Snapshot previous value
      const previousSettings = queryClient.getQueryData<Settings>(settingsKeys.detail())

      // Optimistically update settings
      queryClient.setQueryData<Settings>(settingsKeys.detail(), (old) => ({
        ...old!,
        ...newSettings,
      }))

      return { previousSettings }
    },
    onError: (error: Error, _, context) => {
      // Rollback on error
      if (context?.previousSettings) {
        queryClient.setQueryData(settingsKeys.detail(), context.previousSettings)
      }
      toast.error(`Failed to update settings: ${error.message}`)
    },
    onSuccess: () => {
      toast.success('Settings updated successfully')
      // Refetch to ensure we have the latest from server
      queryClient.invalidateQueries({ queryKey: settingsKeys.detail() })
    },
  })
}
