# Satisfactory Shell

Process manager, metrics, SteamCMD updater and WebUI for the Satisfactory Dedicated Server. Replaces `launch.bat`.

## Project structure

```
SatisfactoryShell/
  src/satisfactory_shell/   # FastAPI backend: process manager, metrics, SteamCMD, WebUI
    templates/, static/     # current server-rendered HTML/HTMX WebUI (being replaced)
  frontend/                 # Vite + React + TypeScript + shadcn/ui WebUI (see frontend/README.md)
  installer/                # Inno Setup Windows installer
  assets/                   # icons and installer images
```

The WebUI is being migrated from server-rendered Jinja2/HTMX templates to the
`frontend/` SPA. Until that migration lands, both exist side by side; see
[`frontend/README.md`](frontend/README.md) for the frontend dev workflow.

## Run from source

```powershell
cd SatisfactoryShell
poetry install --with dev
poetry run satisfactory-shell            # or: poetry run python -m satisfactory_shell
```

Open `http://127.0.0.1:8080`. The server is started automatically (`process.auto_start`).

Flags: `--host`, `--port`, `--no-auto-start`, `--log-level debug`.

A Windows installer (Inno Setup) lives in [`installer/`](installer/README.md). It writes config under `%APPDATA%\SatisfactoryShell\` and can download SteamCMD plus the dedicated server into `{app}\steamcmd` and `{app}\server`.

## Config

Search order: `SATISFACTORY_SHELL_CONFIG` (legacy: `COATING_CONFIG`) → `%APPDATA%\SatisfactoryShell\config.json` → `config.json` next to the starter (this Steam tree / Poetry). If only the former `%APPDATA%\SatisfactoryCoating\` folder exists, that is used until you create the new one. Logs and SteamCMD output go to `%APPDATA%\SatisfactoryShell\data\`. Copy `config.example.json` to pre-seed. This install’s `launch.bat` sets `SATISFACTORY_SHELL_CONFIG` to `SatisfactoryShell\config.json`.

Empty path strings mean "relative to the starter root":

| Key | Default resolution |
| --- | --- |
| `paths.server_root` | Walk up from the starter until `FactoryServer.exe` is found |
| `paths.steamcmd` | `steamcmd` on `PATH`, else `<starter>/steamcmd/steamcmd.exe` |
| `paths.appmanifest` | `<server_root>/../../appmanifest_<app_id>.acf` (Steam library layout) |

`game.port` is the game/HTTPS-API port (`-Port=`), `game.reliable_port` is `-ReliablePort=`.

`webui.host` defaults to `127.0.0.1`; set `0.0.0.0` for LAN access. The Home page needs no login; every other page requires the Satisfactory admin password.

`process.auto_start` (default `true`) launches `FactoryServer.exe` when Satisfactory Shell starts. Set it `false` if you only want the WebUI.

`game.client_password` is the Satisfactory **client protection** password. The shell uses it for `PasswordLogin` at `Client` privilege so Home and metrics can call `QueryServerState` without an admin session. Leave it empty to skip that. The WebUI login page still uses the **admin** password.

The default `extra_args` also include `-ini:Engine:[SystemSettings]:FG.DedicatedServer.AllowInsecureLocalAccess=1` (loopback-only API without a token). Restart the dedicated server after changing that flag.

## Build a single exe

```powershell
poetry run build-exe
```

Output: `dist/satisfactory-shell.exe`. Put it (and `config.json`) anywhere inside the server install, or set `paths.server_root`.

## Updating the server

The Updates page runs `steamcmd +force_install_dir <server_root> +login anonymous +app_update <app_id> [validate] +quit` after stopping the server. If the install lives in a Steam library and the Steam client is running, SteamCMD may fail with `0x606`; close Steam first.

## License

Satisfactory Shell is © 2026 [turbo3000r](https://github.com/turbo3000r), licensed under the [BSD 3-Clause License](LICENSE). You may use, modify, and redistribute it. Redistributions must keep the copyright notice and credit **turbo3000r** as the author.

Third-party libraries (htmx, Chart.js, FastAPI, and others) and Coffee Stain / Valve software stay under their own licenses. See [THIRD_PARTY.md](THIRD_PARTY.md).
