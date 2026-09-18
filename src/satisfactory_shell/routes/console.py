"""In-game console routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ..models.console import ConsoleResponse, ConsoleRunRequest, ConsoleRunResponse, TailResponse
from ..services.console import ConsoleService
from ..utils.deps import get_console_service, require_token

router = APIRouter(prefix="/api/console")


@router.get("", response_model=ConsoleResponse)
async def api_console(
    _token: str = Depends(require_token),
    service: ConsoleService = Depends(get_console_service),
) -> ConsoleResponse:
    return service.snapshot()


@router.post("/run", response_model=ConsoleRunResponse)
async def api_console_run(
    payload: ConsoleRunRequest,
    token: str = Depends(require_token),
    service: ConsoleService = Depends(get_console_service),
) -> ConsoleRunResponse:
    return await service.run(token, payload)


@router.get("/tail", response_model=TailResponse)
async def api_console_tail(
    offset: int = 0,
    _token: str = Depends(require_token),
    service: ConsoleService = Depends(get_console_service),
) -> TailResponse:
    return service.tail(offset)
