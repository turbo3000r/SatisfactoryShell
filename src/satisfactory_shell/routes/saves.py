"""Save-game routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Form, UploadFile
from fastapi.responses import Response

from ..models.common import ActionResponse
from ..models.saves import (
    LoadSaveRequest,
    NewGameRequest,
    SaveNameRequest,
    SavesResponse,
    SessionNameRequest,
)
from ..services.saves import SavesService
from ..utils.deps import get_saves_service, require_token

router = APIRouter(prefix="/api/saves")


@router.get("", response_model=SavesResponse)
async def api_saves(
    token: str = Depends(require_token),
    service: SavesService = Depends(get_saves_service),
) -> SavesResponse:
    return await service.list_saves(token)


@router.post("/save", response_model=ActionResponse)
async def api_saves_save(
    payload: SaveNameRequest,
    token: str = Depends(require_token),
    service: SavesService = Depends(get_saves_service),
) -> ActionResponse:
    return await service.save_game(token, payload)


@router.post("/load", response_model=ActionResponse)
async def api_saves_load(
    payload: LoadSaveRequest,
    token: str = Depends(require_token),
    service: SavesService = Depends(get_saves_service),
) -> ActionResponse:
    return await service.load_game(token, payload)


@router.post("/new", response_model=ActionResponse)
async def api_saves_new(
    payload: NewGameRequest,
    token: str = Depends(require_token),
    service: SavesService = Depends(get_saves_service),
) -> ActionResponse:
    return await service.new_game(token, payload)


@router.post("/autoload", response_model=ActionResponse)
async def api_saves_autoload(
    payload: SessionNameRequest,
    token: str = Depends(require_token),
    service: SavesService = Depends(get_saves_service),
) -> ActionResponse:
    return await service.set_auto_load(token, payload)


@router.post("/delete-file", response_model=ActionResponse)
async def api_saves_delete_file(
    payload: SaveNameRequest,
    token: str = Depends(require_token),
    service: SavesService = Depends(get_saves_service),
) -> ActionResponse:
    return await service.delete_file(token, payload)


@router.post("/delete-session", response_model=ActionResponse)
async def api_saves_delete_session(
    payload: SessionNameRequest,
    token: str = Depends(require_token),
    service: SavesService = Depends(get_saves_service),
) -> ActionResponse:
    return await service.delete_session(token, payload)


@router.post("/upload", response_model=ActionResponse)
async def api_saves_upload(
    file: UploadFile,
    save_name: str = Form(""),
    load: bool = Form(False),
    ags: bool = Form(False),
    token: str = Depends(require_token),
    service: SavesService = Depends(get_saves_service),
) -> ActionResponse:
    return await service.upload(
        token,
        save_name,
        await file.read(),
        load,
        ags,
        file.filename or "upload",
    )


@router.get("/download")
async def api_saves_download(
    save_name: str,
    token: str = Depends(require_token),
    service: SavesService = Depends(get_saves_service),
) -> Response:
    content, safe = await service.download(token, save_name)
    return Response(
        content,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{safe}.sav"'},
    )
