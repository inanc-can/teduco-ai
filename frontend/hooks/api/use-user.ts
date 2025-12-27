import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/lib/api-client'
import { toast } from 'sonner'
import type { UserProfile, UserProfileUpdate } from '@/lib/types/api'
import type { OnboardingFormValues } from '@/lib/schemas/onboarding'
import { useOptimisticMutation } from './use-optimistic-mutation'

// Query keys
export const userKeys = {
  all: ['user'] as const,
  profile: () => [...userKeys.all, 'profile'] as const,
  onboarding: () => [...userKeys.all, 'onboarding'] as const,
}

/**
 * Fetch user profile
 */
export function useUserProfile() {
  return useQuery<UserProfile>({
    queryKey: userKeys.profile(),
    queryFn: () => apiClient.getUserProfile(),
  })
}

/**
 * Update user profile
 */
export function useUpdateUserProfile() {
  return useOptimisticMutation<UserProfile, UserProfileUpdate>({
    queryKey: userKeys.profile(),
    mutationFn: (data) => apiClient.updateUserProfile(data),
    successMessage: 'Profile updated successfully',
    errorMessage: 'Failed to update profile',
  })
}

/**
 * Fetch onboarding status
 */
export function useOnboardingStatus() {
  return useQuery({
    queryKey: userKeys.onboarding(),
    queryFn: () => apiClient.getOnboardingStatus(),
  })
}

/**
 * Complete onboarding
 */
export function useCompleteOnboarding() {
  return useOptimisticMutation<UserProfile, OnboardingFormValues>({
    queryKey: userKeys.onboarding(),
    mutationFn: (data) => apiClient.completeOnboarding(data),
    successMessage: 'Onboarding completed!',
    errorMessage: 'Failed to complete onboarding',
  })
}
