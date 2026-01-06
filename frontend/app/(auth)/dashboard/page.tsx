"use client"

import { useState, useCallback } from "react"
import { useSearchParams, useRouter } from "next/navigation"
import { toast } from "sonner"

import { Chat } from "@/components/ui/chat"
import { useMessages, useSendMessage, useCreateChat } from "@/hooks/api/use-chat"
import { useChatStream } from "@/hooks/use-websocket"
import { useUserProfile } from "@/hooks/api/use-user"
import { logger } from "@/lib/logger"
import { Skeleton } from "@/components/ui/skeleton"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { cn } from "@/lib/utils"

type Message = {
  id: string
  role: 'user' | 'assistant'
  content: string
  pending?: boolean
}

// Mock transcribeAudio function
const transcribeAudio = async (audioBlob: Blob): Promise<string> => {
  logger.logAction('transcribe_audio', { size: audioBlob.size })
  console.log('Mock transcribing audio blob:', audioBlob)
  return "Transcribed audio: Hello, this is a mock transcription."
}

export default function DashboardPage() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const chatId = searchParams.get('chat') || undefined
  
  const [input, setInput] = useState("")

  // Fetch user profile using React Query
  const { data: userProfile } = useUserProfile()
  
  // Fetch messages using React Query
  const { 
    data: messages = [], 
    isLoading, 
    error,
    refetch 
  } = useMessages(chatId)

  // Mutations
  const sendMessage = useSendMessage()
  const createChat = useCreateChat()

  // WebSocket for real-time streaming
  const {
    streamingMessage,
    isStreaming,
    sendChatMessage,
    isConnected: wsConnected,
  } = useChatStream(chatId)

  // Extract user name from profile
  const userName = userProfile?.firstName || null

  // Transform API messages to display format (filter out system messages)
  const transformedMessages: Message[] = messages
    .filter(msg => msg.role !== 'system')
    .map(msg => ({
      id: msg.messageId,
      role: msg.role as 'user' | 'assistant',
      content: msg.content,
    }))

  // Combine database messages with streaming message
  const displayMessages: Message[] = [
    ...transformedMessages,
    ...(isStreaming && streamingMessage
      ? [{
          id: 'streaming-message',
          role: 'assistant' as const,
          content: streamingMessage,
          pending: true,
        }]
      : []),
  ]

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      setInput(e.target.value)
    },
    []
  )

  const handleSubmit = useCallback(
    async (
      event?: { preventDefault?: () => void },
      options?: { experimental_attachments?: FileList }
    ) => {
      if (event?.preventDefault) event.preventDefault()
      if (!input.trim()) return

      const messageContent = input.trim()
      const files = options?.experimental_attachments
        ? Array.from(options.experimental_attachments)
        : undefined

      logger.logAction('send_message', { 
        chatId, 
        hasFiles: !!files?.length,
        fileCount: files?.length 
      })

      setInput("")

      // If no chat exists, create one first
      if (!chatId) {
        createChat.mutate(
          { title: 'New Chat' },
          {
            onSuccess: (newChat) => {
              // Update URL with new chat ID
              router.push(`/dashboard?chat=${newChat.chatId}`)
              
              // Send the message to the new chat
              setTimeout(() => {
                sendMessage.mutate(
                  { chatId: newChat.chatId, message: messageContent, files },
                  {
                    onSuccess: () => {
                      if (wsConnected) {
                        sendChatMessage(messageContent, files)
                      }
                    }
                  }
                )
              }, 100)
            },
            onError: (error) => {
              logger.error('Failed to create chat', error as Error)
            }
          }
        )
        return
      }

      // Send message to existing chat
      sendMessage.mutate(
        { chatId, message: messageContent, files },
        {
          onSuccess: () => {
            // Also send through WebSocket for real-time streaming
            if (wsConnected) {
              sendChatMessage(messageContent, files)
            }
          },
          onError: (error) => {
            logger.error('Failed to send message', error as Error, { chatId })
          },
        }
      )
    },
    [input, chatId, sendMessage, createChat, sendChatMessage, wsConnected, router]
  )

  const stop = useCallback(() => {
    logger.logAction('stop_generation', { chatId })
    toast.info("Stop generation not yet implemented")
  }, [chatId])

  const append = useCallback((message: { role: "user"; content: string }) => {
    logger.logAction('append_message', { role: message.role })

    const messageContent = message.content?.trim()
    if (!messageContent) return

    // If no chat exists, create one first and then send the message
    if (!chatId) {
      createChat.mutate(
        { title: 'New Chat' },
        {
          onSuccess: (newChat) => {
            router.push(`/dashboard?chat=${newChat.chatId}`)

            // Send the message to the newly created chat shortly after navigation
            setTimeout(() => {
              sendMessage.mutate(
                { chatId: newChat.chatId, message: messageContent },
                {
                  onSuccess: () => {
                    if (wsConnected) {
                      sendChatMessage(messageContent)
                    }
                  },
                  onError: (error) => {
                    logger.error('Failed to send appended message', error as Error)
                  }
                }
              )
            }, 100)
          },
          onError: (error) => {
            logger.error('Failed to create chat (append)', error as Error)
          }
        }
      )
      return
    }

    // Send message to existing chat
    sendMessage.mutate(
      { chatId, message: messageContent },
      {
        onSuccess: () => {
          if (wsConnected) {
            sendChatMessage(messageContent)
          }
        },
        onError: (error) => {
          logger.error('Failed to send appended message', error as Error, { chatId })
        }
      }
    )
  }, [chatId, createChat, router, sendMessage, sendChatMessage, wsConnected])

  const isEmpty = displayMessages.length === 0

  // Loading state
  if (isLoading && chatId) {
    return (
      <div className="flex flex-col h-screen w-full items-center justify-center p-4">
        <div className="w-full max-w-2xl space-y-4">
          <Skeleton className="h-20 w-full" />
          <Skeleton className="h-20 w-3/4" />
          <Skeleton className="h-20 w-full" />
          <Skeleton className="h-20 w-2/3" />
        </div>
      </div>
    )
  }

  // Error state
  if (error && chatId) {
    return (
      <div className="flex flex-col h-screen w-full items-center justify-center p-4">
        <Alert variant="destructive" className="max-w-2xl">
          <AlertDescription>
            Failed to load messages: {error.message}
            <button
              onClick={() => refetch()}
              className="ml-2 underline hover:no-underline"
            >
              Retry
            </button>
          </AlertDescription>
        </Alert>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-screen w-full overflow-hidden">
      {/* Chat area with animation */}
      <div 
        className={cn(
          "flex-1 w-full max-w-3xl mx-auto min-h-0 flex items-center justify-center transition-all duration-500 ease-out"
        )}
      >
        <Chat
          className={cn(
            "w-full h-full transition-all duration-500 ease-out",
            isEmpty && "max-h-[600px]"
          )}
          messages={displayMessages}
          handleSubmit={handleSubmit}
          input={input}
          handleInputChange={handleInputChange}
          isGenerating={sendMessage.isPending || isStreaming || createChat.isPending}
          stop={stop}
          append={append}
          setMessages={() => {}} // Handled by React Query
          transcribeAudio={transcribeAudio}
          suggestions={[
            "How can I apply to TUM?",
            "What are the admission requirements?",
            "Tell me about scholarship opportunities.",
            "Help me with my statement of purpose.",
          ]}
          welcomeMessage={userName ? `Teduco'ya Hoşgeldin ${userName}` : "Teduco'ya Hoşgeldin"}
        />
      </div>
      
      {/* WebSocket connection indicator */}
      {!wsConnected && chatId && (
        <div className="fixed bottom-4 right-4 bg-yellow-500/10 border border-yellow-500/20 rounded-lg px-4 py-2 text-sm">
          Reconnecting to real-time updates...
        </div>
      )}
    </div>
  )
}
