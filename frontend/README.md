# Satisfactory Shell — Frontend

Vite + React + TypeScript SPA, styled with Tailwind CSS and [shadcn/ui](https://ui.shadcn.com).

It replaces the server-rendered Jinja2/HTMX templates in
`../src/satisfactory_shell/templates` and talks to the JSON API under `/api`
(defined at the bottom of `../src/satisfactory_shell/app.py`). Auth is the same
session cookie the old pages used, so `/login` works unchanged.

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
      metrics-charts.tsx  # the four old Chart.js canvases as one tabbed card
      stat-list.tsx, state-badges.tsx, confirm-action.tsx, log-view.tsx
    pages/                # one file per route
    hooks/                # use-poll (replaces hx-trigger), use-action (toasts)
    lib/api.ts            # typed client for every /api endpoint
```

## Pages and the API they use

| Route | Replaces | Endpoints |
| --- | --- | --- |
| `/` | `home.html` | `GET /api/status`, `POST /api/start` |
| `/dashboard` | `dashboard.html` | `GET /api/dashboard`, `GET /api/metrics`, `POST /api/process/{action}` |
| `/saves` | `saves.html` | `GET /api/saves`, `POST /api/saves/*`, `GET /api/saves/download` |
| `/console` | `console.html` | `GET /api/console`, `POST /api/console/run`, `GET /api/console/tail` |
| `/updates` | `updates.html` | `GET /api/updates`, `POST /api/updates/check`, `POST /api/updates/run` |
| `/login` | `login.html` | `GET /api/session`, `POST /api/login`, `POST /api/logout` |

## Develop

```powershell
cd frontend
npm install
npm run dev      # http://localhost:5173, proxies /api to http://127.0.0.1:8080
```

Run the backend alongside it (`poetry run satisfactory-shell`); `vite.config.ts`
proxies `/api/*` to `webui.port` (8080 by default).

## Add shadcn/ui components or blocks

Use the shadcn MCP server (configured in `.cursor/mcp.json`) or the CLI:

```powershell
npx shadcn@latest add <component-or-block-name>
```

## Build

```powershell
npm run build     # outputs to frontend/dist (gitignored)
```

The build output is not committed. Once the backend serves the SPA, wire a build
step that copies `frontend/dist` into `src/satisfactory_shell/static/`.
