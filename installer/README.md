# Building the Windows installer

Requires [Inno Setup 6](https://jrsoftware.org/isinfo.php) (6.2+ recommended: `DownloadTemporaryFile`, `GetSpaceOnDisk64`).

## 1. Freeze Satisfactory Shell

From `SatisfactoryShell/`:

```powershell
poetry install --with dev
poetry run build-exe
```

This writes `dist/satisfactory-shell.exe`. The `.iss` script ships that file only.

## 2. Optional: vendor SteamCMD into the installer

```powershell
powershell -File installer/fetch-steamcmd.ps1
```

That downloads Valve's zip to `installer/redist/steamcmd.zip` (~2–3 MB). If you skip this, setup downloads the same URL during install (`https://steamcdn-a.akamaihd.net/client/installer/steamcmd.zip`).

Do **not** bundle `FactoryServer.exe` or the ~15 GB dedicated server. Those are fetched at install time on the "download" path via:

```
steamcmd +force_install_dir {app}\server +login anonymous +app_update 1690800 validate +quit
```

## 3. Compile

Open `installer/satisfactory-shell.iss` in Inno Setup and Build, or:

```powershell
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\satisfactory-shell.iss
```

Output: `dist/SatisfactoryShell-Setup-0.1.0.exe`.

## What the wizard does

### Fresh install (no previous version detected)

Two independent checkboxes: **Install SteamCMD** and **Install the dedicated server**. Unchecked items get a following page to pick an existing `steamcmd.exe` or `FactoryServer.exe` folder.

| SteamCMD | Server | After copy |
| --- | --- | --- |
| checked | checked | SteamCMD zip + ~15 GB `app_update` into `{app}\steamcmd` and `{app}\server`; write `bootstrap.json` |
| checked | unchecked | SteamCMD into `{app}\steamcmd`; you pick an existing server folder |
| unchecked | checked | You pick existing `steamcmd.exe`; it downloads the DS into `{app}\server`; write `bootstrap.json` |
| unchecked | unchecked | You pick both existing paths; `config.json` only (no claim) |

### Upgrade / repair (previous version detected)

The installer detects existing installations via the Uninstall registry key (`HKLM` or `HKCU`). It checks the installed version and which bundled components exist (`steamcmd\steamcmd.exe`, `server\FactoryServer.exe`).

**Same version detected — two options:**

| Mode | What it does |
| --- | --- |
| **Repair** | Re-copies the binary (always). Three checkboxes: binary (locked on), SteamCMD (if bundled), dedicated server (if bundled). Checked components are re-installed/re-downloaded. `config.json` is **not** modified. |
| **Install additional components** | Shown only if at least one component is missing. Checkboxes for adding bundled SteamCMD and/or dedicated server. Only the new component paths are patched into `config.json`; all other settings are preserved. Adding a server shows a claim page (server name, admin password, client password) and writes `bootstrap.json`. |

**Lower version detected — two options:**

| Mode | What it does |
| --- | --- |
| **Upgrade** | Updates the binary and bundled SteamCMD (if applicable). `config.json` is **not** modified; the application handles any new keys with runtime defaults. |
| **Upgrade and modify** | Updates the binary and shows the full wizard (SteamCMD/server checkboxes, ports, passwords). `config.json` is rewritten. SourcePage checkboxes are pre-filled based on the current install state. |

### Config handling summary

| Mode | `config.json` | `bootstrap.json` |
| --- | --- | --- |
| Fresh install | Written from scratch | Written if installing server |
| Repair | Preserved | Not touched |
| Add components | Paths patched in-place | Written if adding server |
| Upgrade | Preserved | Not touched |
| Upgrade and modify | Rewritten | Written if installing server |

`{app}` (default `C:\Program Files\SatisfactoryShell`) gets **Users Modify** so later SteamCMD updates work without an elevated WebUI.

Config and logs live in `%APPDATA%\SatisfactoryShell\`. The Start Menu shortcut runs `satisfactory-shell.exe --bootstrap`. If `bootstrap.json` is present, the shell starts the DS and calls `ClaimServer` when HTTPS is up, then deletes the file. Admin password is never written to `config.json`.

Uninstall removes `{app}` (including a downloaded `server\` folder). It asks before deleting AppData. It does not delete a dedicated server you pointed at outside `{app}`.
