"""FactoryServer process control routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ..models.common import ActionResponse
from ..services.process import ProcessService
from ..utils.deps import get_process_service, require_token

router = APIRouter(prefix="/api")


@router.post("/start", response_model=ActionResponse)
async def api_start(
    service: ProcessService = Depends(get_process_service),
) -> ActionResponse:
    """Public: the game API cannot be reached while the server is down."""
    return await service.start()


@router.post("/process/{action}", response_model=ActionResponse)
async def api_process_action(
    action: str,
    token: str = Depends(require_token),
    service: ProcessService = Depends(get_process_service),
) -> ActionResponse:
    return await service.dispatch(action, token)
