import { useMutation, useQueryClient, QueryKey } from '@tanstack/react-query'
import { toast } from 'sonner'

interface OptimisticMutationOptions<TData, TVariables> {
  queryKey: QueryKey
  mutationFn: (variables: TVariables) => Promise<TData>
  successMessage?: string
  errorMessage?: string
}

/**
 * Reusable hook for mutations with optimistic updates
 * Handles common patterns: cancel queries, snapshot, optimistic update, rollback on error
 */
export function useOptimisticMutation<TData, TVariables>({
  queryKey,
  mutationFn,
  successMessage,
  errorMessage = 'Operation failed',
}: OptimisticMutationOptions<TData, TVariables>) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn,
    onMutate: async (newData) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey })

      // Snapshot previous value
      const previousData = queryClient.getQueryData<TData>(queryKey)

      // Optimistically update only if we have existing data
      if (previousData) {
        queryClient.setQueryData<TData>(queryKey, (old) => 
          old ? { ...old, ...newData } : old
        )
      }

      return { previousData }
    },
    onError: (error: Error, _, context) => {
      // Rollback on error
      if (context?.previousData) {
        queryClient.setQueryData(queryKey, context.previousData)
      }
      toast.error(`${errorMessage}: ${error.message}`)
    },
    onSuccess: () => {
      if (successMessage) {
        toast.success(successMessage)
      }
      // Refetch to ensure we have the latest from server
      queryClient.invalidateQueries({ queryKey })
    },
  })
}
