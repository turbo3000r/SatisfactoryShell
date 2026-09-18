"""config.json loading with defaults, path resolution and persistence."""

from __future__ import annotations

import copy
import json
import os
import secrets
import shutil
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict

from ..utils import paths as pathutil

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
    "steam": {
        "app_id": 1690800,
        "beta": "",
        "validate": True,
        "auto_check": True,
        "check_interval_hours": 2,
    },
    "metrics": {"interval_seconds": 5, "history_minutes": 60},
}


class PathsSettings(BaseModel):
    model_config = ConfigDict(extra="allow")

    server_root: str = ""
    steamcmd: str = ""
    appmanifest: str = ""


class GameSettings(BaseModel):
    model_config = ConfigDict(extra="allow")

    host: str = "127.0.0.1"
    port: int = 49500
    reliable_port: int = 49501
    extra_args: list[str] = Field(
        default_factory=lambda: list(DEFAULTS["game"]["extra_args"])
    )
    client_password: str = ""


class WebuiSettings(BaseModel):
    model_config = ConfigDict(extra="allow")

    host: str = "127.0.0.1"
    port: int = 8080
    secret_key: str = ""


class ProcessSettings(BaseModel):
    model_config = ConfigDict(extra="allow")

    auto_start: bool = True
    auto_restart: bool = True
    restart_delay_seconds: int = 10
    shutdown_timeout_seconds: int = 30


class SteamSettings(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    app_id: int = 1690800
    beta: str = ""
    do_validate: bool = Field(default=True, alias="validate")
    auto_check: bool = True
    check_interval_hours: float = 2


class MetricsSettings(BaseModel):
    model_config = ConfigDict(extra="allow")

    interval_seconds: float = 5
    history_minutes: int = 60


class Config(BaseSettings):
    """Typed settings loaded from config.json, with resolved runtime paths."""

    model_config = SettingsConfigDict(extra="ignore")

    paths: PathsSettings = PathsSettings()
    game: GameSettings = GameSettings()
    webui: WebuiSettings = WebuiSettings()
    process: ProcessSettings = ProcessSettings()
    steam: SteamSettings = SteamSettings()
    metrics: MetricsSettings = MetricsSettings()

    file: Path
    server_root: Path | None = None
    steamcmd: Path | None = None
    appmanifest: Path | None = None
    data_dir: Path = Field(default_factory=pathutil.user_data_dir)

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        del settings_cls, env_settings, dotenv_settings, file_secret_settings
        return (init_settings,)

    @property
    def game_host(self) -> str:
        return self.game.host

    @property
    def game_port(self) -> int:
        return int(self.game.port)

    @property
    def reliable_port(self) -> int:
        return int(self.game.reliable_port)

    @property
    def extra_args(self) -> list[str]:
        return list(self.game.extra_args)

    @property
    def client_password(self) -> str:
        return str(self.game.client_password or "")

    @property
    def webui_host(self) -> str:
        return self.webui.host

    @property
    def webui_port(self) -> int:
        return int(self.webui.port)

    @property
    def secret_key(self) -> str:
        return self.webui.secret_key

    @property
    def auto_start(self) -> bool:
        return bool(self.process.auto_start)

    @property
    def auto_restart(self) -> bool:
        return bool(self.process.auto_restart)

    @auto_restart.setter
    def auto_restart(self, value: bool) -> None:
        self.process.auto_restart = bool(value)

    @property
    def restart_delay(self) -> float:
        return float(self.process.restart_delay_seconds)

    @property
    def shutdown_timeout(self) -> float:
        return float(self.process.shutdown_timeout_seconds)

    @property
    def app_id(self) -> int:
        return int(self.steam.app_id)

    @property
    def steam_beta(self) -> str:
        return self.steam.beta or ""

    @property
    def steam_validate(self) -> bool:
        return bool(self.steam.do_validate)

    @property
    def steam_auto_check(self) -> bool:
        return bool(self.steam.auto_check)

    @property
    def steam_check_interval_hours(self) -> float:
        return float(self.steam.check_interval_hours)

    @property
    def metrics_interval(self) -> float:
        return float(self.metrics.interval_seconds)

    @property
    def metrics_history_minutes(self) -> int:
        return int(self.metrics.history_minutes)

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
        payload = {
            "paths": self.paths.model_dump(),
            "game": self.game.model_dump(),
            "webui": self.webui.model_dump(),
            "process": self.process.model_dump(),
            "steam": self.steam.model_dump(by_alias=True),
            "metrics": self.metrics.model_dump(),
        }
        self.file.parent.mkdir(parents=True, exist_ok=True)
        self.file.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


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
    appdata_cfg = pathutil.user_config_dir() / "config.json"
    local_cfg = pathutil.starter_root() / "config.json"
    if appdata_cfg.is_file():
        return appdata_cfg
    if local_cfg.is_file():
        return local_cfg
    return appdata_cfg


def _resolve_path(value: str, base: Path) -> Path:
    p = Path(value).expanduser()
    return p if p.is_absolute() else (base / p).resolve()


def load() -> Config:
    file = config_path()
    user: dict[str, Any] = {}
    if file.is_file():
        user = json.loads(file.read_text(encoding="utf-8"))
    raw = _deep_merge(DEFAULTS, user)
    cfg = Config.model_validate({**raw, "file": file})

    changed = not file.is_file()
    if not cfg.webui.secret_key:
        cfg.webui.secret_key = secrets.token_urlsafe(32)
        changed = True

    root = pathutil.starter_root()

    sr = cfg.paths.server_root
    cfg.server_root = _resolve_path(sr, root) if sr else pathutil.find_server_root(root)

    sc = cfg.paths.steamcmd
    if sc:
        cfg.steamcmd = _resolve_path(sc, root)
    else:
        found = shutil.which("steamcmd") or shutil.which("steamcmd.exe")
        if found:
            cfg.steamcmd = Path(found)
        elif (root / "steamcmd" / "steamcmd.exe").is_file():
            cfg.steamcmd = root / "steamcmd" / "steamcmd.exe"

    am = cfg.paths.appmanifest
    if am:
        cfg.appmanifest = _resolve_path(am, root)
    elif cfg.server_root:
        cfg.appmanifest = pathutil.find_appmanifest(cfg.server_root, cfg.app_id)

    cfg.data_dir.mkdir(parents=True, exist_ok=True)
    if changed:
        cfg.save()
    return cfg


@lru_cache
def get_settings() -> Config:
    """Cached settings accessor for dependency injection."""
    return load()
