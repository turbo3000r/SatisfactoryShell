/**
 * Client for the Satisfactory Shell JSON API (`/api/*`, session-cookie auth).
 * Endpoint shapes are defined in `src/satisfactory_shell/app.py`.
 */

export type ProcessInfo = {
  running: boolean
  pid: number | null
  owned: boolean
  started_at: number | null
  uptime_seconds: number
  last_exit_code: number | null
  last_unexpected_exit: string | null
  unexpected_exits: number
  user_stopped: boolean
  auto_restart: boolean
  busy: string | null
}

export type GameState = {
  session_name: string
  players: number
  player_limit: number
  tech_tier: number
  game_phase: string
  active_schematic: string
  is_running: boolean
  is_paused: boolean
  duration_seconds: number
  tick_rate: number
  auto_load_session: string
}

export type LightweightState = {
  state: number
  state_name: string
  changelist: number
  modded: boolean
  server_name: string
}

export type Runtime = {
  app_version: string
  mode: string
  python: string
  platform: string
  uptime: number
  bind: string
  config: string
  server_root: string
  steamcmd: string
  game_api: string
}

export type StatusResponse = {
  authed: boolean
  state: { num: number; name: string }
  health: string | null
  api_error: string | null
  lightweight: LightweightState | null
  process: ProcessInfo
  game_state: GameState | null
  bootstrap: { state: string; message: string; ts?: string }
  version: Record<string, string | number>
  manifest: Record<string, string>
  runtime: Runtime
}

export type DashboardResponse = {
  state_name: string
  api_error: string | null
  game_state: GameState | null
  options: Record<string, string>
  pending: Record<string, string>
  process: ProcessInfo
  events: { ts: string; message: string }[]
}

export type MetricsSample = {
  ts: number
  proc_cpu: number | null
  proc_rss_mb: number | null
  host_cpu: number
  host_mem_pct: number
  uptime_s: number
  players: number | null
  tick_rate: number | null
}

export type MetricsResponse = { samples: MetricsSample[]; process: ProcessInfo }

export type SaveHeader = {
  saveName: string
  sessionName: string
  playDuration: number
  saveDateTime: string
  mapName: string
  buildVersion: string
  saveVersion: string
  modded: boolean
  edited: boolean
  creative: boolean
}

export type SaveSession = { sessionName: string; headers: SaveHeader[] }

export type SavesResponse = {
  sessions: SaveSession[]
  current_index: number
  api_error: string | null
  is_playing: boolean
  game_state: GameState | null
}

export type ConsoleEntry = { ts: string; command: string; result: string; error: string }

export type ConsoleResponse = {
  history: ConsoleEntry[]
  log: { text: string; offset: number }
  log_file: string
}

export type TailResponse = { text: string; offset: number; rotated: boolean }

export type UpdateStatus = {
  running: boolean
  phase: string
  started_at: string | null
  finished_at: string | null
  exit_code: number | null
  log_lines: string[]
  available_buildid: string | null
  checked_at: string | null
  check_error: string | null
}

export type UpdatesResponse = {
  installed: { version: Record<string, string | number>; manifest: Record<string, string> }
  status: UpdateStatus
  steamcmd_available: boolean
  steamcmd_path: string
  server_root: string
  local_buildid: string | null
  update_available: boolean
  process: ProcessInfo
  app_id: number
  beta: string
}

export type SessionResponse = { authed: boolean; login_at: string | null; app_version: string }

export type ActionResponse = { ok: boolean; message: string }

export class ApiError extends Error {
  status: number
  code: string

  constructor(status: number, code: string, message: string) {
    super(message)
    this.name = "ApiError"
    this.status = status
    this.code = code
  }
}

let onUnauthorized: () => void = () => {}

/** The auth provider registers here so expired sessions bounce back to /login. */
export function setUnauthorizedHandler(handler: () => void) {
  onUnauthorized = handler
}

type RequestOptions = { notifyUnauthorized?: boolean }

async function request<T>(
  path: string,
  init: RequestInit = {},
  { notifyUnauthorized = true }: RequestOptions = {},
): Promise<T> {
  const response = await fetch(`/api${path}`, {
    cache: "no-store",
    credentials: "same-origin",
    ...init,
  })
  const payload = response.status === 204 ? null : await response.json().catch(() => null)

  if (!response.ok) {
    if (response.status === 401 && notifyUnauthorized) onUnauthorized()
    const message =
      payload?.message ?? payload?.detail ?? payload?.error ?? response.statusText ?? "Request failed"
    throw new ApiError(response.status, payload?.error ?? String(response.status), String(message))
  }
  return payload as T
}

const post = <T,>(path: string, body?: unknown, options?: RequestOptions) =>
  request<T>(
    path,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body ?? {}),
    },
    options,
  )

export const api = {
  session: () => request<SessionResponse>("/session"),
  login: (password: string) => post<{ authed: boolean }>("/login", { password }, { notifyUnauthorized: false }),
  logout: () => post<{ authed: boolean }>("/logout"),

  status: () => request<StatusResponse>("/status"),
  dashboard: () => request<DashboardResponse>("/dashboard"),
  metrics: () => request<MetricsResponse>("/metrics"),

  /** Allowed without a game-API login: logging in is impossible while the server is down. */
  startServer: () => post<ActionResponse>("/start"),
  processAction: (action: "start" | "stop" | "restart" | "toggle-auto-restart") =>
    post<ActionResponse>(`/process/${action}`),

  saves: () => request<SavesResponse>("/saves"),
  saveGame: (saveName: string) => post<ActionResponse>("/saves/save", { save_name: saveName }),
  loadGame: (saveName: string, ags: boolean) => post<ActionResponse>("/saves/load", { save_name: saveName, ags }),
  newGame: (input: { session_name: string; map_name?: string; starting_location?: string }) =>
    post<ActionResponse>("/saves/new", input),
  setAutoLoad: (sessionName: string) => post<ActionResponse>("/saves/autoload", { session_name: sessionName }),
  deleteSaveFile: (saveName: string) => post<ActionResponse>("/saves/delete-file", { save_name: saveName }),
  deleteSaveSession: (sessionName: string) =>
    post<ActionResponse>("/saves/delete-session", { session_name: sessionName }),
  uploadSave: (input: { file: File; saveName: string; load: boolean; ags: boolean }) => {
    const form = new FormData()
    form.append("file", input.file)
    form.append("save_name", input.saveName)
    form.append("load", String(input.load))
    form.append("ags", String(input.ags))
    return request<ActionResponse>("/saves/upload", { method: "POST", body: form })
  },
  downloadUrl: (saveName: string) => `/api/saves/download?save_name=${encodeURIComponent(saveName)}`,

  console: () => request<ConsoleResponse>("/console"),
  runCommand: (command: string) => post<{ history: ConsoleEntry[] }>("/console/run", { command }),
  tail: (offset: number) => request<TailResponse>(`/console/tail?offset=${offset}`),

  updates: () => request<UpdatesResponse>("/updates"),
  checkUpdate: () => post<ActionResponse>("/updates/check"),
  runUpdate: () => post<ActionResponse>("/updates/run"),
}
