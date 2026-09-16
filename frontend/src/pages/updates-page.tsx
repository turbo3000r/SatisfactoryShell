import { DownloadCloudIcon, RefreshCwIcon, TriangleAlertIcon } from "lucide-react"

import { ConfirmAction } from "@/components/confirm-action"
import { LogView } from "@/components/log-view"
import { StatList } from "@/components/stat-list"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardAction, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { useAction } from "@/hooks/use-action"
import { usePoll } from "@/hooks/use-poll"
import { api } from "@/lib/api"
import { orDash } from "@/lib/format"

export function UpdatesPage() {
  const { data, loading, reload } = usePoll(api.updates, 2000)
  const { pending, run } = useAction()

  if (loading && !data) {
    return (
      <div className="flex flex-col gap-4 px-4 lg:px-6">
        <Skeleton className="h-64 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    )
  }
  if (!data) return null

  const { installed, status } = data
  const busy = pending || status.running
  const version = installed.version as Record<string, string | number>

  return (
    <div className="flex flex-col gap-4 px-4 lg:px-6 md:gap-6">
      {!data.steamcmd_available ? (
        <Alert variant="destructive">
          <TriangleAlertIcon />
          <AlertTitle>SteamCMD not found</AlertTitle>
          <AlertDescription>
            Set <code>paths.steamcmd</code> in <code>config.json</code>, or put{" "}
            <code>steamcmd\steamcmd.exe</code> next to the starter.
          </AlertDescription>
        </Alert>
      ) : null}

      <div className="grid grid-cols-1 gap-4 @3xl/main:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Installed</CardTitle>
            <CardDescription>
              App {data.app_id} ({data.beta || "public"})
            </CardDescription>
          </CardHeader>
          <CardContent>
            <StatList
              items={[
                { label: "Game version", value: orDash(version.GameVersion) },
                { label: "Changelist", value: orDash(version.Changelist) },
                { label: "Branch", value: orDash(version.BranchName) },
                { label: "Steam buildid", value: orDash(data.local_buildid) },
                { label: "Last updated", value: orDash(installed.manifest.LastUpdated_iso) },
                { label: "Install dir", value: orDash(data.server_root) },
                { label: "SteamCMD", value: orDash(data.steamcmd_path) },
              ]}
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Available</CardTitle>
            <CardDescription>Latest build on the {data.beta || "public"} branch.</CardDescription>
            <CardAction>
              {data.update_available ? (
                <Badge variant="outline">update available</Badge>
              ) : data.local_buildid && status.available_buildid ? (
                <Badge>up to date</Badge>
              ) : null}
            </CardAction>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <StatList
              items={[
                { label: "Latest buildid", value: status.available_buildid ?? "not checked" },
                { label: "Checked", value: orDash(status.checked_at) },
                ...(status.check_error ? [{ label: "Error", value: status.check_error }] : []),
              ]}
            />
            <div className="flex flex-wrap gap-2">
              <Button
                variant="outline"
                disabled={!data.steamcmd_available || busy}
                onClick={() => void run(api.checkUpdate, reload)}
              >
                <RefreshCwIcon />
                Check for update
              </Button>
              <ConfirmAction
                title="Stop the server and run SteamCMD?"
                description="The server is stopped before the update and started again afterwards if it was running."
                confirmLabel="Update now"
                onConfirm={() => run(api.runUpdate, reload)}
              >
                <Button disabled={!data.steamcmd_available || busy}>
                  <DownloadCloudIcon />
                  Update now
                </Button>
              </ConfirmAction>
            </div>
            <p className="text-sm text-muted-foreground">
              If this install lives in a Steam library, close the Steam client first, otherwise SteamCMD may
              fail with state <code>0x606</code>.
            </p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Last SteamCMD run</CardTitle>
          <CardDescription>
            {status.started_at
              ? `Started ${status.started_at}${status.finished_at ? `, finished ${status.finished_at}` : ""}`
              : "Not run yet."}
          </CardDescription>
          <CardAction>
            {status.running ? (
              <Badge variant="outline">running: {status.phase}</Badge>
            ) : status.exit_code !== null ? (
              <Badge variant={status.exit_code === 0 ? "default" : "destructive"}>
                exit {status.exit_code}
              </Badge>
            ) : null}
          </CardAction>
        </CardHeader>
        <CardContent>
          <LogView
            text={status.log_lines.join("\n")}
            follow={status.running}
            empty="(no steamcmd output yet)"
            className="h-112"
          />
        </CardContent>
      </Card>
    </div>
  )
}
