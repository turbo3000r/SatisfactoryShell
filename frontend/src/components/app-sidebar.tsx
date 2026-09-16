import * as React from "react"
import { FactoryIcon, GaugeIcon, HardDriveDownloadIcon, SaveIcon, TerminalIcon, HouseIcon } from "lucide-react"
import { Link } from "react-router-dom"

import { useAuth } from "@/components/auth-provider"
import { NavMain } from "@/components/nav-main"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar"

const NAV_ITEMS = [
  { title: "Home", url: "/", icon: <HouseIcon /> },
  { title: "Dashboard", url: "/dashboard", icon: <GaugeIcon />, requiresAuth: true },
  { title: "Saves", url: "/saves", icon: <SaveIcon />, requiresAuth: true },
  { title: "Console", url: "/console", icon: <TerminalIcon />, requiresAuth: true },
  { title: "Updates", url: "/updates", icon: <HardDriveDownloadIcon />, requiresAuth: true },
]

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  const { appVersion } = useAuth()

  return (
    <Sidebar collapsible="offcanvas" {...props}>
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton asChild className="data-[slot=sidebar-menu-button]:p-1.5!">
              <Link to="/">
                <FactoryIcon className="size-5!" />
                <span className="text-base font-semibold">Satisfactory Shell</span>
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>
      <SidebarContent>
        <NavMain items={NAV_ITEMS} />
      </SidebarContent>
      <SidebarFooter>
        <p className="px-2 py-1 text-xs text-muted-foreground">
          satisfactory-shell {appVersion || "\u2026"}
        </p>
      </SidebarFooter>
    </Sidebar>
  )
}
