# Satisfactory Shell — Frontend

Vite + React + TypeScript SPA, styled with Tailwind CSS and [shadcn/ui](https://ui.shadcn.com).

This will replace the current server-rendered Jinja2/HTMX templates in
`../src/satisfactory_shell/templates`. During the migration the FastAPI
backend needs to expose JSON endpoints (it currently returns HTML) for the
pages under `src/pages/` to consume.

## Layout

```
frontend/
  src/
    components/
      ui/            # shadcn primitives (button, card, table, sidebar, ...)
      app-sidebar.tsx, nav-main.tsx, nav-user.tsx, site-header.tsx
    pages/           # one file per route: home, dashboard, saves, console, updates
    App.tsx          # shell layout (sidebar + header) and route table
    main.tsx         # React Router + app entry point
  components.json     # shadcn/ui configuration (registries, aliases, style)
```

## Develop

```powershell
cd frontend
npm install
npm run dev      # http://localhost:5173, proxies /api to http://127.0.0.1:8000
```

Run the FastAPI backend separately (`poetry run satisfactory-shell`) while
developing; `vite.config.ts` proxies `/api/*` requests to it.

## Add shadcn/ui components or blocks

Use the shadcn MCP server (configured in `.cursor/mcp.json`) or the CLI directly:

```powershell
npx shadcn@latest add <component-or-block-name>
```

## Build

```powershell
npm run build     # outputs to frontend/dist (gitignored)
```

The build output is not committed. Once the backend serves the SPA, wire a
build step to copy `frontend/dist` into `src/satisfactory_shell/static/`.
