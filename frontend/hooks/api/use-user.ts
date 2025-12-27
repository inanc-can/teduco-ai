import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/lib/api-client'
import { toast } from 'sonner'
import type { UserProfile, UserProfileUpdate } from '@/lib/types/api'
import type { OnboardingFormValues } from '@/lib/schemas/onboarding'

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
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: UserProfileUpdate) => apiClient.updateUserProfile(data),
    onMutate: async (newProfile) => {
      await queryClient.cancelQueries({ queryKey: userKeys.profile() })

      const previousProfile = queryClient.getQueryData<UserProfile>(userKeys.profile())

      queryClient.setQueryData<UserProfile>(userKeys.profile(), (old) => ({
        ...old!,
        ...newProfile,
      }))

      return { previousProfile }
    },
    onError: (error: Error, _, context) => {
      if (context?.previousProfile) {
        queryClient.setQueryData(userKeys.profile(), context.previousProfile)
      }
      toast.error(`Failed to update profile: ${error.message}`)
    },
    onSuccess: () => {
      toast.success('Profile updated successfully')
      queryClient.invalidateQueries({ queryKey: userKeys.profile() })
    },
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
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: OnboardingFormValues) => apiClient.completeOnboarding(data),
    onSuccess: () => {
      toast.success('Onboarding completed!')
      // Invalidate both onboarding status and user profile
      queryClient.invalidateQueries({ queryKey: userKeys.onboarding() })
      queryClient.invalidateQueries({ queryKey: userKeys.profile() })
    },
    onError: (error: Error) => {
      toast.error(`Failed to complete onboarding: ${error.message}`)
    },
  })
}
