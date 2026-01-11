import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/lib/api-client'
import { toast } from 'sonner'
import { useEffect, useState } from 'react'
import { supabase } from '@/lib/supabase'

// Query keys for cache management
export const chatKeys = {
  all: ['chats'] as const,
  lists: () => [...chatKeys.all, 'list'] as const,
  list: () => [...chatKeys.lists()] as const,
  details: () => [...chatKeys.all, 'detail'] as const,
  detail: (id: string) => [...chatKeys.details(), id] as const,
  messages: (chatId: string) => [...chatKeys.detail(chatId), 'messages'] as const,
}

/**
 * Hook to check if user is authenticated
 */
function useIsAuthenticated() {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [isChecking, setIsChecking] = useState(true)

  useEffect(() => {
    // Check current session
    supabase.auth.getSession().then(({ data: { session } }) => {
      setIsAuthenticated(!!session)
      setIsChecking(false)
    })

    // Listen for auth changes
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setIsAuthenticated(!!session)
      setIsChecking(false)
    })

    return () => subscription.unsubscribe()
  }, [])

  return { isAuthenticated, isChecking }
}

/**
 * Fetch all chats for the current user
 */
export function useChats() {
  const { isAuthenticated, isChecking } = useIsAuthenticated()
  
  return useQuery({
    queryKey: chatKeys.list(),
    queryFn: () => apiClient.getChats(),
    enabled: isAuthenticated && !isChecking,
  })
}

/**
 * Fetch a single chat by ID
 */
export function useChat(chatId: string) {
  return useQuery({
    queryKey: chatKeys.detail(chatId),
    queryFn: () => apiClient.getChat(chatId),
    enabled: !!chatId,
  })
}

/**
 * Fetch messages for a specific chat
 */
export function useMessages(chatId: string | undefined) {
  return useQuery({
    queryKey: chatKeys.messages(chatId || 'none'),
    queryFn: () => apiClient.getMessages(chatId!),
    enabled: !!chatId && chatId !== 'undefined',
    // Refetch messages every 30 seconds to catch new messages
    refetchInterval: 30000,
  })
}

/**
 * Create a new chat
 */
export function useCreateChat() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: { title?: string }) => apiClient.createChat(data),
    onSuccess: () => {
      // Invalidate and refetch chats list
      queryClient.invalidateQueries({ queryKey: chatKeys.list() })
      toast.success('Chat created successfully')
    },
    onError: (error: Error) => {
      toast.error(`Failed to create chat: ${error.message}`)
    },
  })
}

/**
 * Delete a chat
 */
export function useDeleteChat() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (chatId: string) => apiClient.deleteChat(chatId),
    onSuccess: (_, chatId) => {
      // Remove from cache
      queryClient.removeQueries({ queryKey: chatKeys.detail(chatId) })
      // Refetch chats list
      queryClient.invalidateQueries({ queryKey: chatKeys.list() })
      toast.success('Chat deleted successfully')
    },
    onError: (error: Error) => {
      toast.error(`Failed to delete chat: ${error.message}`)
    },
  })
}

/**
 * Update a chat (title, emoji, pinned status)
 */
export function useUpdateChat() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ chatId, ...data }: { chatId: string; title?: string; emoji?: string; is_pinned?: boolean }) =>
      apiClient.updateChat(chatId, data),
    onMutate: async ({ chatId, ...updates }) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: chatKeys.list() })
      await queryClient.cancelQueries({ queryKey: chatKeys.detail(chatId) })

      // Snapshot previous values
      const previousChats = queryClient.getQueryData(chatKeys.list())
      const previousChat = queryClient.getQueryData(chatKeys.detail(chatId))

      // Optimistically update
      queryClient.setQueryData(chatKeys.list(), (old: unknown[] = []) =>
        old.map((chat: unknown) => {
          const c = chat as { id: string }
          return c.id === chatId ? { ...c, ...updates } : chat
        })
      )
      queryClient.setQueryData(chatKeys.detail(chatId), (old: unknown) =>
        old ? { ...old, ...updates } : old
      )

      return { previousChats, previousChat }
    },
    onError: (error: Error, variables, context) => {
      // Revert on error
      if (context?.previousChats) {
        queryClient.setQueryData(chatKeys.list(), context.previousChats)
      }
      if (context?.previousChat) {
        queryClient.setQueryData(chatKeys.detail(variables.chatId), context.previousChat)
      }
      toast.error(`Failed to update chat: ${error.message}`)
    },
    onSuccess: (_, variables) => {
      // Invalidate to ensure consistency
      queryClient.invalidateQueries({ queryKey: chatKeys.list() })
      queryClient.invalidateQueries({ queryKey: chatKeys.detail(variables.chatId) })
    },
  })
}

/**
 * Send a message to a chat with optimistic updates
 */
export function useSendMessage() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: { chatId: string; message: string; files?: File[] }) =>
      apiClient.sendMessage(data),
    onMutate: async (variables) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({
        queryKey: chatKeys.messages(variables.chatId),
      })

      // Snapshot the previous value
      const previousMessages = queryClient.getQueryData(
        chatKeys.messages(variables.chatId)
      )

      // Optimistically update to the new value
      const optimisticMessage = {
        id: `temp-${Date.now()}`,
        role: 'user',
        content: variables.message,
        created_at: new Date().toISOString(),
        pending: true,
      }

      queryClient.setQueryData(
        chatKeys.messages(variables.chatId),
        (old: unknown[] = []) => [...old, optimisticMessage]
      )

      // Return a context object with the snapshotted value
      return { previousMessages }
    },
    onError: (error: Error, variables, context) => {
      // Rollback to the previous value on error
      if (context?.previousMessages) {
        queryClient.setQueryData(
          chatKeys.messages(variables.chatId),
          context.previousMessages
        )
      }
      toast.error(`Failed to send message: ${error.message}`)
    },
    onSuccess: (data, variables) => {
      // Invalidate and refetch messages
      queryClient.invalidateQueries({
        queryKey: chatKeys.messages(variables.chatId),
      })
      // Update chats list (to show latest message)
      queryClient.invalidateQueries({ queryKey: chatKeys.list() })
    },
  })
}

/**
 * Rate a message (thumbs up/down)
 */
export function useRateMessage() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      chatId,
      messageId,
      rating,
    }: {
      chatId: string
      messageId: string
      rating: 'thumbs-up' | 'thumbs-down'
    }) =>
      apiClient.post(`/chats/${chatId}/messages/${messageId}/rate`, {
        rating,
      }),
    onSuccess: (_, variables) => {
      // Invalidate messages to refetch with updated rating
      queryClient.invalidateQueries({
        queryKey: chatKeys.messages(variables.chatId),
      })
      toast.success('Thank you for your feedback!')
    },
    onError: (error: Error) => {
      toast.error(`Failed to submit rating: ${error.message}`)
    },
  })
}
