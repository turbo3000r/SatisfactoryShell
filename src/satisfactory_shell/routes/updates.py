"""SteamCMD update routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ..models.common import ActionResponse
from ..models.updates import UpdatesResponse
from ..services.updates import UpdatesService
from ..utils.deps import get_updates_service, require_token

router = APIRouter(prefix="/api/updates")


@router.get("", response_model=UpdatesResponse)
async def api_updates(
    _token: str = Depends(require_token),
    service: UpdatesService = Depends(get_updates_service),
) -> UpdatesResponse:
    return service.snapshot()


@router.post("/check", response_model=ActionResponse)
async def api_updates_check(
    _token: str = Depends(require_token),
    service: UpdatesService = Depends(get_updates_service),
) -> ActionResponse:
    return await service.check()


@router.post("/run", response_model=ActionResponse)
async def api_updates_run(
    token: str = Depends(require_token),
    service: UpdatesService = Depends(get_updates_service),
) -> ActionResponse:
    return await service.run(token)
