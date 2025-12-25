"use client"

import { useState, useCallback, useEffect } from "react"
import { useSearchParams } from "next/navigation"
import { supabase, getCachedSession } from "@/lib/supabase"
import { toast } from "sonner"

import { cn } from "@/lib/utils"
import { Chat } from "@/components/ui/chat"

type Message = {
  id: string
  role: 'user' | 'assistant'
  content: string
}

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'


// Mock transcribeAudio function
const transcribeAudio = async (audioBlob: Blob): Promise<string> => {
  // Mock implementation: return a fixed string
  console.log('Mock transcribing audio blob:', audioBlob)
  return "Transcribed audio: Hello, this is a mock transcription."
}

// Custom useChat hook with database integration
function useChatWithDB({ chatId }: { chatId?: string }) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [status, setStatus] = useState<'ready' | 'submitted' | 'streaming'>('ready')
  const [isLoading, setIsLoading] = useState(false)
  const [currentChatId, setCurrentChatId] = useState<string | undefined>(chatId)

  // Load messages when chatId changes
  useEffect(() => {
    if (!chatId) {
      setIsLoading(false)
      setMessages([])
      setCurrentChatId(undefined)
      return
    }

    setIsLoading(true)
    setCurrentChatId(chatId)

    const loadMessages = async () => {
      try {
        const session = await getCachedSession()
        
        if (!session) {
          console.error("No session found")
          setIsLoading(false)
          return
        }

        const response = await fetch(`${BACKEND_URL}/chats/${chatId}/messages`, {
          headers: {
            "Authorization": `Bearer ${session.access_token}`,
          },
        })

        if (response.ok) {
          const data = await response.json()
          setMessages(data.map((msg: Message) => ({
            id: msg.id,
            role: msg.role,
            content: msg.content
          })))
        } else {
          console.error("Failed to load messages:", response.status)
          toast.error("Failed to load messages")
        }
      } catch (error) {
        console.error("Error loading messages:", error)
        toast.error("Failed to load messages")
      } finally {
        setIsLoading(false)
      }
    }

    loadMessages()
  }, [chatId])

  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value)
  }, [])

  const handleSubmit = useCallback(async (event?: { preventDefault?: () => void }) => {
    if (event?.preventDefault) event.preventDefault()
    if (!input.trim()) return

    const userMessageContent = input.trim()
    setInput("")
    setStatus('submitted')

    // Optimistically add user message to UI
    const tempUserMessage: Message = {
      id: `temp-${Date.now()}`,
      role: 'user',
      content: userMessageContent
    }
    setMessages(prev => [...prev, tempUserMessage])

    try {
      const session = await getCachedSession()
      
      if (!session) {
        toast.error("Please log in")
        setStatus('ready')
        return
      }

      setStatus('streaming')

      // If no chat exists yet, create one first
      let activeChatId = currentChatId
      if (!activeChatId) {
        const createResponse = await fetch(`${BACKEND_URL}/chats`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${session.access_token}`,
          },
          body: JSON.stringify({
            title: "New Chat",
            emoji: "💬"
          }),
        })

        if (createResponse.ok) {
          const newChat = await createResponse.json()
          activeChatId = newChat.id
          setCurrentChatId(activeChatId)
          // Update URL without reload
          window.history.replaceState(null, '', `/auth/dashboard?chat=${activeChatId}`)
        } else {
          toast.error("Failed to create chat")
          setMessages(prev => prev.filter(m => m.id !== tempUserMessage.id))
          setStatus('ready')
          return
        }
      }

      const response = await fetch(`${BACKEND_URL}/chats/${activeChatId}/messages`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({
          content: userMessageContent
        }),
      })

      if (response.ok) {
        const data = await response.json()
        
        // Replace temp message with real one and add AI response
        setMessages(prev => {
          const withoutTemp = prev.filter(m => m.id !== tempUserMessage.id)
          const newMessages: Message[] = [
            ...withoutTemp,
            {
              id: data.user_message.id,
              role: 'user',
              content: data.user_message.content
            }
          ]
          
          if (data.assistant_message) {
            newMessages.push({
              id: data.assistant_message.id,
              role: 'assistant',
              content: data.assistant_message.content
            })
          }
          
          return newMessages
        })
      } else {
        toast.error("Failed to send message")
        // Remove temp message on error
        setMessages(prev => prev.filter(m => m.id !== tempUserMessage.id))
      }
    } catch (error) {
      console.error("Error sending message:", error)
      toast.error("Failed to send message")
      setMessages(prev => prev.filter(m => m.id !== tempUserMessage.id))
    } finally {
      setStatus('ready')
    }
  }, [input, currentChatId])

  const append = useCallback((message: { role: "user"; content: string; }) => {
    const fullMessage: Message = {
      id: Date.now().toString(),
      ...message
    }
    setMessages(prev => [...prev, fullMessage])
  }, [])

  const stop = useCallback(() => {
    setStatus('ready')
  }, [])

  return {
    messages,
    input,
    handleInputChange,
    handleSubmit,
    append,
    stop,
    status,
    isLoading,
    setMessages,
  }
}

export default function DashboardPage() {
  const searchParams = useSearchParams()
  const chatId = searchParams.get('chat')

  const {
    messages,
    input,
    handleInputChange,
    handleSubmit,
    append,
    stop,
    status,
    isLoading,
    setMessages,
  } = useChatWithDB({ chatId: chatId || undefined })

  const [userName, setUserName] = useState<string | null>(null)

  useEffect(() => {
    async function loadUserName() {
      try {
        const { data: { user: authUser } } = await supabase.auth.getUser()
        if (authUser) {
          const { data: profile } = await supabase
            .from('users')
            .select('first_name')
            .eq('user_id', authUser.id)
            .single()
          
          if (profile?.first_name) {
            setUserName(profile.first_name)
          }
        }
      } catch (error) {
        console.error('Error loading user name:', error)
      }
    }
    loadUserName()
  }, [])

  const isEmpty = messages.length === 0

  if (isLoading && chatId) {
    return (
      <div className="relative flex flex-col h-screen w-full overflow-hidden">
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-current border-r-transparent align-[-0.125em] motion-reduce:animate-[spin_1.5s_linear_infinite]" />
          </div>
        </div>
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
          messages={messages}
          handleSubmit={handleSubmit}
          input={input}
          handleInputChange={handleInputChange}
          isGenerating={status === 'submitted' || status === 'streaming'}
          stop={stop}
          append={append}
          setMessages={setMessages}
          transcribeAudio={transcribeAudio}
          suggestions={[
            "How can I apply to TUM?",
            "What are the admission requirements?",
            "Tell me about scholarship opportunities.",
            "Help me with my statement of purpose.",
          ]}
          welcomeMessage={userName ? `Teduco'ya Hoşgeldin ${userName}` : "Teduco'ya Hoşgeldin İnanç"}
        />
      </div>
    </div>
  )
}
