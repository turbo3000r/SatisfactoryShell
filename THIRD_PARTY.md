# Third-party software

Satisfactory Shell is licensed under the BSD 3-Clause License (see `LICENSE`).
That license covers **this project’s own source and binaries only**. Other
software you use with it keeps its own terms.

## WebUI (built at freeze time)

The React SPA in `frontend/` is compiled by Vite (`npm run build`) into
`dist/webui/` (or `frontend/dist` when running from source). Those generated
files are shipped next to the frozen binary / Windows installer / Linux tarball;
the npm packages themselves are not vendored as source. Licenses for React, Vite,
Tailwind, shadcn/ui, and other frontend dependencies are in `frontend/node_modules`
(see `frontend/package.json` and `frontend/package-lock.json`).

Keep those notices when you redistribute the project, a built binary, the
Windows installer, or the Linux tarball.

## Python runtime (not vendored)

Installed by Poetry / pip when you run from source. Typical SPDX identifiers:

| Package | License |
| --- | --- |
| FastAPI | MIT |
| Uvicorn | BSD 3-Clause |
| python-multipart | Apache-2.0 |
| itsdangerous | BSD 3-Clause |
| psutil | BSD 3-Clause |
| httpx | BSD 3-Clause |

Exact versions are in `poetry.lock`. Each package ships its own license files
inside the virtualenv or wheel.

## Used to build, not shipped as source

| Tool | Role | License |
| --- | --- | --- |
| [Node.js](https://nodejs.org/) / npm | `npm run build` for the WebUI | various |
| [Vite](https://vite.dev/) | Frontend bundler | MIT |
| [PyInstaller](https://pyinstaller.org/) | `poetry run build-exe` | GPL-2.0-or-later with the Bootloader exception (the frozen app is not required to be GPL) |
| [Inno Setup](https://jrsoftware.org/isinfo.php) | Windows installer | Inno Setup license |

## Downloaded or pointed at; not part of this project

Satisfactory Shell can start, update, or talk to these. It does **not** grant
rights to them and must not be treated as redistributing them:

| Software | Owner | Notes |
| --- | --- | --- |
| Satisfactory Dedicated Server (`FactoryServer.exe` / Linux shipping binary) | Coffee Stain / Epic | Steam / Coffee Stain EULA. Not included in this repo. |
| [SteamCMD](https://developer.valvesoftware.com/wiki/SteamCMD) | Valve | Valve terms. Optional Windows-installer download into `{app}\steamcmd`. |

Do not bundle the dedicated-server content into a Satisfactory Shell release
unless Coffee Stain / Valve allow it.
