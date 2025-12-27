"use client"

import { useEffect } from "react"
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
import { supabase } from "@/lib/supabase"
import { useChats, useCreateChat, useDeleteChat, useUpdateChat } from "@/hooks/api/use-chat"

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

export function NavChats() {
  const { isMobile } = useSidebar()
  const router = useRouter()
  
  // Use React Query hooks
  const { data: chats = [], isLoading, refetch } = useChats()
  const createChatMutation = useCreateChat()
  const deleteChatMutation = useDeleteChat()
  const updateChatMutation = useUpdateChat()

  // Set up realtime subscription for updates from other tabs/devices
  useEffect(() => {
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
          // Refetch chats when changes occur from other sources
          // React Query will handle deduplication and caching
          if (payload.eventType === 'INSERT' || payload.eventType === 'UPDATE' || payload.eventType === 'DELETE') {
            refetch()
          }
        }
      )
      .subscribe()

    return () => {
      supabase.removeChannel(channel)
    }
  }, [refetch])

  const createNewChat = async () => {
    createChatMutation.mutate(
      { title: "New Chat" },
      {
        onSuccess: (newChat) => {
          router.push(`/dashboard?chat=${newChat.chatId}`)
        },
      }
    )
  }

  const deleteChat = (chatId: string, chatTitle: string) => {
    deleteChatMutation.mutate(chatId, {
      onSuccess: () => {
        toast.success(`"${chatTitle}" deleted`)
      },
    })
  }

  const togglePinChat = (chatId: string, currentPinned: boolean) => {
    updateChatMutation.mutate(
      { chatId, is_pinned: !currentPinned },
      {
        onSuccess: () => {
          toast.success(currentPinned ? "Unpinned" : "Pinned")
        },
      }
    )
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
            <SidebarMenuItem key={chat.chatId}>
              <SidebarMenuButton asChild>
                <a href={`/dashboard?chat=${chat.chatId}`} title={chat.title}>
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
                  <DropdownMenuItem onClick={() => togglePinChat(chat.chatId, chat.isPinned)}>
                    {chat.isPinned ? (
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
                    navigator.clipboard.writeText(`${window.location.origin}/dashboard?chat=${chat.chatId}`)
                    toast.success("Link copied to clipboard")
                  }}>
                    <Link className="text-muted-foreground" />
                    <span>Copy Link</span>
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => {
                    window.open(`/dashboard?chat=${chat.chatId}`, '_blank')
                  }}>
                    <ArrowUpRight className="text-muted-foreground" />
                    <span>Open in New Tab</span>
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem 
                    className="text-destructive"
                    onClick={() => deleteChat(chat.chatId, chat.title)}
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
