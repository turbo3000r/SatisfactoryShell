import { LogInIcon, LogOutIcon } from "lucide-react"
import { useLocation, useNavigate } from "react-router-dom"
import { toast } from "sonner"

import { useAuth } from "@/components/auth-provider"
import { ModeToggle } from "@/components/mode-toggle"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { SidebarTrigger } from "@/components/ui/sidebar"

const TITLES: Record<string, string> = {
  "/": "Server overview",
  "/dashboard": "Dashboard",
  "/saves": "Saves",
  "/console": "Console",
  "/updates": "Updates (SteamCMD)",
  "/login": "Login",
}

export function SiteHeader() {
  const location = useLocation()
  const navigate = useNavigate()
  const { authed, logout } = useAuth()

  async function onLogout() {
    await logout()
    toast.success("Signed out.")
    navigate("/")
  }

  return (
    <header className="flex h-(--header-height) shrink-0 items-center gap-2 border-b transition-[width,height] ease-linear group-has-data-[collapsible=icon]/sidebar-wrapper:h-(--header-height)">
      <div className="flex w-full items-center gap-1 px-4 lg:gap-2 lg:px-6">
        <SidebarTrigger className="-ml-1" />
        <Separator orientation="vertical" className="mx-2 data-[orientation=vertical]:h-4" />
        <h1 className="text-base font-medium">{TITLES[location.pathname] ?? "Satisfactory Shell"}</h1>
        <div className="ml-auto flex items-center gap-2">
          <ModeToggle />
          {authed ? (
            <Button variant="outline" size="sm" onClick={() => void onLogout()}>
              <LogOutIcon />
              Logout
            </Button>
          ) : (
            <Button variant="outline" size="sm" onClick={() => navigate("/login")}>
              <LogInIcon />
              Login
            </Button>
          )}
        </div>
      </div>
    </header>
  )
}
