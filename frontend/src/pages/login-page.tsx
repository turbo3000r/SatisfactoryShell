import { useState } from "react"
import { Navigate, useNavigate, useSearchParams } from "react-router-dom"
import { toast } from "sonner"

import { useAuth } from "@/components/auth-provider"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { describeError } from "@/lib/errors"

export function LoginPage() {
  const { authed, login } = useAuth()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [password, setPassword] = useState("")
  const [error, setError] = useState<string | null>(null)
  const [pending, setPending] = useState(false)

  const next = searchParams.get("next") || "/dashboard"
  if (authed) return <Navigate to={next} replace />

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault()
    setPending(true)
    setError(null)
    try {
      await login(password)
      toast.success("Signed in.")
      navigate(next, { replace: true })
    } catch (err) {
      setError(describeError(err))
    } finally {
      setPending(false)
    }
  }

  return (
    <div className="px-4 lg:px-6">
      <Card className="mx-auto w-full max-w-md">
        <CardHeader>
          <CardTitle>Login</CardTitle>
          <CardDescription>
            Use the Satisfactory server <strong>admin password</strong>. Leave it empty to try passwordless
            login on an unclaimed server.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={onSubmit} className="flex flex-col gap-4">
            {error ? (
              <Alert variant="destructive">
                <AlertTitle>Login failed</AlertTitle>
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            ) : null}
            <div className="flex flex-col gap-2">
              <Label htmlFor="password">Admin password</Label>
              <Input
                id="password"
                type="password"
                autoComplete="current-password"
                autoFocus
                value={password}
                onChange={(event) => setPassword(event.target.value)}
              />
            </div>
            <Button type="submit" disabled={pending}>
              {pending ? "Signing in..." : "Sign in"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
