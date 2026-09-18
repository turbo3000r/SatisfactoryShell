import type { CSSProperties, ReactNode } from "react"
import { Navigate, Route, Routes, useLocation } from "react-router-dom"

import { AppSidebar } from "@/components/app-sidebar"
import { AuthProvider, useAuth } from "@/components/auth-provider"
import { SiteHeader } from "@/components/site-header"
import { ThemeProvider } from "@/components/theme-provider"
import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar"
import { Skeleton } from "@/components/ui/skeleton"
import { Toaster } from "@/components/ui/sonner"
import { TooltipProvider } from "@/components/ui/tooltip"
import { ConsolePage } from "@/pages/console-page"
import { DashboardPage } from "@/pages/dashboard-page"
import { HomePage } from "@/pages/home-page"
import { LoginPage } from "@/pages/login-page"
import { SavesPage } from "@/pages/saves-page"
import { UpdatesPage } from "@/pages/updates-page"

/** Pages that need a game-API session; unauthenticated visitors go to /login. */
function RequireAuth({ children }: { children: ReactNode }) {
  const { authed, ready } = useAuth()
  const location = useLocation()

  if (!ready) {
    return (
      <div className="flex flex-col gap-4 px-4 lg:px-6">
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    )
  }
  if (!authed) {
    return <Navigate to={`/login?next=${encodeURIComponent(location.pathname)}`} replace />
  }
  return children
}

function AppShell() {
  return (
    <SidebarProvider
      style={
        {
          "--sidebar-width": "calc(var(--spacing) * 60)",
          "--header-height": "calc(var(--spacing) * 12)",
        } as CSSProperties
      }
    >
      <AppSidebar variant="inset" />
      <SidebarInset>
        <SiteHeader />
        <div className="flex flex-1 flex-col">
          <div className="@container/main flex flex-1 flex-col gap-2">
            <div className="flex flex-col gap-4 py-4 md:gap-6 md:py-6">
              <Routes>
                <Route path="/" element={<HomePage />} />
                <Route path="/login" element={<LoginPage />} />
                <Route
                  path="/dashboard"
                  element={
                    <RequireAuth>
                      <DashboardPage />
                    </RequireAuth>
                  }
                />
                <Route
                  path="/saves"
                  element={
                    <RequireAuth>
                      <SavesPage />
                    </RequireAuth>
                  }
                />
                <Route
                  path="/console"
                  element={
                    <RequireAuth>
                      <ConsolePage />
                    </RequireAuth>
                  }
                />
                <Route
                  path="/updates"
                  element={
                    <RequireAuth>
                      <UpdatesPage />
                    </RequireAuth>
                  }
                />
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </div>
          </div>
        </div>
      </SidebarInset>
    </SidebarProvider>
  )
}

function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <TooltipProvider>
          <AppShell />
          <Toaster />
        </TooltipProvider>
      </AuthProvider>
    </ThemeProvider>
  )
}

export default App
