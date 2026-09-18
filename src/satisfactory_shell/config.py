"""config.json loading with defaults, path resolution and persistence."""

from __future__ import annotations

import copy
import json
import os
import secrets
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from . import paths

DEFAULTS: dict[str, Any] = {
    "paths": {"server_root": "", "steamcmd": "", "appmanifest": ""},
    "game": {
        "host": "127.0.0.1",
        "port": 49500,
        "reliable_port": 49501,
        "extra_args": [
            "-log",
            "-unattended",
            "-ini:Engine:[SystemSettings]:FG.DedicatedServer.AllowInsecureLocalAccess=1",
        ],
        "client_password": "",
    },
    "webui": {"host": "127.0.0.1", "port": 8080, "secret_key": ""},
    "process": {
        "auto_start": True,
        "auto_restart": True,
        "restart_delay_seconds": 10,
        "shutdown_timeout_seconds": 30,
    },
    "steam": {"app_id": 1690800, "beta": "", "validate": True},
    "metrics": {"interval_seconds": 5, "history_minutes": 60},
}


def _deep_merge(base: dict, override: dict) -> dict:
    out = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _deep_merge(out[key], value)
        else:
            out[key] = value
    return out


def config_path() -> Path:
    env = os.environ.get("SATISFACTORY_SHELL_CONFIG") or os.environ.get("COATING_CONFIG")
    if env:
        return Path(env)
    appdata_cfg = paths.user_config_dir() / "config.json"
    local_cfg = paths.starter_root() / "config.json"
    if appdata_cfg.is_file():
        return appdata_cfg
    if local_cfg.is_file():
        return local_cfg
    return appdata_cfg


@dataclass
class Config:
    raw: dict[str, Any]
    file: Path
    server_root: Path | None = None
    steamcmd: Path | None = None
    appmanifest: Path | None = None
    data_dir: Path = field(default_factory=paths.user_data_dir)

    # -- typed accessors ---------------------------------------------------
    @property
    def game_host(self) -> str:
        return self.raw["game"]["host"]

    @property
    def game_port(self) -> int:
        return int(self.raw["game"]["port"])

    @property
    def reliable_port(self) -> int:
        return int(self.raw["game"]["reliable_port"])

    @property
    def extra_args(self) -> list[str]:
        return list(self.raw["game"]["extra_args"])

    @property
    def client_password(self) -> str:
        return str(self.raw["game"].get("client_password") or "")

    @property
    def webui_host(self) -> str:
        return self.raw["webui"]["host"]

    @property
    def webui_port(self) -> int:
        return int(self.raw["webui"]["port"])

    @property
    def secret_key(self) -> str:
        return self.raw["webui"]["secret_key"]

    @property
    def auto_start(self) -> bool:
        return bool(self.raw["process"]["auto_start"])

    @property
    def auto_restart(self) -> bool:
        return bool(self.raw["process"]["auto_restart"])

    @auto_restart.setter
    def auto_restart(self, value: bool) -> None:
        self.raw["process"]["auto_restart"] = bool(value)

    @property
    def restart_delay(self) -> float:
        return float(self.raw["process"]["restart_delay_seconds"])

    @property
    def shutdown_timeout(self) -> float:
        return float(self.raw["process"]["shutdown_timeout_seconds"])

    @property
    def app_id(self) -> int:
        return int(self.raw["steam"]["app_id"])

    @property
    def steam_beta(self) -> str:
        return self.raw["steam"]["beta"] or ""

    @property
    def steam_validate(self) -> bool:
        return bool(self.raw["steam"]["validate"])

    @property
    def metrics_interval(self) -> float:
        return float(self.raw["metrics"]["interval_seconds"])

    @property
    def metrics_history_minutes(self) -> int:
        return int(self.raw["metrics"]["history_minutes"])

    @property
    def server_exe(self) -> Path | None:
        return self.server_root / "FactoryServer.exe" if self.server_root else None

    @property
    def log_file(self) -> Path | None:
        if not self.server_root:
            return None
        return self.server_root / "FactoryGame" / "Saved" / "Logs" / "FactoryGame.log"

    @property
    def version_file(self) -> Path | None:
        if not self.server_root:
            return None
        return (
            self.server_root
            / "Engine"
            / "Binaries"
            / "Win64"
            / "FactoryServer-Win64-Shipping.version"
        )

    def save(self) -> None:
        self.file.parent.mkdir(parents=True, exist_ok=True)
        self.file.write_text(json.dumps(self.raw, indent=2) + "\n", encoding="utf-8")


def _resolve_path(value: str, base: Path) -> Path:
    p = Path(value).expanduser()
    return p if p.is_absolute() else (base / p).resolve()


def load() -> Config:
    file = config_path()
    user: dict[str, Any] = {}
    if file.is_file():
        user = json.loads(file.read_text(encoding="utf-8"))
    raw = _deep_merge(DEFAULTS, user)
    cfg = Config(raw=raw, file=file)

    changed = not file.is_file()
    if not raw["webui"]["secret_key"]:
        raw["webui"]["secret_key"] = secrets.token_urlsafe(32)
        changed = True

    root = paths.starter_root()

    # server_root: explicit or walk up from the starter root
    sr = raw["paths"]["server_root"]
    cfg.server_root = _resolve_path(sr, root) if sr else paths.find_server_root(root)

    # steamcmd: explicit, or on PATH, or steamcmd/ next to the starter
    sc = raw["paths"]["steamcmd"]
    if sc:
        cfg.steamcmd = _resolve_path(sc, root)
    else:
        found = shutil.which("steamcmd") or shutil.which("steamcmd.exe")
        if found:
            cfg.steamcmd = Path(found)
        elif (root / "steamcmd" / "steamcmd.exe").is_file():
            cfg.steamcmd = root / "steamcmd" / "steamcmd.exe"

    am = raw["paths"]["appmanifest"]
    if am:
        cfg.appmanifest = _resolve_path(am, root)
    elif cfg.server_root:
        cfg.appmanifest = paths.find_appmanifest(cfg.server_root, cfg.app_id)

    cfg.data_dir.mkdir(parents=True, exist_ok=True)
    if changed:
        cfg.save()
    return cfg
