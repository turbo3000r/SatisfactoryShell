import { useCallback, useEffect, useRef, useState } from "react"
import { SendIcon } from "lucide-react"

import { LogView } from "@/components/log-view"
import { Button } from "@/components/ui/button"
import { Card, CardAction, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Skeleton } from "@/components/ui/skeleton"
import { Switch } from "@/components/ui/switch"
import { api, type ConsoleEntry } from "@/lib/api"
import { toastError } from "@/lib/errors"

const MAX_LOG_CHARS = 400_000
const TAIL_INTERVAL_MS = 1000

export function ConsolePage() {
  const [history, setHistory] = useState<ConsoleEntry[]>([])
  const [command, setCommand] = useState("")
  const [pending, setPending] = useState(false)
  const [ready, setReady] = useState(false)
  const [logText, setLogText] = useState("")
  const [logFile, setLogFile] = useState("")
  const [follow, setFollow] = useState(true)
  const offsetRef = useRef(0)

  useEffect(() => {
    let cancelled = false
    api
      .console()
      .then((data) => {
        if (cancelled) return
        setHistory(data.history)
        setLogText(data.log.text)
        setLogFile(data.log_file)
        offsetRef.current = data.log.offset
      })
      .catch(toastError)
      .finally(() => !cancelled && setReady(true))
    return () => {
      cancelled = true
    }
  }, [])

  // Byte-offset tail of FactoryGame.log, same contract as the old page.
  useEffect(() => {
    if (!ready) return
    const id = window.setInterval(async () => {
      try {
        const tail = await api.tail(offsetRef.current)
        offsetRef.current = tail.offset
        if (tail.rotated) setLogText(tail.text)
        else if (tail.text) setLogText((previous) => (previous + tail.text).slice(-MAX_LOG_CHARS))
      } catch {
        // transient failures are expected while the server restarts
      }
    }, TAIL_INTERVAL_MS)
    return () => window.clearInterval(id)
  }, [ready])

  const onSubmit = useCallback(
    async (event: React.FormEvent) => {
      event.preventDefault()
      if (command.trim() === "") return
      setPending(true)
      try {
        const result = await api.runCommand(command)
        setHistory(result.history)
        setCommand("")
      } catch (error) {
        toastError(error)
      } finally {
        setPending(false)
      }
    },
    [command],
  )

  if (!ready) {
    return (
      <div className="flex flex-col gap-4 px-4 lg:px-6">
        <Skeleton className="h-48 w-full" />
        <Skeleton className="h-96 w-full" />
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-4 px-4 lg:px-6 md:gap-6">
      <Card>
        <CardHeader>
          <CardTitle>Run command</CardTitle>
          <CardDescription>
            Sent through the game API <code>RunCommand</code>; try <code>?</code> for help.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <form className="flex items-end gap-2" onSubmit={onSubmit}>
            <div className="flex flex-1 flex-col gap-2">
              <Label htmlFor="command">Command</Label>
              <Input
                id="command"
                value={command}
                autoFocus
                autoComplete="off"
                placeholder="e.g. server.SaveGame backup"
                onChange={(event) => setCommand(event.target.value)}
              />
            </div>
            <Button type="submit" disabled={pending || command.trim() === ""}>
              <SendIcon />
              Run
            </Button>
          </form>

          {history.length === 0 ? (
            <p className="text-sm text-muted-foreground">No commands run yet.</p>
          ) : (
            <div className="flex flex-col gap-4">
              {history.map((entry, index) => (
                <div key={`${entry.ts}-${index}`} className="flex flex-col gap-2">
                  <p className="text-sm">
                    <span className="text-muted-foreground">{entry.ts}</span>{" "}
                    <span className="font-medium">&gt; {entry.command}</span>
                  </p>
                  <LogView
                    text={entry.error || entry.result}
                    follow={false}
                    empty="(no output)"
                    className={entry.error ? "h-32 border-destructive text-destructive" : "h-32"}
                  />
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>FactoryGame.log</CardTitle>
          <CardDescription>{logFile || "log file not found"}</CardDescription>
          <CardAction className="flex items-center gap-2">
            <Switch id="follow" checked={follow} onCheckedChange={setFollow} />
            <Label htmlFor="follow">Follow</Label>
          </CardAction>
        </CardHeader>
        <CardContent>
          <LogView text={logText} follow={follow} className="h-128" empty="(no log output)" />
        </CardContent>
      </Card>
    </div>
  )
}
