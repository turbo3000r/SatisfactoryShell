# Changelog

## 0.2.0

- New React WebUI (Vite + TypeScript + shadcn/ui). The Jinja2/HTMX pages are removed.
- FastAPI serves the SPA from `webui/` next to the exe (or `frontend/dist` when running from source) and a JSON API under `/api`.
- `poetry run build-exe` builds the frontend and stages `dist/webui/` beside `satisfactory-shell.exe`. Node.js is required on the build machine.
- The Windows installer ships that `webui/` folder, replaces it on upgrade/repair, and removes it on uninstall.

## 0.1.0

- First public release: process manager, metrics, SteamCMD updates, and the HTML/HTMX WebUI.
