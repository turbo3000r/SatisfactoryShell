# Satisfactory Shell

Process manager, metrics, SteamCMD updater, and WebUI for the Satisfactory Dedicated Server.

**0.2.1** adds Linux support: the same WebUI and process manager, a portable `satisfactory-shell` + `webui/` layout, a systemd unit, and `scripts/install.sh`. Windows still uses the Inno Setup wizard. See [CHANGELOG.md](CHANGELOG.md).

## Install (Windows)

Build or download `SatisfactoryShell-Setup-0.2.1.exe` (see [`installer/README.md`](installer/README.md)). The wizard can install SteamCMD and the dedicated server, or point at copies you already have.

Config and logs go under `%APPDATA%\SatisfactoryShell\`. After setup, the Start Menu shortcut starts the shell; open **http://127.0.0.1:8080**.

Home needs no login. Dashboard, Saves, Console, and Updates use the Satisfactory **admin** password.

## Install (Linux)

Installs the shell only. Point `paths.server_root` and `paths.steamcmd` at a Linux dedicated server and SteamCMD you already have (Steam app `1690800`).

One-liner after a GitHub Release exists:

```bash
curl -fsSL https://github.com/turbo3000r/SatisfactoryShell/releases/latest/download/install.sh | sudo bash
```

Or from a tarball you built or downloaded:

```bash
sudo ./scripts/install.sh dist/satisfactory-shell-0.2.1-linux-x64.tar.gz
```

That copies the binary and `webui/` to `/opt/satisfactory-shell`, writes a systemd unit as the sudo-invoking user, and runs `systemctl enable --now satisfactory-shell`. Open **http://127.0.0.1:8080**.

Config and logs go under `~/.config/satisfactory-shell/` (or `$XDG_CONFIG_HOME/satisfactory-shell/`). The unit does not download SteamCMD or the dedicated server.

Build the tarball on Linux or WSL (`./scripts/pack-linux.sh`), or use the [Linux release](.github/workflows/linux-release.yml) workflow on a `v*` tag.

## Portable layout

Windows:

```
satisfactory-shell.exe
webui\                 # required; the binary serves this folder
config.json            # optional if you use AppData config
```

Linux:

```
satisfactory-shell
webui/                 # required; the binary serves this folder
satisfactory-shell.service
install.sh
```

`poetry run build-exe` writes the binary and `webui/` under `dist/`. On Linux, `./scripts/pack-linux.sh` adds the unit and install script to `dist/satisfactory-shell-<version>-linux-x64.tar.gz`. Put the binary and `webui/` together inside a server install, or set `paths.server_root`.

## Run from source

Needs Python 3.11+ (Poetry) and [Node.js](https://nodejs.org/) (to build the WebUI).

```powershell
cd SatisfactoryShell
poetry install --with dev
cd frontend; npm install; npm run build; cd ..
poetry run satisfactory-shell            # or: poetry run python -m satisfactory_shell
```

```bash
cd SatisfactoryShell
poetry install --with dev
(cd frontend && npm install && npm run build)
poetry run satisfactory-shell
```

Open `http://127.0.0.1:8080`. The dedicated server is started automatically (`process.auto_start`).

While iterating on the UI, run `npm run dev` in `frontend/` (http://localhost:5173) alongside the backend; Vite proxies `/api` to port 8080. A production `npm run build` is still required if you open `:8080` directly. Details: [`frontend/README.md`](frontend/README.md).

Flags: `--host`, `--port`, `--no-auto-start`, `--log-level debug`.

## Config

Search order: `SATISFACTORY_SHELL_CONFIG` (legacy: `COATING_CONFIG`) → the user config directory `config.json` → `config.json` next to the binary / project root.

User config directory:

- Windows: `%APPDATA%\SatisfactoryShell\`. If only the former `%APPDATA%\SatisfactoryCoating\` folder exists, that is used until you create the new one.
- Linux / macOS: `$XDG_CONFIG_HOME/satisfactory-shell/` or `~/.config/satisfactory-shell/`.

Logs and SteamCMD output go to `<config-dir>/data/`. Copy [`config.example.json`](config.example.json) to pre-seed.

Empty path strings mean "relative to the starter root":

| Key | Default resolution |
| --- | --- |
| `paths.server_root` | Walk up from the starter until a dedicated-server launcher is found (`FactoryServer-Linux-Shipping`, `FactoryServer.sh`, or `FactoryServer.exe`) |
| `paths.steamcmd` | `steamcmd` / `steamcmd.sh` / `steamcmd.exe` on `PATH`, else `<starter>/steamcmd/<that name>` |
| `paths.appmanifest` | `<server_root>/../../appmanifest_<app_id>.acf` (Steam library layout) |

`game.port` is the game/HTTPS-API port (`-Port=`), `game.reliable_port` is `-ReliablePort=`.

`webui.host` defaults to `127.0.0.1`; set `0.0.0.0` for LAN access.

`process.auto_start` (default `true`) launches the dedicated server when Satisfactory Shell starts. Set it `false` if you only want the WebUI.

`game.client_password` is the Satisfactory **client protection** password. The shell uses it for `PasswordLogin` at `Client` privilege so Home and metrics can call `QueryServerState` without an admin session. Leave it empty to skip that. The WebUI login page still uses the **admin** password.

The default `extra_args` also include `-ini:Engine:[SystemSettings]:FG.DedicatedServer.AllowInsecureLocalAccess=1` (loopback-only API without a token). Restart the dedicated server after changing that flag.

## Build a release

Needs Poetry and Node.js. Windows installer builds also need [Inno Setup 6](https://jrsoftware.org/isinfo.php). Linux tarballs must be built **on Linux** (or in the GitHub Actions workflow).

Windows:

```powershell
poetry install --with dev
poetry run build-exe
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\satisfactory-shell.iss
```

Output: `dist/satisfactory-shell.exe`, `dist/webui/`, and `dist/SatisfactoryShell-Setup-0.2.1.exe`. Full installer notes: [`installer/README.md`](installer/README.md).

Linux:

```bash
poetry install --with dev
./scripts/pack-linux.sh
```

Output: `dist/satisfactory-shell`, `dist/webui/`, and `dist/satisfactory-shell-0.2.1-linux-x64.tar.gz`. Tag `v0.2.1` to have [`.github/workflows/linux-release.yml`](.github/workflows/linux-release.yml) attach that archive and `scripts/install.sh` to the GitHub Release.

## Updating the dedicated server

The Updates page runs `steamcmd +force_install_dir <server_root> +login anonymous +app_update <app_id> [validate] +quit` after stopping the server. If the install lives in a Steam library and the Steam client is running, SteamCMD may fail with `0x606`; close Steam first.

## License

Satisfactory Shell is © 2026 [turbo3000r](https://github.com/turbo3000r), licensed under the [BSD 3-Clause License](LICENSE). You may use, modify, and redistribute it. Redistributions must keep the copyright notice and credit **turbo3000r** as the author.

Third-party libraries (FastAPI, React, Vite, and others) and Coffee Stain / Valve software stay under their own licenses. See [THIRD_PARTY.md](THIRD_PARTY.md).
