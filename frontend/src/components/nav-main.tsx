import { LockIcon } from "lucide-react"
import { Link, useLocation } from "react-router-dom"

import { useAuth } from "@/components/auth-provider"
import {
  SidebarGroup,
  SidebarGroupContent,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar"

export function NavMain({
  items,
}: {
  items: {
    title: string
    url: string
    icon?: React.ReactNode
    requiresAuth?: boolean
  }[]
}) {
  const location = useLocation()
  const { authed } = useAuth()

  return (
    <SidebarGroup>
      <SidebarGroupContent className="flex flex-col gap-2">
        <SidebarMenu>
          {items.map((item) => {
            const locked = Boolean(item.requiresAuth) && !authed
            return (
              <SidebarMenuItem key={item.title}>
                <SidebarMenuButton
                  asChild
                  tooltip={locked ? `${item.title} (login required)` : item.title}
                  isActive={location.pathname === item.url}
                >
                  <Link to={item.url}>
                    {item.icon}
                    <span>{item.title}</span>
                    {locked ? <LockIcon className="ml-auto size-3 text-muted-foreground" /> : null}
                  </Link>
                </SidebarMenuButton>
              </SidebarMenuItem>
            )
          })}
        </SidebarMenu>
      </SidebarGroupContent>
    </SidebarGroup>
  )
}
