"""Path resolution that works both from source and from a PyInstaller one-file binary."""

from __future__ import annotations

import os
import sys
from pathlib import Path

APPDATA_APP = "SatisfactoryShell"
LEGACY_APPDATA_APP = "SatisfactoryCoating"


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def _package_dir() -> Path:
    """Directory of the ``satisfactory_shell`` package (not a subpackage)."""
    here = Path(__file__).resolve().parent
    while here.name != "satisfactory_shell" and here.parent != here:
        here = here.parent
    return here


def starter_root() -> Path:
    """Directory of the exe when frozen, otherwise the project root (``SatisfactoryShell/``)."""
    if is_frozen():
        return Path(sys.executable).resolve().parent
    # src/satisfactory_shell -> SatisfactoryShell/
    return _package_dir().parent.parent


def user_config_dir() -> Path:
    """``%APPDATA%\\SatisfactoryShell`` on Windows, else the starter root.

    If the new folder does not exist yet and the former ``SatisfactoryCoating``
    AppData directory does, keep using the old one so existing installs still
    find config and bootstrap files.
    """
    appdata = os.environ.get("APPDATA")
    if not appdata:
        return starter_root()
    new = Path(appdata) / APPDATA_APP
    old = Path(appdata) / LEGACY_APPDATA_APP
    if new.exists() or not old.is_dir():
        return new
    return old


def user_data_dir() -> Path:
    return user_config_dir() / "data"


def bootstrap_file() -> Path:
    return user_config_dir() / "bootstrap.json"


def webui_dir() -> Path:
    """Vite build output: ``webui/`` next to the exe, or ``frontend/dist`` from source."""
    if is_frozen():
        return starter_root() / "webui"
    return starter_root() / "frontend" / "dist"


def find_server_root(start: Path) -> Path | None:
    """Walk up from ``start`` until a directory containing FactoryServer.exe is found."""
    for candidate in [start, *start.parents]:
        if (candidate / "FactoryServer.exe").is_file():
            return candidate
    return None


def find_appmanifest(server_root: Path, app_id: int) -> Path | None:
    """Steam library layout: steamapps/common/<install>/ -> steamapps/appmanifest_<id>.acf."""
    candidate = server_root.parent.parent / f"appmanifest_{app_id}.acf"
    return candidate if candidate.is_file() else None
