import * as React from "react"
import {
  BoxesIcon,
  FactoryIcon,
  GaugeIcon,
  SaveIcon,
  TerminalIcon,
  UploadCloudIcon,
} from "lucide-react"

import { NavMain } from "@/components/nav-main"
import { NavUser } from "@/components/nav-user"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar"

const data = {
  user: {
    name: "Admin",
    email: "admin@satisfactory-shell.local",
    avatar: "",
  },
  navMain: [
    {
      title: "Home",
      url: "/",
      icon: <GaugeIcon />,
    },
    {
      title: "Dashboard",
      url: "/dashboard",
      icon: <BoxesIcon />,
      requiresAuth: true,
    },
    {
      title: "Saves",
      url: "/saves",
      icon: <SaveIcon />,
      requiresAuth: true,
    },
    {
      title: "Console",
      url: "/console",
      icon: <TerminalIcon />,
      requiresAuth: true,
    },
    {
      title: "Updates",
      url: "/updates",
      icon: <UploadCloudIcon />,
      requiresAuth: true,
    },
  ],
}

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  return (
    <Sidebar collapsible="offcanvas" {...props}>
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton
              asChild
              className="data-[slot=sidebar-menu-button]:p-1.5!"
            >
              <a href="/">
                <FactoryIcon className="size-5!" />
                <span className="text-base font-semibold">Satisfactory Shell</span>
              </a>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>
      <SidebarContent>
        <NavMain items={data.navMain} />
      </SidebarContent>
      <SidebarFooter>
        <NavUser user={data.user} />
      </SidebarFooter>
    </Sidebar>
  )
}
