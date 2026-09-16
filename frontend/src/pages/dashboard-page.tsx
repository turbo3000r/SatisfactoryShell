import { PlayIcon, RotateCcwIcon, SquareIcon } from "lucide-react"

import { ConfirmAction } from "@/components/confirm-action"
import { MetricsCharts } from "@/components/metrics-charts"
import { OnOffBadge, ServerStateBadge, TickRateBadge } from "@/components/state-badges"
import { StatList } from "@/components/stat-list"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Skeleton } from "@/components/ui/skeleton"
import { Switch } from "@/components/ui/switch"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { useAction } from "@/hooks/use-action"
import { usePoll } from "@/hooks/use-poll"
import { api, type DashboardResponse } from "@/lib/api"
import { formatDuration, formatTickRate, orDash } from "@/lib/format"

function StatCard({
  label,
  value,
  action,
  footer,
}: {
  label: string
  value: React.ReactNode
  action?: React.ReactNode
  footer?: React.ReactNode
}) {
  return (
    <Card className="@container/card">
      <CardHeader>
        <CardDescription>{label}</CardDescription>
        <CardTitle className="text-2xl font-semibold tabular-nums @[250px]/card:text-3xl">{value}</CardTitle>
        {action ? <CardAction>{action}</CardAction> : null}
      </CardHeader>
      {footer ? (
        <CardFooter className="text-sm text-muted-foreground">
          <div className="line-clamp-1">{footer}</div>
        </CardFooter>
      ) : null}
    </Card>
  )
}

function ProcessCard({ data, reload }: { data: DashboardResponse; reload: () => Promise<void> }) {
  const { pending, run } = useAction()
  const { process: proc } = data
  const busy = pending || Boolean(proc.busy)

  return (
    <Card>
      <CardHeader>
        <CardTitle>Process</CardTitle>
        <CardDescription>FactoryServer.exe lifecycle</CardDescription>
        <CardAction>{proc.busy ? <Badge variant="outline">{proc.busy}</Badge> : null}</CardAction>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <StatList
          items={[
            {
              label: "PID",
              value: proc.running ? `${proc.pid}${proc.owned ? "" : " (external, adopted)"}` : "-",
            },
            { label: "Uptime", value: proc.running ? formatDuration(proc.uptime_seconds) : "-" },
            {
              label: "Unexpected exits",
              value: proc.last_unexpected_exit
                ? `${proc.unexpected_exits} (last ${proc.last_unexpected_exit})`
                : String(proc.unexpected_exits),
            },
            { label: "Last exit code", value: orDash(proc.last_exit_code) },
          ]}
        />
        <div className="flex flex-wrap items-center gap-2">
          <Button disabled={busy || proc.running} onClick={() => void run(() => api.processAction("start"), reload)}>
            <PlayIcon />
            Start
          </Button>
          <ConfirmAction
            title="Stop the server?"
            description="Connected players will be disconnected."
            confirmLabel="Stop"
            destructive
            onConfirm={() => run(() => api.processAction("stop"), reload)}
          >
            <Button variant="destructive" disabled={busy || !proc.running}>
              <SquareIcon />
              Stop
            </Button>
          </ConfirmAction>
          <ConfirmAction
            title="Restart the server?"
            description="The server is stopped and started again; players will be disconnected."
            confirmLabel="Restart"
            onConfirm={() => run(() => api.processAction("restart"), reload)}
          >
            <Button variant="outline" disabled={busy || !proc.running}>
              <RotateCcwIcon />
              Restart
            </Button>
          </ConfirmAction>
        </div>
        <div className="flex items-center gap-2">
          <Switch
            id="auto-restart"
            checked={proc.auto_restart}
            disabled={pending}
            onCheckedChange={() => void run(() => api.processAction("toggle-auto-restart"), reload)}
          />
          <Label htmlFor="auto-restart">Restart automatically after a crash</Label>
        </div>
      </CardContent>
    </Card>
  )
}

function ServerOptionsCard({ options, pending }: { options: Record<string, string>; pending: Record<string, string> }) {
  const keys = Object.keys(options).sort()

  return (
    <Card>
      <CardHeader>
        <CardTitle>Server options</CardTitle>
        <CardDescription>Read-only; pending values apply after a restart.</CardDescription>
      </CardHeader>
      <CardContent>
        {keys.length === 0 ? (
          <p className="text-sm text-muted-foreground">No options reported.</p>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Option</TableHead>
                <TableHead className="text-right">Value</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {keys.map((key) => (
                <TableRow key={key}>
                  <TableCell className="font-medium">{key.replace("FG.", "")}</TableCell>
                  <TableCell className="text-right">
                    <span className="flex items-center justify-end gap-2">
                      {options[key]}
                      {key in pending ? <Badge variant="outline">→ {pending[key]}</Badge> : null}
                    </span>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  )
}

export function DashboardPage() {
  const { data, loading, reload } = usePoll(api.dashboard, 5000)
  const metrics = usePoll(api.metrics, 5000)

  if (loading && !data) {
    return (
      <div className="flex flex-col gap-4 px-4 lg:px-6">
        <Skeleton className="h-28 w-full" />
        <Skeleton className="h-72 w-full" />
      </div>
    )
  }
  if (!data) return null

  const { game_state: game, process: proc, events } = data

  return (
    <div className="flex flex-col gap-4 px-4 lg:px-6 md:gap-6">
      {data.api_error ? (
        <Alert variant="destructive">
          <AlertTitle>Game API: {data.api_error}</AlertTitle>
          <AlertDescription>The server may be offline or loading a save.</AlertDescription>
        </Alert>
      ) : null}

      <div className="grid grid-cols-1 gap-4 @xl/main:grid-cols-2 @5xl/main:grid-cols-4">
        <StatCard
          label="Server state"
          value={data.state_name}
          action={<ServerStateBadge name={data.state_name} />}
          footer={proc.running ? `pid ${proc.pid}` : "process not running"}
        />
        <StatCard
          label="Players"
          value={game ? `${game.players} / ${orDash(game.player_limit)}` : "-"}
          footer={game?.session_name ? `session ${game.session_name}` : "no session loaded"}
        />
        <StatCard
          label="Tick rate"
          value={game ? formatTickRate(game.tick_rate) : "-"}
          action={game ? <TickRateBadge value={game.tick_rate} /> : null}
          footer={game ? (game.is_paused ? "game paused" : "game running") : "waiting for session"}
        />
        <StatCard
          label="Process uptime"
          value={proc.running ? formatDuration(proc.uptime_seconds) : "-"}
          action={<OnOffBadge on={proc.auto_restart} labels={["auto-restart on", "auto-restart off"]} />}
          footer={`${proc.unexpected_exits} unexpected exit(s)`}
        />
      </div>

      <MetricsCharts samples={metrics.data?.samples ?? []} />

      <div className="grid grid-cols-1 gap-4 @3xl/main:grid-cols-2">
        <ProcessCard data={data} reload={reload} />

        <Card>
          <CardHeader>
            <CardTitle>Game</CardTitle>
            <CardDescription>Reported by QueryServerState</CardDescription>
          </CardHeader>
          <CardContent>
            {game ? (
              <StatList
                items={[
                  { label: "Session", value: orDash(game.session_name) },
                  {
                    label: "Running",
                    value: (
                      <OnOffBadge on={game.is_running} labels={["save loaded", "waiting for session"]} />
                    ),
                  },
                  { label: "Paused", value: <OnOffBadge on={!game.is_paused} labels={["running", "paused"]} /> },
                  { label: "Players", value: `${game.players} / ${orDash(game.player_limit)}` },
                  { label: "Tick rate", value: <TickRateBadge value={game.tick_rate} /> },
                  { label: "Time played", value: formatDuration(game.duration_seconds) },
                  { label: "Tech tier", value: orDash(game.tech_tier) },
                  { label: "Game phase", value: orDash(game.game_phase) },
                  { label: "Active milestone", value: orDash(game.active_schematic) },
                  { label: "Auto-load session", value: orDash(game.auto_load_session) },
                ]}
              />
            ) : (
              <p className="text-sm text-muted-foreground">Server API not reachable.</p>
            )}
          </CardContent>
        </Card>

        <ServerOptionsCard options={data.options} pending={data.pending} />

        <Card>
          <CardHeader>
            <CardTitle>Recent events</CardTitle>
            <CardDescription>Process manager log</CardDescription>
          </CardHeader>
          <CardContent>
            {events.length === 0 ? (
              <p className="text-sm text-muted-foreground">None yet.</p>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Time</TableHead>
                    <TableHead>Event</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {events.map((event) => (
                    <TableRow key={`${event.ts}-${event.message}`}>
                      <TableCell className="whitespace-nowrap text-muted-foreground">{event.ts}</TableCell>
                      <TableCell>{event.message}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
