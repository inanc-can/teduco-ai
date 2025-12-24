"use client"

import { useState, useCallback, useEffect } from "react"
import { supabase } from "@/lib/supabase"

import { cn } from "@/lib/utils"
import { Chat } from "@/components/ui/chat"

type Message = {
  id: string
  role: 'user' | 'assistant'
  content: string
}

type ChatDemoProps = {
  initialMessages?: Message[]
}

// Mock transcribeAudio function
const transcribeAudio = async (audioBlob: Blob): Promise<string> => {
  // Mock implementation: return a fixed string
  console.log('Mock transcribing audio blob:', audioBlob)
  return "Transcribed audio: Hello, this is a mock transcription."
}

// Mock useChat hook
function useChat({ initialMessages = [] }: { initialMessages?: Message[] }) {
  const [messages, setMessages] = useState<Message[]>(initialMessages)
  const [input, setInput] = useState("")
  const [status, setStatus] = useState<'ready' | 'submitted' | 'streaming'>('ready')

  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value)
  }, [])

  const handleSubmit = useCallback((event?: { preventDefault?: () => void }, _options?: { experimental_attachments?: FileList }) => {
    if (event?.preventDefault) event.preventDefault()
    if (!input.trim()) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim()
    }
    setMessages(prev => [...prev, userMessage])
    setInput("")
    setStatus('submitted')

    // Simulate AI response
    setTimeout(() => {
      setStatus('streaming')
      setTimeout(() => {
        const aiMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: `Mock response to: "${userMessage.content}"`
        }
        setMessages(prev => [...prev, aiMessage])
        setStatus('ready')
      }, 1000) // Simulate streaming delay
    }, 500) // Simulate submission delay
  }, [input])

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
    setMessages,
  }
}

export default function Page(props: ChatDemoProps) {
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

  const {
    messages,
    input,
    handleInputChange,
    handleSubmit,
    append,
    stop,
    status,
    setMessages,
  } = useChat({
    initialMessages: props.initialMessages,
  })

  const isLoading = status === "submitted" || status === "streaming"
  const isEmpty = messages.length === 0

  return (
    <div className="relative flex flex-col h-screen w-full overflow-hidden">
      {/* Model selector in top right 
      
      <div className="absolute top-4 right-6 z-10">
        <Select value={selectedModel} onValueChange={setSelectedModel}>
          <SelectTrigger className="w-[160px] bg-background/80 backdrop-blur-sm border-muted-foreground/20 text-sm">
            <SelectValue placeholder="Select Model" />
          </SelectTrigger>
          <SelectContent>
            {MODELS.map((model) => (
              <SelectItem key={model.id} value={model.id}>
                {model.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      */}

      {/* Chat area with animation */}
      <div 
        className={cn(
          "flex-1 flex flex-col w-full max-w-3xl mx-auto px-4 pb-6 transition-all duration-500 ease-out",
          isEmpty ? "justify-center pt-0" : "justify-end pt-16"
        )}
      >
        <Chat
          className={cn(
            "w-full transition-all duration-500 ease-out",
            isEmpty ? "max-h-[400px]" : "h-full"
          )}
          messages={messages}
          handleSubmit={handleSubmit}
          input={input}
          handleInputChange={handleInputChange}
          isGenerating={isLoading}
          stop={stop}
          append={append}
          setMessages={setMessages}
          transcribeAudio={transcribeAudio}
          suggestions={[
            "How can I apply TUM?",
            "What are the admission requirements?",
            "Tell me about the Computer Science program.",
          ]}
          welcomeMessage={userName ? `Teduco'ya Hoşgeldin ${userName}` : "Teduco'ya Hoşgeldin"}
        />
      </div>
    </div>
  )
}
