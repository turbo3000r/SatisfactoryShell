"""FastAPI application factory: middleware, exception handlers, routers, SPA."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from . import __version__
from .configs.settings import Config
from .routes.console import router as console_router
from .routes.process import router as process_router
from .routes.saves import router as saves_router
from .routes.session import router as session_router
from .routes.spa import router as spa_router
from .routes.status import router as status_router
from .routes.updates import router as updates_router
from .services.state import AppState
from .utils.exceptions import ApiError, AppError, api_error_http_status
from .utils.spa import webui_or_raise


def create_app(cfg: Config) -> FastAPI:
    state = AppState(cfg)
    webui = webui_or_raise()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.shell = state
        state.tasks = [
            asyncio.create_task(state.pm.run_watchdog(), name="watchdog"),
            asyncio.create_task(state.metrics.run(), name="metrics"),
            asyncio.create_task(state.bootstrap.run(state.wait_for_api), name="bootstrap"),
        ]
        try:
            yield
        finally:
            for task in list(state.tasks):
                task.cancel()
            await state.api.aclose()

    app = FastAPI(
        title="Satisfactory Shell",
        version=__version__,
        lifespan=lifespan,
        docs_url=None,
        redoc_url=None,
    )
    app.state.shell = state
    app.state.webui = webui

    @app.exception_handler(ApiError)
    async def game_api_error(_request: Request, exc: ApiError) -> JSONResponse:
        """Game-API failures in ``/api`` routes become JSON instead of a 500."""
        return JSONResponse(
            {"error": exc.code, "message": exc.message or str(exc)},
            status_code=api_error_http_status(exc),
        )

    @app.exception_handler(AppError)
    async def app_error(_request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse({"detail": exc.message}, status_code=exc.status_code)

    app.add_middleware(
        SessionMiddleware,
        secret_key=cfg.secret_key,
        same_site="lax",
        https_only=False,
        max_age=12 * 3600,
    )

    app.include_router(session_router)
    app.include_router(status_router)
    app.include_router(process_router)
    app.include_router(saves_router)
    app.include_router(console_router)
    app.include_router(updates_router)

    assets = webui / "assets"
    if assets.is_dir():
        app.mount("/assets", StaticFiles(directory=str(assets)), name="assets")

    app.include_router(spa_router)
    return app
