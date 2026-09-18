"""FastAPI dependencies: app state, session token, service factories."""

from __future__ import annotations

from fastapi import Depends, HTTPException, Request

from ..services.console import ConsoleService
from ..services.process import ProcessService
from ..services.saves import SavesService
from ..services.session import SessionService
from ..services.state import AppState
from ..services.status import StatusService
from ..services.updates import UpdatesService


def get_state(request: Request) -> AppState:
    return request.app.state.shell


def require_token(request: Request) -> str:
    token = request.session.get("token")
    if not token:
        raise HTTPException(status_code=401, detail="unauthorized")
    return token


def get_session_service(state: AppState = Depends(get_state)) -> SessionService:
    return SessionService(state)


def get_status_service(state: AppState = Depends(get_state)) -> StatusService:
    return StatusService(state)


def get_process_service(state: AppState = Depends(get_state)) -> ProcessService:
    return ProcessService(state)


def get_saves_service(state: AppState = Depends(get_state)) -> SavesService:
    return SavesService(state)


def get_console_service(state: AppState = Depends(get_state)) -> ConsoleService:
    return ConsoleService(state)


def get_updates_service(state: AppState = Depends(get_state)) -> UpdatesService:
    return UpdatesService(state)
