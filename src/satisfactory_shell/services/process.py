"""Process start / stop / restart / auto-restart."""

from __future__ import annotations

from ..models.common import ActionResponse
from ..utils.exceptions import AppError
from .state import AppState


class ProcessService:
    def __init__(self, state: AppState):
        self._state = state

    async def start(self) -> ActionResponse:
        await self._state.pm.start()
        return ActionResponse(ok=True, message="Server start requested.")

    async def dispatch(self, action: str, token: str) -> ActionResponse:
        cfg = self._state.cfg
        if action == "start":
            await self._state.pm.start()
            message = "Server start requested."
        elif action == "stop":
            await self._state.pm.stop(self._state.api, token)
            message = "Server stopped."
        elif action == "restart":
            await self._state.pm.restart(self._state.api, token)
            message = "Server restarted."
        elif action == "toggle-auto-restart":
            self._state.pm.set_auto_restart(not cfg.auto_restart)
            message = f"Auto-restart {'enabled' if cfg.auto_restart else 'disabled'}."
        else:
            raise AppError(f"unknown action {action}", status_code=404)
        return ActionResponse(ok=True, message=message)
