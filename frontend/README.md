# Satisfactory Shell — Frontend

Vite + React + TypeScript SPA, styled with Tailwind CSS and [shadcn/ui](https://ui.shadcn.com).

It is the only WebUI. FastAPI serves the production build (`frontend/dist` from source, or `webui/` next to the frozen exe) and the JSON API under `/api` (defined in `../src/satisfactory_shell/app.py`). Auth is a session cookie; `/login` talks to `POST /api/login`.

## Layout

```
frontend/
  src/
    components/
      ui/                 # shadcn primitives (card, table, sidebar, chart, ...)
      app-sidebar.tsx     # nav: Home / Dashboard / Saves / Console / Updates
      site-header.tsx     # page title, theme toggle, login/logout
      auth-provider.tsx   # session state, 401 handling
      theme-provider.tsx  # light/dark/system, persisted in localStorage
      metrics-charts.tsx  # CPU / RAM / ping / tick-rate charts
      stat-list.tsx, state-badges.tsx, confirm-action.tsx, log-view.tsx
    pages/                # one file per route
    hooks/                # use-poll, use-action (toasts)
    lib/api.ts            # typed client for every /api endpoint
```

## Pages and the API they use

| Route | Endpoints |
| --- | --- |
| `/` | `GET /api/status`, `POST /api/start` |
| `/dashboard` | `GET /api/dashboard`, `GET /api/metrics`, `POST /api/process/{action}` |
| `/saves` | `GET /api/saves`, `POST /api/saves/*`, `GET /api/saves/download` |
| `/console` | `GET /api/console`, `POST /api/console/run`, `GET /api/console/tail` |
| `/updates` | `GET /api/updates`, `POST /api/updates/check`, `POST /api/updates/run` |
| `/login` | `GET /api/session`, `POST /api/login`, `POST /api/logout` |

## Develop

```powershell
cd frontend
npm install
npm run dev      # http://localhost:5173, proxies /api to http://127.0.0.1:8080
```

Run the backend alongside it (`poetry run satisfactory-shell`); `vite.config.ts`
proxies `/api/*` to `webui.port` (8080 by default). The backend still needs a
production SPA build (`npm run build`) if you open `:8080` directly.

## Add shadcn/ui components or blocks

Use the shadcn MCP server (configured in `.cursor/mcp.json`) or the CLI:

```powershell
npx shadcn@latest add <component-or-block-name>
```

## Build

```powershell
npm run build     # outputs to frontend/dist (gitignored)
```

The build output is not committed. `poetry run satisfactory-shell` serves
`frontend/dist`. `poetry run build-exe` runs this build and copies the files to
`dist/webui/` next to `satisfactory-shell.exe`. The installer ships that folder
as `{app}\webui`.
