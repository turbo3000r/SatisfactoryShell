"""JSON-safe views of the runtime dataclasses, used by the API services."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict
from datetime import datetime
from typing import Any

from .helpers import pick


def _iso(value: datetime | None) -> str | None:
    return value.isoformat(sep=" ", timespec="seconds") if value else None


def process_info(info: Any) -> dict:
    return asdict(info) | {"last_unexpected_exit": _iso(info.last_unexpected_exit)}


def lightweight(lw: Any | None) -> dict | None:
    if lw is None:
        return None
    return {
        "state": lw.state,
        "state_name": lw.state_name,
        "changelist": lw.changelist,
        "modded": lw.modded,
        "server_name": lw.server_name,
    }


def events(items: Iterable[tuple[datetime, str]]) -> list[dict]:
    return [{"ts": _iso(ts), "message": message} for ts, message in items]


def update_status(status: Any, *, log_limit: int = 400) -> dict:
    return {
        "running": status.running,
        "phase": status.phase,
        "started_at": _iso(status.started_at),
        "finished_at": _iso(status.finished_at),
        "exit_code": status.exit_code,
        "log_lines": status.log_lines[-log_limit:],
        "available_buildid": status.available_buildid,
        "checked_at": _iso(status.checked_at),
        "check_error": status.check_error,
    }


def game_state(state: dict | None) -> dict | None:
    """Flatten ``QueryServerState`` (the game API mixes camelCase and PascalCase)."""
    if not state:
        return None
    return {
        "session_name": pick(state, "activeSessionName", default="") or "",
        "players": pick(state, "numConnectedPlayers", default=0) or 0,
        "player_limit": pick(state, "playerLimit", default=0) or 0,
        "tech_tier": pick(state, "techTier", default=0),
        "game_phase": (pick(state, "gamePhase", default="") or "").replace(
            "/Game/FactoryGame/GamePhases/", ""
        ),
        "active_schematic": (pick(state, "activeSchematic", default="") or "").rsplit("/", 1)[-1],
        "is_running": bool(pick(state, "isGameRunning", default=False)),
        "is_paused": bool(pick(state, "isGamePaused", default=False)),
        "duration_seconds": pick(state, "totalGameDuration", default=0) or 0,
        "tick_rate": float(pick(state, "averageTickRate", default=0.0) or 0.0),
        "auto_load_session": pick(state, "autoLoadSessionName", default="") or "",
    }
