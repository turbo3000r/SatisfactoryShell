"""Session cookie login routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from ..models.session import LoginRequest, LoginResponse, LogoutResponse, SessionResponse
from ..services.session import SessionService
from ..utils.deps import get_session_service

router = APIRouter(prefix="/api")


@router.get("/session", response_model=SessionResponse)
async def api_session(
    request: Request,
    service: SessionService = Depends(get_session_service),
) -> SessionResponse:
    return service.session(request)


@router.post("/login", response_model=LoginResponse)
async def api_login(
    payload: LoginRequest,
    request: Request,
    service: SessionService = Depends(get_session_service),
) -> LoginResponse:
    return await service.login(request, payload)


@router.post("/logout", response_model=LogoutResponse)
async def api_logout(
    request: Request,
    service: SessionService = Depends(get_session_service),
) -> LogoutResponse:
    return service.logout(request)
