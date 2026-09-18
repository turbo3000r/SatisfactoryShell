# Satisfactory Shell

Process manager, metrics, SteamCMD updater, and WebUI for the Satisfactory Dedicated Server.

**0.2.0** replaces the old HTML/HTMX pages with a React WebUI. The Windows installer and the portable layout both ship `satisfactory-shell.exe` plus a `webui/` folder next to it. Keep those two together. See [CHANGELOG.md](CHANGELOG.md).

## Install (Windows)

Build or download `SatisfactoryShell-Setup-0.2.0.exe` (see [`installer/README.md`](installer/README.md)). The wizard can install SteamCMD and the dedicated server, or point at copies you already have.

Config and logs go under `%APPDATA%\SatisfactoryShell\`. After setup, the Start Menu shortcut starts the shell; open **http://127.0.0.1:8080**.

Home needs no login. Dashboard, Saves, Console, and Updates use the Satisfactory **admin** password.

## Portable layout

```
satisfactory-shell.exe
webui\                 # required; the exe serves this folder
config.json            # optional if you use AppData config
```

`poetry run build-exe` writes that pair under `dist/`. Put them anywhere inside a server install, or set `paths.server_root`.

## Run from source

Needs Python 3.11+ (Poetry) and [Node.js](https://nodejs.org/) (to build the WebUI).

```powershell
cd SatisfactoryShell
poetry install --with dev
cd frontend; npm install; npm run build; cd ..
poetry run satisfactory-shell            # or: poetry run python -m satisfactory_shell
```

Open `http://127.0.0.1:8080`. The dedicated server is started automatically (`process.auto_start`).

While iterating on the UI, run `npm run dev` in `frontend/` (http://localhost:5173) alongside the backend; Vite proxies `/api` to port 8080. A production `npm run build` is still required if you open `:8080` directly. Details: [`frontend/README.md`](frontend/README.md).

Flags: `--host`, `--port`, `--no-auto-start`, `--log-level debug`.

## Config

Search order: `SATISFACTORY_SHELL_CONFIG` (legacy: `COATING_CONFIG`) → `%APPDATA%\SatisfactoryShell\config.json` → `config.json` next to the exe / project root. If only the former `%APPDATA%\SatisfactoryCoating\` folder exists, that is used until you create the new one. Logs and SteamCMD output go to `%APPDATA%\SatisfactoryShell\data\`. Copy [`config.example.json`](config.example.json) to pre-seed.

Empty path strings mean "relative to the starter root":

| Key | Default resolution |
| --- | --- |
| `paths.server_root` | Walk up from the starter until `FactoryServer.exe` is found |
| `paths.steamcmd` | `steamcmd` on `PATH`, else `<starter>/steamcmd/steamcmd.exe` |
| `paths.appmanifest` | `<server_root>/../../appmanifest_<app_id>.acf` (Steam library layout) |

`game.port` is the game/HTTPS-API port (`-Port=`), `game.reliable_port` is `-ReliablePort=`.

`webui.host` defaults to `127.0.0.1`; set `0.0.0.0` for LAN access.

`process.auto_start` (default `true`) launches `FactoryServer.exe` when Satisfactory Shell starts. Set it `false` if you only want the WebUI.

`game.client_password` is the Satisfactory **client protection** password. The shell uses it for `PasswordLogin` at `Client` privilege so Home and metrics can call `QueryServerState` without an admin session. Leave it empty to skip that. The WebUI login page still uses the **admin** password.

The default `extra_args` also include `-ini:Engine:[SystemSettings]:FG.DedicatedServer.AllowInsecureLocalAccess=1` (loopback-only API without a token). Restart the dedicated server after changing that flag.

## Build a release

Needs Poetry, Node.js, and [Inno Setup 6](https://jrsoftware.org/isinfo.php) for the installer.

```powershell
poetry install --with dev
poetry run build-exe
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\satisfactory-shell.iss
```

Output: `dist/satisfactory-shell.exe`, `dist/webui/`, and `dist/SatisfactoryShell-Setup-0.2.0.exe`. Full installer notes: [`installer/README.md`](installer/README.md).

## Updating the dedicated server

The Updates page runs `steamcmd +force_install_dir <server_root> +login anonymous +app_update <app_id> [validate] +quit` after stopping the server. If the install lives in a Steam library and the Steam client is running, SteamCMD may fail with `0x606`; close Steam first.

## License

Satisfactory Shell is © 2026 [turbo3000r](https://github.com/turbo3000r), licensed under the [BSD 3-Clause License](LICENSE). You may use, modify, and redistribute it. Redistributions must keep the copyright notice and credit **turbo3000r** as the author.

Third-party libraries (FastAPI, React, Vite, and others) and Coffee Stain / Valve software stay under their own licenses. See [THIRD_PARTY.md](THIRD_PARTY.md).
