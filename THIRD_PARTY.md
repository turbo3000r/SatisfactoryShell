# Third-party software

Satisfactory Shell is licensed under the BSD 3-Clause License (see `LICENSE`).
That license covers **this project’s own source and binaries only**. Other
software you use with it keeps its own terms.

## Bundled in this repository

These files are copied into the WebUI and into the frozen exe:

| Component | Version (approx.) | License | Location |
| --- | --- | --- | --- |
| [htmx](https://htmx.org/) | 2.0.4 | BSD 2-Clause | `src/satisfactory_shell/static/htmx.min.js` |
| [Chart.js](https://www.chartjs.org/) | 4.4.7 | MIT | `src/satisfactory_shell/static/chart.umd.js` |

Keep those notices when you redistribute the project or a built exe.

## Python runtime (not vendored)

Installed by Poetry / pip when you run from source. Typical SPDX identifiers:

| Package | License |
| --- | --- |
| FastAPI | MIT |
| Uvicorn | BSD 3-Clause |
| Jinja2 | BSD 3-Clause |
| python-multipart | Apache-2.0 |
| itsdangerous | BSD 3-Clause |
| psutil | BSD 3-Clause |
| httpx | BSD 3-Clause |

Exact versions are in `poetry.lock`. Each package ships its own license files
inside the virtualenv or wheel.

## Used to build, not shipped as source

| Tool | Role | License |
| --- | --- | --- |
| [PyInstaller](https://pyinstaller.org/) | `poetry run build-exe` | GPL-2.0-or-later with the Bootloader exception (the frozen app is not required to be GPL) |
| [Inno Setup](https://jrsoftware.org/isinfo.php) | Windows installer | Inno Setup license |

## Downloaded or pointed at; not part of this project

Satisfactory Shell can start, update, or talk to these. It does **not** grant
rights to them and must not be treated as redistributing them:

| Software | Owner | Notes |
| --- | --- | --- |
| Satisfactory Dedicated Server (`FactoryServer.exe`) | Coffee Stain / Epic | Steam / Coffee Stain EULA. Not included in this repo. |
| [SteamCMD](https://developer.valvesoftware.com/wiki/SteamCMD) | Valve | Valve terms. Optional installer download into `{app}\steamcmd`. |

Do not bundle `FactoryServer.exe` or the dedicated-server content into a
Satisfactory Shell release unless Coffee Stain / Valve allow it.
