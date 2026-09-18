import { useState } from "react"
import { DownloadIcon, FolderOpenIcon, PlusIcon, SaveIcon, Trash2Icon, UploadIcon } from "lucide-react"

import { ConfirmAction } from "@/components/confirm-action"
import { SaveFlagBadges } from "@/components/state-badges"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardAction, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Checkbox } from "@/components/ui/checkbox"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Skeleton } from "@/components/ui/skeleton"
import { Switch } from "@/components/ui/switch"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { useAction } from "@/hooks/use-action"
import { usePoll } from "@/hooks/use-poll"
import { api, type SaveSession } from "@/lib/api"
import { formatDuration, orDash } from "@/lib/format"

function SaveNowCard({ isPlaying, reload }: { isPlaying: boolean; reload: () => Promise<void> }) {
  const [name, setName] = useState("")
  const { pending, run } = useAction()

  return (
    <Card>
      <CardHeader>
        <CardTitle>Save current game</CardTitle>
        <CardDescription>
          {isPlaying ? "Writes a new save file for the loaded session." : "No session loaded."}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form
          className="flex flex-wrap items-end gap-2"
          onSubmit={(event) => {
            event.preventDefault()
            void run(() => api.saveGame(name), async () => {
              setName("")
              await reload()
            })
          }}
        >
          <div className="flex min-w-48 flex-1 flex-col gap-2">
            <Label htmlFor="save-name">Save name</Label>
            <Input
              id="save-name"
              value={name}
              disabled={!isPlaying}
              onChange={(event) => setName(event.target.value)}
              placeholder="backup-manual"
            />
          </div>
          <Button type="submit" disabled={!isPlaying || pending || name.trim() === ""}>
            <SaveIcon />
            Save now
          </Button>
        </form>
      </CardContent>
    </Card>
  )
}

function UploadCard({ reload }: { reload: () => Promise<void> }) {
  const [file, setFile] = useState<File | null>(null)
  const [name, setName] = useState("")
  const [load, setLoad] = useState(false)
  const [ags, setAgs] = useState(false)
  const { pending, run } = useAction()

  return (
    <Card>
      <CardHeader>
        <CardTitle>Upload save</CardTitle>
        <CardDescription>Send a local .sav file to the dedicated server.</CardDescription>
      </CardHeader>
      <CardContent>
        <form
          className="flex flex-col gap-4"
          onSubmit={(event) => {
            event.preventDefault()
            if (!file) return
            void run(() => api.uploadSave({ file, saveName: name, load, ags }), async () => {
              setFile(null)
              setName("")
              await reload()
            })
          }}
        >
          <div className="flex flex-col gap-2">
            <Label htmlFor="upload-file">Save file</Label>
            <Input
              id="upload-file"
              type="file"
              accept=".sav"
              onChange={(event) => setFile(event.target.files?.[0] ?? null)}
            />
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="upload-name">Save name</Label>
            <Input
              id="upload-name"
              value={name}
              onChange={(event) => setName(event.target.value)}
              placeholder="default: file name"
            />
          </div>
          <div className="flex flex-wrap items-center gap-6">
            <div className="flex items-center gap-2">
              <Switch id="upload-load" checked={load} onCheckedChange={setLoad} />
              <Label htmlFor="upload-load">Load after upload</Label>
            </div>
            <div className="flex items-center gap-2">
              <Switch id="upload-ags" checked={ags} onCheckedChange={setAgs} />
              <Label htmlFor="upload-ags">Advanced game settings</Label>
            </div>
          </div>
          <Button type="submit" className="self-start" disabled={!file || pending}>
            <UploadIcon />
            Upload
          </Button>
        </form>
      </CardContent>
    </Card>
  )
}

function NewGameCard({ reload }: { reload: () => Promise<void> }) {
  const [session, setSession] = useState("")
  const [startingLocation, setStartingLocation] = useState("")
  const [mapName, setMapName] = useState("")
  const { pending, run } = useAction()

  return (
    <Card>
      <CardHeader>
        <CardTitle>Create new game</CardTitle>
        <CardDescription>Starts a fresh session and loads it.</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <div className="flex flex-col gap-2">
          <Label htmlFor="new-session">Session name</Label>
          <Input id="new-session" value={session} onChange={(event) => setSession(event.target.value)} />
        </div>
        <div className="flex flex-col gap-2">
          <Label htmlFor="new-location">Starting location (optional)</Label>
          <Input
            id="new-location"
            value={startingLocation}
            onChange={(event) => setStartingLocation(event.target.value)}
          />
        </div>
        <div className="flex flex-col gap-2">
          <Label htmlFor="new-map">Map package path (optional)</Label>
          <Input id="new-map" value={mapName} onChange={(event) => setMapName(event.target.value)} />
        </div>
        <ConfirmAction
          title="Create and load a new session?"
          description="The current session will be unloaded and the game API is unavailable while loading."
          confirmLabel="Create & load"
          onConfirm={() =>
            run(
              () =>
                api.newGame({
                  session_name: session,
                  starting_location: startingLocation,
                  map_name: mapName,
                }),
              async () => {
                setSession("")
                setStartingLocation("")
                setMapName("")
                await reload()
              },
            )
          }
        >
          <Button className="self-start" disabled={pending || session.trim() === ""}>
            <PlusIcon />
            Create &amp; load
          </Button>
        </ConfirmAction>
      </CardContent>
    </Card>
  )
}

function AutoLoadCard({
  sessions,
  current,
  reload,
}: {
  sessions: SaveSession[]
  current: string
  reload: () => Promise<void>
}) {
  const [selected, setSelected] = useState("")
  const { pending, run } = useAction()

  return (
    <Card>
      <CardHeader>
        <CardTitle>Auto-load on startup</CardTitle>
        <CardDescription>Session the server loads when it starts.</CardDescription>
        <CardAction>
          <Badge variant="outline">current: {orDash(current)}</Badge>
        </CardAction>
      </CardHeader>
      <CardContent className="flex flex-wrap items-end gap-2">
        <div className="flex min-w-48 flex-1 flex-col gap-2">
          <Label htmlFor="autoload-session">Session</Label>
          <Select value={selected} onValueChange={setSelected}>
            <SelectTrigger id="autoload-session">
              <SelectValue placeholder="choose session" />
            </SelectTrigger>
            <SelectContent>
              {sessions.map((session) => (
                <SelectItem key={session.sessionName} value={session.sessionName}>
                  {session.sessionName}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <Button
          variant="outline"
          disabled={pending || selected === ""}
          onClick={() => void run(() => api.setAutoLoad(selected), reload)}
        >
          Set auto-load
        </Button>
      </CardContent>
    </Card>
  )
}

function SessionCard({
  session,
  loaded,
  reload,
}: {
  session: SaveSession
  loaded: boolean
  reload: () => Promise<void>
}) {
  const [agsByName, setAgsByName] = useState<Record<string, boolean>>({})
  const { pending, run } = useAction()

  return (
    <Card>
      <CardHeader>
        <CardTitle>Session: {session.sessionName}</CardTitle>
        <CardDescription>{session.headers.length} save file(s)</CardDescription>
        <CardAction className="flex items-center gap-2">
          {loaded ? <Badge>loaded</Badge> : null}
          <ConfirmAction
            title={`Delete session ${session.sessionName}?`}
            description={`All ${session.headers.length} save files of this session are deleted on the server.`}
            confirmLabel="Delete session"
            destructive
            onConfirm={() => run(() => api.deleteSaveSession(session.sessionName), reload)}
          >
            <Button variant="destructive" size="sm" disabled={pending}>
              <Trash2Icon />
              Delete session
            </Button>
          </ConfirmAction>
        </CardAction>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Save</TableHead>
              <TableHead>Saved</TableHead>
              <TableHead>Play time</TableHead>
              <TableHead>Map</TableHead>
              <TableHead>Build</TableHead>
              <TableHead>Flags</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {session.headers.map((header) => {
              const ags = agsByName[header.saveName] ?? header.creative
              return (
                <TableRow key={header.saveName}>
                  <TableCell className="font-medium">{header.saveName}</TableCell>
                  <TableCell className="text-muted-foreground">{orDash(header.saveDateTime)}</TableCell>
                  <TableCell>{formatDuration(header.playDuration)}</TableCell>
                  <TableCell className="text-muted-foreground">{orDash(header.mapName)}</TableCell>
                  <TableCell className="text-muted-foreground">{orDash(header.buildVersion)}</TableCell>
                  <TableCell>
                    <SaveFlagBadges header={header} />
                  </TableCell>
                  <TableCell>
                    <div className="flex flex-wrap items-center justify-end gap-2">
                      <div className="flex items-center gap-2">
                        <Checkbox
                          id={`ags-${header.saveName}`}
                          checked={ags}
                          onCheckedChange={(checked) =>
                            setAgsByName((previous) => ({ ...previous, [header.saveName]: checked === true }))
                          }
                        />
                        <Label htmlFor={`ags-${header.saveName}`} className="text-xs">
                          AGS
                        </Label>
                      </div>
                      <ConfirmAction
                        title={`Load ${header.saveName}?`}
                        description="The game API is unavailable while the save loads."
                        confirmLabel="Load"
                        onConfirm={() => run(() => api.loadGame(header.saveName, ags), reload)}
                      >
                        <Button variant="outline" size="sm" disabled={pending}>
                          <FolderOpenIcon />
                          Load
                        </Button>
                      </ConfirmAction>
                      <Button variant="ghost" size="sm" asChild>
                        <a href={api.downloadUrl(header.saveName)}>
                          <DownloadIcon />
                          Download
                        </a>
                      </Button>
                      <ConfirmAction
                        title={`Delete save ${header.saveName}?`}
                        confirmLabel="Delete"
                        destructive
                        onConfirm={() => run(() => api.deleteSaveFile(header.saveName), reload)}
                      >
                        <Button variant="ghost" size="sm" disabled={pending}>
                          <Trash2Icon />
                          Delete
                        </Button>
                      </ConfirmAction>
                    </div>
                  </TableCell>
                </TableRow>
              )
            })}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  )
}

export function SavesPage() {
  const { data, loading, reload } = usePoll(api.saves, 10000)

  if (loading && !data) {
    return (
      <div className="flex flex-col gap-4 px-4 lg:px-6">
        <Skeleton className="h-48 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    )
  }
  if (!data) return null

  return (
    <div className="flex flex-col gap-4 px-4 lg:px-6 md:gap-6">
      {data.api_error ? (
        <Alert variant="destructive">
          <AlertTitle>Game API: {data.api_error}</AlertTitle>
          <AlertDescription>The server may be offline or loading a save.</AlertDescription>
        </Alert>
      ) : null}

      <div className="grid grid-cols-1 gap-4 @3xl/main:grid-cols-2">
        <SaveNowCard isPlaying={data.is_playing} reload={reload} />
        <AutoLoadCard
          sessions={data.sessions}
          current={data.game_state?.auto_load_session ?? ""}
          reload={reload}
        />
        <UploadCard reload={reload} />
        <NewGameCard reload={reload} />
      </div>

      {data.sessions.map((session, index) => (
        <SessionCard
          key={session.sessionName}
          session={session}
          loaded={index === data.current_index}
          reload={reload}
        />
      ))}

      {data.sessions.length === 0 && !data.api_error ? (
        <p className="text-sm text-muted-foreground">No save sessions found on the server.</p>
      ) : null}
    </div>
  )
}
