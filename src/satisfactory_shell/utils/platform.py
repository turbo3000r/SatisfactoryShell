"""OS-aware names for the dedicated server, SteamCMD, config, and process spawn.

Detection prefers files that exist so a config can point at a Linux or Windows
server_root regardless of the OS running Satisfactory Shell.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

APPDATA_APP = "SatisfactoryShell"
LEGACY_APPDATA_APP = "SatisfactoryCoating"
XDG_APP = "satisfactory-shell"

# First existing file wins. Shipping binary before the .sh wrapper so Popen
# owns the real process (killing the wrapper can leave the game running).
SERVER_LAUNCHERS: tuple[Path, ...] = (
    Path("Engine") / "Binaries" / "Linux" / "FactoryServer-Linux-Shipping",
    Path("FactoryServer.sh"),
    Path("FactoryServer.exe"),
)

VERSION_FILES: tuple[Path, ...] = (
    Path("Engine") / "Binaries" / "Linux" / "FactoryServer-Linux-Shipping.version",
    Path("Engine") / "Binaries" / "Win64" / "FactoryServer-Win64-Shipping.version",
)

STEAMCMD_NAMES: tuple[str, ...] = ("steamcmd", "steamcmd.sh", "steamcmd.exe")

PROCESS_NAME_PREFIXES: tuple[str, ...] = (
    "factoryserver",
    "factoryserver-linux-shipping",
)


def is_windows() -> bool:
    return sys.platform == "win32"


def server_exe(server_root: Path | None) -> Path | None:
    if server_root is None:
        return None
    for rel in SERVER_LAUNCHERS:
        candidate = server_root / rel
        if candidate.is_file():
            return candidate
    return None


def version_file(server_root: Path | None) -> Path | None:
    if server_root is None:
        return None
    for rel in VERSION_FILES:
        candidate = server_root / rel
        if candidate.is_file():
            return candidate
    return None


def find_server_root(start: Path) -> Path | None:
    """Walk up from ``start`` until a dedicated-server launcher is found."""
    for candidate in [start, *start.parents]:
        if server_exe(candidate) is not None:
            return candidate
    return None


def find_steamcmd(root: Path) -> Path | None:
    for name in STEAMCMD_NAMES:
        found = shutil.which(name)
        if found:
            return Path(found)
    steam_dir = root / "steamcmd"
    for name in STEAMCMD_NAMES:
        candidate = steam_dir / name
        if candidate.is_file():
            return candidate
    return None


def user_config_dir(*, windows_fallback: Path) -> Path:
    """Windows: ``%APPDATA%\\SatisfactoryShell``. Else XDG config home."""
    if is_windows():
        appdata = os.environ.get("APPDATA")
        if not appdata:
            return windows_fallback
        new = Path(appdata) / APPDATA_APP
        old = Path(appdata) / LEGACY_APPDATA_APP
        if new.exists() or not old.is_dir():
            return new
        return old
    xdg = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg) if xdg else Path.home() / ".config"
    return base / XDG_APP


def popen_kwargs() -> dict[str, object]:
    if is_windows():
        flags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) | getattr(
            subprocess, "CREATE_NO_WINDOW", 0
        )
        return {"creationflags": flags}
    return {"start_new_session": True}


def process_name_matches(name: str) -> bool:
    lowered = (name or "").lower()
    return any(lowered.startswith(prefix) for prefix in PROCESS_NAME_PREFIXES)
