import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/lib/api-client'
import type { Settings, SettingsUpdate } from '@/lib/types/api'
import { useOptimisticMutation } from './use-optimistic-mutation'

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
  })
}

/**
 * Update user settings with optimistic updates
 */
export function useUpdateSettings() {
  return useOptimisticMutation<Settings, SettingsUpdate>({
    queryKey: settingsKeys.detail(),
    mutationFn: (data) => apiClient.updateSettings(data),
    successMessage: 'Settings updated successfully',
    errorMessage: 'Failed to update settings',
  })
}
