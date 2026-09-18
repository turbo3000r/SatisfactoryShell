"""Path resolution that works both from source and from a PyInstaller one-file binary."""

from __future__ import annotations

import sys
from pathlib import Path

from . import platform as plat

APPDATA_APP = plat.APPDATA_APP
LEGACY_APPDATA_APP = plat.LEGACY_APPDATA_APP


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
    """``%APPDATA%\\SatisfactoryShell`` on Windows; XDG config on Linux/macOS.

    If the new Windows folder does not exist yet and the former
    ``SatisfactoryCoating`` AppData directory does, keep using the old one so
    existing installs still find config and bootstrap files.
    """
    return plat.user_config_dir(windows_fallback=starter_root())


def user_data_dir() -> Path:
    return user_config_dir() / "data"


def bootstrap_file() -> Path:
    return user_config_dir() / "bootstrap.json"


def webui_dir() -> Path:
    """Vite build output: ``webui/`` next to the binary, or ``frontend/dist`` from source."""
    if is_frozen():
        return starter_root() / "webui"
    return starter_root() / "frontend" / "dist"


def find_server_root(start: Path) -> Path | None:
    """Walk up from ``start`` until a dedicated-server launcher is found."""
    return plat.find_server_root(start)


def find_appmanifest(server_root: Path, app_id: int) -> Path | None:
    """Steam library layout: steamapps/common/<install>/ -> steamapps/appmanifest_<id>.acf."""
    candidate = server_root.parent.parent / f"appmanifest_{app_id}.acf"
    return candidate if candidate.is_file() else None
