"""Save-game enumerate / save / load / upload / download."""

from __future__ import annotations

import asyncio

from ..models.common import ActionResponse
from ..models.saves import (
    GameStateResponse,
    LoadSaveRequest,
    NewGameRequest,
    SaveHeaderResponse,
    SaveNameRequest,
    SaveSessionResponse,
    SavesResponse,
    SessionNameRequest,
)
from ..utils import serialize
from ..utils.exceptions import ApiError, Unauthorized
from ..utils.helpers import pick
from .state import AppState


class SavesService:
    def __init__(self, state: AppState):
        self._state = state

    async def list_saves(self, token: str) -> SavesResponse:
        ctx = await self._saves_ctx(token)
        game = serialize.game_state(ctx["game_state"])
        return SavesResponse(
            sessions=[SaveSessionResponse.model_validate(session) for session in ctx["sessions"]],
            current_index=ctx["current_index"],
            api_error=ctx["api_error"],
            is_playing=ctx["is_playing"],
            game_state=GameStateResponse.model_validate(game) if game else None,
        )

    async def save_game(self, token: str, payload: SaveNameRequest) -> ActionResponse:
        name = payload.save_name.strip()
        await self._state.api.save_game(token, name)
        return ActionResponse(ok=True, message=f"Saved as '{name}'.")

    async def load_game(self, token: str, payload: LoadSaveRequest) -> ActionResponse:
        name = payload.save_name.strip()
        await self._state.api.load_game(token, name, payload.ags)
        asyncio.create_task(self._after_load())
        return ActionResponse(
            ok=True,
            message=f"Loading '{name}'... the game API is unavailable while loading.",
        )

    async def new_game(self, token: str, payload: NewGameRequest) -> ActionResponse:
        session = payload.session_name.strip()
        await self._state.api.create_new_game(
            token,
            session,
            payload.map_name.strip(),
            payload.starting_location.strip(),
        )
        asyncio.create_task(self._after_load())
        return ActionResponse(ok=True, message=f"Creating session '{session}'...")

    async def set_auto_load(self, token: str, payload: SessionNameRequest) -> ActionResponse:
        session = payload.session_name.strip()
        await self._state.api.set_auto_load(token, session)
        return ActionResponse(ok=True, message=f"Auto-load session set to '{session}'.")

    async def delete_file(self, token: str, payload: SaveNameRequest) -> ActionResponse:
        name = payload.save_name.strip()
        await self._state.api.delete_save_file(token, name)
        return ActionResponse(ok=True, message=f"Deleted save '{name}'.")

    async def delete_session(self, token: str, payload: SessionNameRequest) -> ActionResponse:
        session = payload.session_name.strip()
        await self._state.api.delete_save_session(token, session)
        return ActionResponse(ok=True, message=f"Deleted session '{session}'.")

    async def upload(
        self, token: str, save_name: str, file_bytes: bytes, load: bool, ags: bool, filename: str
    ) -> ActionResponse:
        name = save_name.strip() or filename.rsplit(".", 1)[0]
        await self._state.api.upload_save(token, name, file_bytes, load, ags)
        if load:
            asyncio.create_task(self._after_load())
        return ActionResponse(
            ok=True,
            message=f"Uploaded '{name}'" + (" and loading." if load else "."),
        )

    async def download(self, token: str, save_name: str) -> tuple[bytes, str]:
        content = await self._state.api.download_save(token, save_name)
        safe = "".join(c for c in save_name if c.isalnum() or c in "-_. ") or "save"
        return content, safe

    async def _after_load(self) -> None:
        """LoadGame/CreateNewGame return 202 and the API goes dark (state 2). Wait for it."""
        await asyncio.sleep(2.0)
        await self._state.wait_for_api(timeout=300)

    async def _saves_ctx(self, token: str) -> dict:
        sessions: list = []
        current_index = -1
        api_error = None
        game_state = None
        try:
            data = await self._state.api.enumerate_sessions(token)
            sessions = pick(data, "sessions", default=[]) or []
            current_index = pick(data, "currentSessionIndex", default=-1)
            game_state = await self._state.api.query_server_state(token)
        except Unauthorized:
            raise
        except ApiError as exc:
            api_error = exc.code
        norm = []
        for session in sessions:
            headers = []
            for header in pick(session, "saveHeaders", default=[]) or []:
                headers.append(
                    SaveHeaderResponse(
                        saveName=pick(header, "saveName", default="") or "",
                        sessionName=pick(header, "sessionName", default="") or "",
                        playDuration=pick(header, "playDurationSeconds", default=0),
                        saveDateTime=pick(header, "saveDateTime", default="") or "",
                        mapName=(pick(header, "mapName", default="") or "").rsplit("/", 1)[-1],
                        buildVersion=pick(header, "buildVersion", default="") or "",
                        saveVersion=pick(header, "saveVersion", default="") or "",
                        modded=bool(pick(header, "isModdedSave", default=False)),
                        edited=bool(pick(header, "isEditedSave", default=False)),
                        creative=bool(pick(header, "isCreativeModeEnabled", default=False)),
                    )
                )
            headers.sort(key=lambda item: item.saveDateTime, reverse=True)
            norm.append(
                {
                    "sessionName": pick(session, "sessionName", default=""),
                    "headers": [h.model_dump() for h in headers],
                }
            )
        return {
            "sessions": norm,
            "current_index": current_index,
            "api_error": api_error,
            "game_state": game_state,
            "is_playing": bool(pick(game_state, "isGameRunning", default=False))
            if game_state
            else False,
        }
