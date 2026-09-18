"""Session login and logout."""

from __future__ import annotations

from datetime import datetime

from fastapi import Request

from .. import __version__
from ..models.session import LoginRequest, LoginResponse, LogoutResponse, SessionResponse
from .state import AppState


class SessionService:
    def __init__(self, state: AppState):
        self._state = state

    def session(self, request: Request) -> SessionResponse:
        return SessionResponse(
            authed=bool(request.session.get("token")),
            login_at=request.session.get("login_at"),
            app_version=__version__,
        )

    async def login(self, request: Request, payload: LoginRequest) -> LoginResponse:
        password = payload.password or ""
        token = (
            await self._state.api.password_login(password)
            if password
            else await self._state.api.passwordless_login()
        )
        request.session["token"] = token
        request.session["login_at"] = datetime.now().isoformat(timespec="seconds")
        return LoginResponse(authed=True)

    def logout(self, request: Request) -> LogoutResponse:
        request.session.clear()
        return LogoutResponse(authed=False)
