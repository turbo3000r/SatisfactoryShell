import { PlayIcon } from "lucide-react"

import { HealthBadge, ServerStateBadge } from "@/components/state-badges"
import { StatList } from "@/components/stat-list"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Card, CardAction, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { useAction } from "@/hooks/use-action"
import { usePoll } from "@/hooks/use-poll"
import { api } from "@/lib/api"
import { formatDuration, formatTickRate, orDash } from "@/lib/format"

const BOOTSTRAP_VARIANTS: Record<string, "default" | "destructive"> = {
  failed: "destructive",
}

export function HomePage() {
  const { data, loading, reload } = usePoll(api.status, 5000)
  const { pending, run } = useAction()

  if (loading && !data) {
    return (
      <div className="grid grid-cols-1 gap-4 px-4 lg:px-6 @3xl/main:grid-cols-2">
        <Skeleton className="h-72 w-full" />
        <Skeleton className="h-72 w-full" />
      </div>
    )
  }
  if (!data) return null

  const { state, process, game_state: game, lightweight, runtime, version, manifest, bootstrap } = data
  const engine = `${orDash(version.MajorVersion)}.${orDash(version.MinorVersion)}.${orDash(version.PatchVersion)}`

  return (
    <div className="flex flex-col gap-4 px-4 lg:px-6">
      {bootstrap.state && bootstrap.state !== "none" ? (
        <Alert variant={BOOTSTRAP_VARIANTS[bootstrap.state] ?? "default"}>
          <AlertTitle>First-run claim: {bootstrap.state}</AlertTitle>
          <AlertDescription>{bootstrap.message}</AlertDescription>
        </Alert>
      ) : null}

      <div className="grid grid-cols-1 gap-4 @3xl/main:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Status</CardTitle>
            <CardAction>
              <ServerStateBadge name={state.name} />
            </CardAction>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <StatList
              items={[
                {
                  label: "Health",
                  value:
                    data.health !== null ? (
                      <HealthBadge health={data.health} />
                    ) : state.num === 2 ? (
                      <span className="text-muted-foreground">API unavailable while loading</span>
                    ) : (
                      orDash(data.api_error)
                    ),
                },
                { label: "Server name", value: orDash(lightweight?.server_name) },
                { label: "Net changelist", value: orDash(lightweight?.changelist) },
                { label: "Modded", value: lightweight ? (lightweight.modded ? "yes" : "no") : "-" },
                {
                  label: "Process",
                  value: process.running
                    ? `pid ${process.pid}${process.owned ? "" : " (external)"}, up ${formatDuration(process.uptime_seconds)}`
                    : "not running",
                },
              ]}
            />
            {process.running ? (
              process.busy ? (
                <p className="text-sm text-muted-foreground">{process.busy}…</p>
              ) : null
            ) : (
              <Button
                className="self-start"
                disabled={pending || Boolean(process.busy)}
                onClick={() => void run(api.startServer, reload)}
              >
                <PlayIcon />
                Start server
              </Button>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Dedicated server version</CardTitle>
          </CardHeader>
          <CardContent>
            <StatList
              items={[
                { label: "Game version", value: orDash(version.GameVersion) },
                { label: "Changelist", value: orDash(version.Changelist) },
                { label: "Branch", value: orDash(version.BranchName) },
                { label: "Engine", value: engine },
                { label: "Steam buildid", value: orDash(manifest.buildid) },
                { label: "Last updated", value: orDash(manifest.LastUpdated_iso) },
              ]}
            />
          </CardContent>
        </Card>

        {game ? (
          <Card>
            <CardHeader>
              <CardTitle>Game state</CardTitle>
            </CardHeader>
            <CardContent>
              <StatList
                items={[
                  { label: "Session", value: orDash(game.session_name) },
                  { label: "Players", value: `${game.players} / ${orDash(game.player_limit)}` },
                  { label: "Tech tier", value: orDash(game.tech_tier) },
                  { label: "Game phase", value: orDash(game.game_phase) },
                  { label: "Active milestone", value: orDash(game.active_schematic) },
                  { label: "Time played", value: formatDuration(game.duration_seconds) },
                  { label: "Paused", value: game.is_paused ? "yes" : "no" },
                  { label: "Tick rate", value: formatTickRate(game.tick_rate) },
                  { label: "Auto-load session", value: orDash(game.auto_load_session) },
                ]}
              />
            </CardContent>
          </Card>
        ) : null}

        <Card>
          <CardHeader>
            <CardTitle>Shell runtime</CardTitle>
          </CardHeader>
          <CardContent>
            <StatList
              items={[
                { label: "Version", value: `${runtime.app_version} (${runtime.mode})` },
                { label: "Python", value: runtime.python },
                { label: "Platform", value: runtime.platform },
                { label: "Uptime", value: formatDuration(runtime.uptime) },
                { label: "WebUI bind", value: runtime.bind },
                { label: "Game API", value: runtime.game_api },
                { label: "Server root", value: runtime.server_root },
                { label: "SteamCMD", value: runtime.steamcmd },
                { label: "Config", value: runtime.config },
              ]}
            />
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
