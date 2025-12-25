"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import {
  ArrowUpRight,
  Link,
  MoreHorizontal,
  StarOff,
  Star,
  Trash2,
  Plus,
} from "lucide-react"
import { toast } from "sonner"
import { supabase, getCachedSession } from "@/lib/supabase"

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  SidebarGroup,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuAction,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from "@/components/ui/sidebar"
import { Button } from "@/components/ui/button"

interface Chat {
  id: string
  title: string
  emoji: string
  is_pinned: boolean
  last_message_at: string
  created_at: string
}

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

export function NavChats() {
  const { isMobile } = useSidebar()
  const router = useRouter()
  const [chats, setChats] = useState<Chat[]>([])
  const [isLoading, setIsLoading] = useState(true)

  const fetchChats = async () => {
    try {
      const session = await getCachedSession()
      
      if (!session) {
        console.error("No session found")
        setIsLoading(false)
        return
      }

      const response = await fetch(`${BACKEND_URL}/chats`, {
        headers: {
          "Authorization": `Bearer ${session.access_token}`,
        },
      })

      if (response.ok) {
        const data = await response.json()
        setChats(data)
      } else {
        console.error("Failed to fetch chats:", response.status)
      }
    } catch (error) {
      console.error("Error fetching chats:", error)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchChats()

    // Set up realtime subscription for updates from other tabs/devices
    const channel = supabase
      .channel('chats-changes')
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'chats'
        },
        (payload) => {
          // Only update if the change came from another source (not this client)
          // This prevents double-fetching when we make changes ourselves
          if (payload.eventType === 'INSERT' && payload.new.id.startsWith('temp-')) {
            // Ignore optimistic updates
            return
          }
          
          // Update specific chat instead of refetching all
          if (payload.eventType === 'INSERT') {
            setChats(prev => {
              const exists = prev.some(chat => chat.id === payload.new.id)
              if (!exists) {
                return [payload.new as Chat, ...prev]
              }
              return prev
            })
          } else if (payload.eventType === 'UPDATE') {
            setChats(prev => prev.map(chat => 
              chat.id === payload.new.id ? payload.new as Chat : chat
            ))
          } else if (payload.eventType === 'DELETE') {
            setChats(prev => prev.filter(chat => chat.id !== payload.old.id))
          }
        }
      )
      .subscribe()

    return () => {
      supabase.removeChannel(channel)
    }
  }, [])

  const createNewChat = async () => {
    try {
      const session = await getCachedSession()
      
      if (!session) {
        toast.error("Please log in to create a chat")
        return
      }

      // Create optimistic chat entry
      const tempId = `temp-${Date.now()}`
      const optimisticChat: Chat = {
        id: tempId,
        title: "New Chat",
        emoji: "💬",
        is_pinned: false,
        last_message_at: new Date().toISOString(),
        created_at: new Date().toISOString()
      }
      
      // Add to UI immediately
      setChats(prev => [optimisticChat, ...prev])

      const response = await fetch(`${BACKEND_URL}/chats`, {
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

      if (response.ok) {
        const newChat = await response.json()
        
        // Replace optimistic chat with real one
        setChats(prev => prev.map(chat => 
          chat.id === tempId ? newChat : chat
        ))
        
        // Navigate to new chat (this only updates the dashboard, not sidebar)
        router.push(`/auth/dashboard?chat=${newChat.id}`)
        toast.success("New chat created")
      } else {
        // Remove optimistic chat on error
        setChats(prev => prev.filter(chat => chat.id !== tempId))
        toast.error("Failed to create chat")
      }
    } catch (error) {
      console.error("Error creating chat:", error)
      toast.error("Failed to create chat")
    }
  }

  const deleteChat = async (chatId: string, chatTitle: string) => {
    try {
      const session = await getCachedSession()
      
      if (!session) {
        toast.error("Please log in")
        return
      }

      // Optimistically remove from UI
      setChats(prev => prev.filter(chat => chat.id !== chatId))

      const response = await fetch(`${BACKEND_URL}/chats/${chatId}`, {
        method: "DELETE",
        headers: {
          "Authorization": `Bearer ${session.access_token}`,
        },
      })

      if (response.ok) {
        toast.success(`"${chatTitle}" deleted`)
      } else {
        // Restore on error by refetching
        fetchChats()
        toast.error("Failed to delete chat")
      }
    } catch (error) {
      console.error("Error deleting chat:", error)
      fetchChats()
      toast.error("Failed to delete chat")
    }
  }

  const togglePinChat = async (chatId: string, currentPinned: boolean) => {
    try {
      const session = await getCachedSession()
      
      if (!session) {
        toast.error("Please log in")
        return
      }

      // Optimistically update UI
      setChats(prev => prev.map(chat => 
        chat.id === chatId ? { ...chat, is_pinned: !currentPinned } : chat
      ))

      const response = await fetch(`${BACKEND_URL}/chats/${chatId}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({
          is_pinned: !currentPinned
        }),
      })

      if (response.ok) {
        toast.success(currentPinned ? "Unpinned" : "Pinned")
      } else {
        // Revert on error
        setChats(prev => prev.map(chat => 
          chat.id === chatId ? { ...chat, is_pinned: currentPinned } : chat
        ))
        toast.error("Failed to update chat")
      }
    } catch (error) {
      console.error("Error updating chat:", error)
      // Revert on error
      setChats(prev => prev.map(chat => 
        chat.id === chatId ? { ...chat, is_pinned: currentPinned } : chat
      ))
      toast.error("Failed to update chat")
    }
  }

  if (isLoading) {
    return (
      <SidebarGroup className="group-data-[collapsible=icon]:hidden">
        <SidebarGroupLabel>Chats</SidebarGroupLabel>
        <SidebarMenu>
          <div className="px-2 py-4 text-sm text-muted-foreground">Loading...</div>
        </SidebarMenu>
      </SidebarGroup>
    )
  }

  return (
    <SidebarGroup className="group-data-[collapsible=icon]:hidden">
      <div className="flex items-center justify-between">
        <SidebarGroupLabel>Chats</SidebarGroupLabel>
        <Button
          variant="ghost"
          size="icon"
          className="h-6 w-6"
          onClick={createNewChat}
          title="New Chat"
        >
          <Plus className="h-4 w-4" />
        </Button>
      </div>
      <SidebarMenu>
        {chats.length === 0 ? (
          <div className="px-2 py-4 text-sm text-muted-foreground">
            No chats yet. Create one to get started!
          </div>
        ) : (
          chats.map((chat) => (
            <SidebarMenuItem key={chat.id}>
              <SidebarMenuButton asChild>
                <a href={`/auth/dashboard?chat=${chat.id}`} title={chat.title}>
                  <span>{chat.emoji}</span>
                  <span className="truncate">{chat.title}</span>
                </a>
              </SidebarMenuButton>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <SidebarMenuAction showOnHover>
                    <MoreHorizontal />
                    <span className="sr-only">More</span>
                  </SidebarMenuAction>
                </DropdownMenuTrigger>
                <DropdownMenuContent
                  className="w-56 rounded-lg"
                  side={isMobile ? "bottom" : "right"}
                  align={isMobile ? "end" : "start"}
                >
                  <DropdownMenuItem onClick={() => togglePinChat(chat.id, chat.is_pinned)}>
                    {chat.is_pinned ? (
                      <>
                        <StarOff className="text-muted-foreground" />
                        <span>Unpin</span>
                      </>
                    ) : (
                      <>
                        <Star className="text-muted-foreground" />
                        <span>Pin</span>
                      </>
                    )}
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={() => {
                    navigator.clipboard.writeText(`${window.location.origin}/auth/dashboard?chat=${chat.id}`)
                    toast.success("Link copied to clipboard")
                  }}>
                    <Link className="text-muted-foreground" />
                    <span>Copy Link</span>
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => {
                    window.open(`/auth/dashboard?chat=${chat.id}`, '_blank')
                  }}>
                    <ArrowUpRight className="text-muted-foreground" />
                    <span>Open in New Tab</span>
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem 
                    className="text-destructive"
                    onClick={() => deleteChat(chat.id, chat.title)}
                  >
                    <Trash2 />
                    <span>Delete</span>
                  </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </SidebarMenuItem>
        ))
        )}
      </SidebarMenu>
    </SidebarGroup>
  )
}
