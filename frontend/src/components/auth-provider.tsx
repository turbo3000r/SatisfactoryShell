import { createContext, useCallback, useContext, useEffect, useRef, useState } from "react"
import { toast } from "sonner"

import { api, setUnauthorizedHandler } from "@/lib/api"

type AuthContextValue = {
  authed: boolean
  ready: boolean
  appVersion: string
  login: (password: string) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [authed, setAuthed] = useState(false)
  const [ready, setReady] = useState(false)
  const [appVersion, setAppVersion] = useState("")
  const authedRef = useRef(authed)

  useEffect(() => {
    authedRef.current = authed
  }, [authed])

  useEffect(() => {
    setUnauthorizedHandler(() => {
      if (authedRef.current) toast.warning("Session expired, please log in again.")
      setAuthed(false)
    })
  }, [])

  useEffect(() => {
    api
      .session()
      .then((session) => {
        setAuthed(session.authed)
        setAppVersion(session.app_version)
      })
      .catch(() => setAuthed(false))
      .finally(() => setReady(true))
  }, [])

  const login = useCallback(async (password: string) => {
    await api.login(password)
    setAuthed(true)
  }, [])

  const logout = useCallback(async () => {
    await api.logout()
    setAuthed(false)
  }, [])

  return (
    <AuthContext.Provider value={{ authed, ready, appVersion, login, logout }}>{children}</AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error("useAuth must be used within an AuthProvider")
  return context
}
