# Changelog

## 0.2.1

- Linux: detect the dedicated server and SteamCMD by files that exist (`FactoryServer-Linux-Shipping` / `FactoryServer.sh` / `FactoryServer.exe`, `steamcmd` / `steamcmd.sh` / `steamcmd.exe`).
- Linux: config and logs use `$XDG_CONFIG_HOME/satisfactory-shell` or `~/.config/satisfactory-shell`.
- Linux portable tarball (`scripts/pack-linux.sh`): frozen `satisfactory-shell`, `webui/`, systemd unit, and `install.sh`.
- `scripts/install.sh` installs to `/opt/satisfactory-shell` and enables a systemd unit. It does not download SteamCMD or the dedicated server.
- GitHub Actions workflow builds the Linux tarball on `v*` tags (`workflow_dispatch` also uploads an artifact).
- `poetry run build-exe` omits `--noconsole` on non-Windows so the daemon can log to the journal.

## 0.2.0

- New React WebUI (Vite + TypeScript + shadcn/ui). The Jinja2/HTMX pages are removed.
- FastAPI serves the SPA from `webui/` next to the exe (or `frontend/dist` when running from source) and a JSON API under `/api`.
- `poetry run build-exe` builds the frontend and stages `dist/webui/` beside `satisfactory-shell.exe`. Node.js is required on the build machine.
- The Windows installer ships that `webui/` folder, replaces it on upgrade/repair, and removes it on uninstall.

## 0.1.0

- First public release: process manager, metrics, SteamCMD updates, and the HTML/HTMX WebUI.
