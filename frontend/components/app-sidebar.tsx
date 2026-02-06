"use client"

import * as React from "react"
import {
  Home,
  Sparkles,
  FileEdit,
} from "lucide-react"

import { NavChats } from "@/components/nav-chats"
import { NavMain } from "@/components/nav-main"
import DarkToggle from "@/components/dark-toggle"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarRail,
} from "@/components/ui/sidebar"
import { NavUser } from "./nav-user"

// This is sample data.
const data = {
  navMain: [
    {
      title: "Home",
      url: "/dashboard",
      icon: Home,
    },
    {
      title: "Edit Letters",
      url: "/edit",
      icon: FileEdit,
    },
  ],
}

type AppSidebarProps = React.ComponentProps<typeof Sidebar> & {
  user?: {
    name: string
    email: string
    avatar: string
  }
}

export function AppSidebar({ user, ...props }: AppSidebarProps) {
  
  return (
    <Sidebar className="border-r-0" {...props}>
      <SidebarHeader>
        <div className="flex items-center gap-2 px-3 py-2">
          <div className="text-lg font-semibold">Teduco</div>
          <DarkToggle />
        </div>
        <NavMain items={data.navMain} />
      </SidebarHeader>
      <SidebarContent>
        <NavChats />
      </SidebarContent>
      <SidebarRail />
      <SidebarFooter>
        {/* Footer content can go here */}
        {user && <NavUser user={user} />}
      </SidebarFooter>
    </Sidebar>
  )
}
