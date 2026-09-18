"""React SPA static files and client-side routing fallback."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse

from ..utils.spa import safe_webui_file

router = APIRouter()


async def _spa(request: Request, full_path: str = "") -> FileResponse:
    """Serve Vite files; unknown paths fall back to index.html for client routing."""
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="not found")
    webui = request.app.state.webui
    existing = safe_webui_file(webui, full_path)
    if existing is not None:
        return FileResponse(existing)
    return FileResponse(webui / "index.html")


@router.get("/")
async def spa_root(request: Request) -> FileResponse:
    return await _spa(request, "")


@router.get("/{full_path:path}")
async def spa_path(request: Request, full_path: str) -> FileResponse:
    return await _spa(request, full_path)
