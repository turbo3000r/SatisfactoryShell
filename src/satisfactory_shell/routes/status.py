"""Status, dashboard, and metrics routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from ..models.status import DashboardResponse, MetricsResponse, StatusResponse
from ..services.status import StatusService
from ..utils.deps import get_status_service, require_token

router = APIRouter(prefix="/api")


@router.get("/status", response_model=StatusResponse)
async def api_status(
    request: Request,
    service: StatusService = Depends(get_status_service),
) -> StatusResponse:
    return await service.status(authed=bool(request.session.get("token")))


@router.get("/metrics", response_model=MetricsResponse)
async def api_metrics(
    _token: str = Depends(require_token),
    service: StatusService = Depends(get_status_service),
) -> JSONResponse:
    payload = service.metrics()
    return JSONResponse(
        payload.model_dump(mode="json"),
        headers={"Cache-Control": "no-store"},
    )


@router.get("/dashboard", response_model=DashboardResponse)
async def api_dashboard(
    token: str = Depends(require_token),
    service: StatusService = Depends(get_status_service),
) -> DashboardResponse:
    return await service.dashboard(token)
