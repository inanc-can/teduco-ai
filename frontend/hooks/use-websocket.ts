import { useEffect, useState, useCallback, useRef } from 'react'
import { wsClient, WebSocketMessage, WebSocketStatus } from '@/lib/websocket-client'
import { getCachedSession } from '@/lib/supabase'

export interface UseWebSocketOptions {
  autoConnect?: boolean
  onMessage?: (message: WebSocketMessage) => void
  onStatusChange?: (status: WebSocketStatus) => void
}

export function useWebSocket(options: UseWebSocketOptions = {}) {
  const { autoConnect = true, onMessage, onStatusChange } = options
  
  const [status, setStatus] = useState<WebSocketStatus>(() => wsClient.getStatus())
  const [messages, setMessages] = useState<WebSocketMessage[]>([])
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null)
  const onMessageRef = useRef(onMessage)
  const onStatusChangeRef = useRef(onStatusChange)

  // Keep refs updated
  useEffect(() => {
    onMessageRef.current = onMessage
    onStatusChangeRef.current = onStatusChange
  }, [onMessage, onStatusChange])

  // Connect to WebSocket
  const connect = useCallback(async () => {
    const session = await getCachedSession()
    const token = session?.access_token
    await wsClient.connect(token)
  }, [])

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    wsClient.disconnect()
  }, [])

  // Send a message
  const sendMessage = useCallback((message: Omit<WebSocketMessage, 'type'> & { type?: WebSocketMessage['type'] }) => {
    wsClient.send({
      type: 'message',
      ...message,
    })
  }, [])

  // Subscribe to messages and status
  useEffect(() => {
    const unsubscribeMessages = wsClient.onMessage((message) => {
      setMessages((prev) => [...prev, message])
      setLastMessage(message)
      onMessageRef.current?.(message)
    })

    const unsubscribeStatus = wsClient.onStatusChange((newStatus) => {
      setStatus(newStatus)
      onStatusChangeRef.current?.(newStatus)
    })

    return () => {
      unsubscribeMessages()
      unsubscribeStatus()
    }
  }, [])

  // Auto-connect on mount
  // Disabled until backend WebSocket endpoint is implemented
  useEffect(() => {
    // if (autoConnect) {
    //   connect()
    // }

    // return () => {
    //   if (autoConnect) {
    //     disconnect()
    //   }
    // }
  }, [autoConnect, connect, disconnect])

  return {
    // State
    status,
    isConnected: status === 'connected',
    messages,
    lastMessage,

    // Actions
    connect,
    disconnect,
    sendMessage,

    // Helpers
    clearMessages: () => setMessages([]),
  }
}

/**
 * Hook for streaming chat messages
 */
export function useChatStream(chatId: string | undefined) {
  const [streamingMessage, setStreamingMessage] = useState<string>('')
  const [isStreaming, setIsStreaming] = useState(false)
  const streamingMessageId = useRef<string | null>(null)

  const handleMessage = useCallback(
    (message: WebSocketMessage) => {
      // Only handle messages for this chat
      if (!chatId || message.chatId !== chatId) {
        return
      }

      switch (message.type) {
        case 'stream_start':
          setIsStreaming(true)
          setStreamingMessage('')
          streamingMessageId.current = message.messageId || null
          break

        case 'stream_chunk':
          setStreamingMessage((prev) => prev + (message.data || ''))
          break

        case 'stream_end':
          setIsStreaming(false)
          streamingMessageId.current = null
          break

        case 'error':
          setIsStreaming(false)
          streamingMessageId.current = null
          console.error('Stream error:', message.error)
          break
      }
    },
    [chatId]
  )

  const { sendMessage, ...websocket } = useWebSocket({
    autoConnect: true,
    onMessage: handleMessage,
  })

  const sendChatMessage = useCallback(
    (content: string, files?: File[]) => {
      if (!chatId) return
      
      sendMessage({
        type: 'message',
        chatId,
        data: {
          content,
          files: files?.map((f) => f.name),
        },
      })
    },
    [chatId, sendMessage]
  )

  return {
    ...websocket,
    streamingMessage,
    isStreaming,
    streamingMessageId: streamingMessageId.current,
    sendChatMessage,
    clearStreamingMessage: () => setStreamingMessage(''),
  }
}
