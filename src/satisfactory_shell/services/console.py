"""FactoryGame.log tail and admin console commands."""

from __future__ import annotations

from datetime import datetime

from ..models.console import (
    ConsoleEntryResponse,
    ConsoleLogResponse,
    ConsoleResponse,
    ConsoleRunRequest,
    ConsoleRunResponse,
    TailResponse,
)
from ..utils.exceptions import ApiError, Unauthorized
from ..utils.logtail import read_tail
from .state import AppState


class ConsoleService:
    def __init__(self, state: AppState):
        self._state = state

    def snapshot(self) -> ConsoleResponse:
        text, offset, _ = read_tail(self._state.cfg.log_file, None)
        return ConsoleResponse(
            history=[
                ConsoleEntryResponse.model_validate(entry)
                for entry in reversed(self._state.console_history)
            ],
            log=ConsoleLogResponse(text=text, offset=offset),
            log_file=str(self._state.cfg.log_file or ""),
        )

    async def run(self, token: str, payload: ConsoleRunRequest) -> ConsoleRunResponse:
        command = payload.command.strip()
        entry = {
            "ts": datetime.now().strftime("%H:%M:%S"),
            "command": command,
            "result": "",
            "error": "",
        }
        try:
            entry["result"] = await self._state.api.run_command(token, command)
        except Unauthorized:
            raise
        except ApiError as exc:
            entry["error"] = str(exc)
        self._state.console_history.append(entry)
        return ConsoleRunResponse(
            history=[
                ConsoleEntryResponse.model_validate(item)
                for item in reversed(self._state.console_history)
            ]
        )

    def tail(self, offset: int) -> TailResponse:
        text, new_offset, rotated = read_tail(self._state.cfg.log_file, offset)
        return TailResponse(text=text, offset=new_offset, rotated=rotated)
