"""FastAPI application: JSON API and the React SPA."""

from __future__ import annotations

import asyncio
import platform
import time
from collections import deque
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from . import __version__, paths, serialize
from .bootstrap import Bootstrapper, read_status as read_bootstrap_status
from .config import Config
from .logtail import read_tail
from .metrics import MetricsCollector
from .process import ProcessManager
from .sf_client import (
    SERVER_STATES,
    ApiError,
    ApiUnavailable,
    ClientAuth,
    HttpsClient,
    Unauthorized,
    pick,
    poll_lightweight,
)
from .steamcmd import SteamCmd, read_appmanifest, read_version_file


class State:
    """Everything shared between requests."""

    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.api = HttpsClient(cfg.game_host, cfg.game_port)
        self.client_auth = ClientAuth(self.api, cfg.client_password)
        self.pm = ProcessManager(cfg)
        self.metrics = MetricsCollector(cfg, self.pm, self.api, self.client_auth)
        self.steam = SteamCmd(cfg)
        self.bootstrap = Bootstrapper(cfg, self.api)
        self.started_at = time.time()
        self.console_history: deque[dict] = deque(maxlen=50)
        self.tasks: list[asyncio.Task] = []

    async def wait_for_api(self, timeout: float = 120.0) -> bool:
        """Block until the HTTPS API answers a HealthCheck (after start / load)."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                await self.api.health_check()
                return True
            except ApiError:
                await asyncio.sleep(2.0)
        return False


def _webui_or_raise() -> Path:
    webui = paths.webui_dir()
    index = webui / "index.html"
    if not index.is_file():
        if paths.is_frozen():
            hint = f"Keep the webui folder next to the exe ({webui})."
        else:
            hint = "Run `npm run build` in frontend/."
        raise FileNotFoundError(f"WebUI assets not found at {index}. {hint}")
    return webui


def _safe_webui_file(webui: Path, relative: str) -> Path | None:
    if not relative or relative.endswith("/"):
        return None
    candidate = (webui / relative).resolve()
    try:
        candidate.relative_to(webui.resolve())
    except ValueError:
        return None
    return candidate if candidate.is_file() else None


def create_app(cfg: Config) -> FastAPI:
    st = State(cfg)
    webui = _webui_or_raise()

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        st.tasks = [
            asyncio.create_task(st.pm.run_watchdog(), name="watchdog"),
            asyncio.create_task(st.metrics.run(), name="metrics"),
            asyncio.create_task(st.bootstrap.run(st.wait_for_api), name="bootstrap"),
        ]
        try:
            yield
        finally:
            for t in st.tasks:
                t.cancel()
            await st.api.aclose()

    app = FastAPI(
        title="Satisfactory Shell",
        version=__version__,
        lifespan=lifespan,
        docs_url=None,
        redoc_url=None,
    )

    @app.exception_handler(ApiError)
    async def game_api_error(_request: Request, exc: ApiError) -> JSONResponse:
        """Game-API failures in ``/api`` routes become JSON instead of a 500."""
        if isinstance(exc, Unauthorized):
            status = 401
        elif isinstance(exc, ApiUnavailable):
            status = 503
        else:
            status = 400
        return JSONResponse(
            {"error": exc.code, "message": exc.message or str(exc)}, status_code=status
        )

    app.add_middleware(
        SessionMiddleware,
        secret_key=cfg.secret_key,
        same_site="lax",
        https_only=False,
        max_age=12 * 3600,
    )

    # ------------------------------------------------------------ helpers
    def token_of(request: Request) -> str | None:
        return request.session.get("token")

    async def public_snapshot() -> dict:
        """Data that needs no game session token."""
        lw = await poll_lightweight(cfg.game_host, cfg.game_port, timeout=0.8)
        health: dict | None = None
        game_state: dict | None = None
        api_error: str | None = None
        if lw and lw.state != 2:
            try:
                health = await st.api.health_check()
            except ApiError as exc:
                api_error = exc.code
            if health is not None:
                if (
                    st.metrics.last_state
                    and st.metrics.last_state_ts
                    and time.time() - st.metrics.last_state_ts < 30
                ):
                    game_state = st.metrics.last_state
                else:
                    try:
                        game_state = await st.client_auth.query_server_state()
                    except Unauthorized:
                        game_state = None
                    except ApiError as exc:
                        api_error = exc.code
        pinfo = st.pm.info()
        state_num = lw.state if lw else (2 if pinfo.running else 0)
        return {
            "lw": lw,
            "state_num": state_num,
            "state_name": SERVER_STATES.get(state_num, "Unknown")
            if lw or not pinfo.running
            else "Starting",
            "health": health,
            "game_state": game_state,
            "api_error": api_error,
            "bootstrap": read_bootstrap_status(cfg),
            "proc": pinfo,
            "version": read_version_file(cfg.version_file),
            "manifest": read_appmanifest(cfg.appmanifest),
            "runtime": {
                "app_version": __version__,
                "mode": "frozen exe" if paths.is_frozen() else "source (poetry)",
                "python": platform.python_version(),
                "platform": platform.platform(),
                "uptime": time.time() - st.started_at,
                "bind": f"{cfg.webui_host}:{cfg.webui_port}",
                "config": str(cfg.file),
                "server_root": str(cfg.server_root or "not found"),
                "steamcmd": str(cfg.steamcmd or "not found"),
                "game_api": f"https://{cfg.game_host}:{cfg.game_port}/api/v1",
            },
        }

    async def dashboard_ctx(token: str) -> dict:
        game_state = options = pending = None
        api_error = None
        try:
            game_state = await st.api.query_server_state(token)
            opts = await st.api.get_server_options(token)
            options = pick(opts, "serverOptions", default={}) or {}
            pending = pick(opts, "pendingServerOptions", default={}) or {}
        except Unauthorized:
            raise
        except ApiError as exc:
            api_error = exc.code
        lw = await poll_lightweight(cfg.game_host, cfg.game_port, timeout=0.6)
        return {
            "game_state": game_state,
            "options": options,
            "pending": pending,
            "api_error": api_error,
            "proc": st.pm.info(),
            "events": list(reversed(st.pm.events[-15:])),
            "lw": lw,
            "state_name": lw.state_name
            if lw
            else ("Starting" if st.pm.info().running else "Offline"),
        }

    async def saves_ctx(token: str) -> dict:
        sessions: list = []
        current_index = -1
        api_error = None
        game_state = None
        try:
            data = await st.api.enumerate_sessions(token)
            sessions = pick(data, "sessions", default=[]) or []
            current_index = pick(data, "currentSessionIndex", default=-1)
            game_state = await st.api.query_server_state(token)
        except Unauthorized:
            raise
        except ApiError as exc:
            api_error = exc.code
        norm = []
        for s in sessions:
            headers = []
            for h in pick(s, "saveHeaders", default=[]) or []:
                headers.append(
                    {
                        "saveName": pick(h, "saveName", default=""),
                        "sessionName": pick(h, "sessionName", default=""),
                        "playDuration": pick(h, "playDurationSeconds", default=0),
                        "saveDateTime": pick(h, "saveDateTime", default=""),
                        "mapName": (pick(h, "mapName", default="") or "").rsplit("/", 1)[-1],
                        "buildVersion": pick(h, "buildVersion", default=""),
                        "saveVersion": pick(h, "saveVersion", default=""),
                        "modded": pick(h, "isModdedSave", default=False),
                        "edited": pick(h, "isEditedSave", default=False),
                        "creative": pick(h, "isCreativeModeEnabled", default=False),
                    }
                )
            headers.sort(key=lambda h: h["saveDateTime"], reverse=True)
            norm.append({"sessionName": pick(s, "sessionName", default=""), "headers": headers})
        return {
            "sessions": norm,
            "current_index": current_index,
            "api_error": api_error,
            "game_state": game_state,
            "is_playing": bool(pick(game_state, "isGameRunning", default=False))
            if game_state
            else False,
        }

    async def after_load(_token: str) -> None:
        """LoadGame/CreateNewGame return 202 and the API goes dark (state 2). Wait for it."""
        await asyncio.sleep(2.0)
        await st.wait_for_api(timeout=300)

    def updates_ctx() -> dict:
        inst = st.steam.installed()
        local_bid = inst["manifest"].get("buildid")
        avail = st.steam.status.available_buildid
        return {
            "installed": inst,
            "status": st.steam.status,
            "steamcmd_available": st.steam.available,
            "steamcmd_path": str(cfg.steamcmd or ""),
            "server_root": str(cfg.server_root or ""),
            "local_buildid": local_bid,
            "update_available": bool(avail and local_bid and avail != local_bid),
            "proc": st.pm.info(),
            "app_id": cfg.app_id,
            "beta": cfg.steam_beta,
        }

    async def read_body(request: Request) -> dict:
        try:
            data = await request.json()
        except Exception:  # pylint: disable=broad-exception-caught
            return {}
        return data if isinstance(data, dict) else {}

    def api_token(request: Request) -> str:
        tok = token_of(request)
        if not tok:
            raise HTTPException(status_code=401, detail="unauthorized")
        return tok

    def required(data: dict, key: str) -> str:
        value = str(data.get(key) or "").strip()
        if not value:
            raise HTTPException(status_code=422, detail=f"{key} is required")
        return value

    # ----------------------------------------------------- JSON API (SPA)
    @app.get("/api/session")
    async def api_session(request: Request):
        return {
            "authed": bool(token_of(request)),
            "login_at": request.session.get("login_at"),
            "app_version": __version__,
        }

    @app.post("/api/login")
    async def api_login(request: Request):
        data = await read_body(request)
        password = str(data.get("password") or "")
        token = (
            await st.api.password_login(password) if password else await st.api.passwordless_login()
        )
        request.session["token"] = token
        request.session["login_at"] = datetime.now().isoformat(timespec="seconds")
        return {"authed": True}

    @app.post("/api/logout")
    async def api_logout(request: Request):
        request.session.clear()
        return {"authed": False}

    @app.get("/api/status")
    async def api_status(request: Request):
        snap = await public_snapshot()
        return {
            "authed": bool(token_of(request)),
            "state": {"num": snap["state_num"], "name": snap["state_name"]},
            "health": pick(snap["health"], "health", default=None),
            "api_error": snap["api_error"],
            "lightweight": serialize.lightweight(snap["lw"]),
            "process": serialize.process_info(snap["proc"]),
            "game_state": serialize.game_state(snap["game_state"]),
            "bootstrap": snap["bootstrap"],
            "version": snap["version"],
            "manifest": snap["manifest"],
            "runtime": snap["runtime"],
        }

    @app.get("/api/metrics")
    async def api_metrics(request: Request):
        api_token(request)
        payload = {
            "samples": st.metrics.snapshot(),
            "process": serialize.process_info(st.pm.info()),
        }
        return JSONResponse(payload, headers={"Cache-Control": "no-store"})

    @app.get("/api/dashboard")
    async def api_dashboard(request: Request):
        ctx = await dashboard_ctx(api_token(request))
        return {
            "state_name": ctx["state_name"],
            "api_error": ctx["api_error"],
            "game_state": serialize.game_state(ctx["game_state"]),
            "options": ctx["options"],
            "pending": ctx["pending"],
            "process": serialize.process_info(ctx["proc"]),
            "events": serialize.events(ctx["events"]),
        }

    @app.post("/api/start")
    async def api_start(_request: Request):
        """Public: the game API cannot be reached while the server is down."""
        await st.pm.start()
        return {"ok": True, "message": "Server start requested."}

    @app.post("/api/process/{action}")
    async def api_process_action(request: Request, action: str):
        tok = api_token(request)
        if action == "start":
            await st.pm.start()
            message = "Server start requested."
        elif action == "stop":
            await st.pm.stop(st.api, tok)
            message = "Server stopped."
        elif action == "restart":
            await st.pm.restart(st.api, tok)
            message = "Server restarted."
        elif action == "toggle-auto-restart":
            st.pm.set_auto_restart(not cfg.auto_restart)
            message = f"Auto-restart {'enabled' if cfg.auto_restart else 'disabled'}."
        else:
            raise HTTPException(status_code=404, detail=f"unknown action {action}")
        return {"ok": True, "message": message}

    @app.get("/api/saves")
    async def api_saves(request: Request):
        ctx = await saves_ctx(api_token(request))
        return {
            "sessions": ctx["sessions"],
            "current_index": ctx["current_index"],
            "api_error": ctx["api_error"],
            "is_playing": ctx["is_playing"],
            "game_state": serialize.game_state(ctx["game_state"]),
        }

    @app.post("/api/saves/save")
    async def api_saves_save(request: Request):
        tok = api_token(request)
        name = required(await read_body(request), "save_name")
        await st.api.save_game(tok, name)
        return {"ok": True, "message": f"Saved as '{name}'."}

    @app.post("/api/saves/load")
    async def api_saves_load(request: Request):
        tok = api_token(request)
        data = await read_body(request)
        name = required(data, "save_name")
        await st.api.load_game(tok, name, bool(data.get("ags")))
        asyncio.create_task(after_load(tok))
        return {
            "ok": True,
            "message": f"Loading '{name}'... the game API is unavailable while loading.",
        }

    @app.post("/api/saves/new")
    async def api_saves_new(request: Request):
        tok = api_token(request)
        data = await read_body(request)
        session = required(data, "session_name")
        await st.api.create_new_game(
            tok,
            session,
            str(data.get("map_name") or "").strip(),
            str(data.get("starting_location") or "").strip(),
        )
        asyncio.create_task(after_load(tok))
        return {"ok": True, "message": f"Creating session '{session}'..."}

    @app.post("/api/saves/autoload")
    async def api_saves_autoload(request: Request):
        tok = api_token(request)
        session = required(await read_body(request), "session_name")
        await st.api.set_auto_load(tok, session)
        return {"ok": True, "message": f"Auto-load session set to '{session}'."}

    @app.post("/api/saves/delete-file")
    async def api_saves_delete_file(request: Request):
        tok = api_token(request)
        name = required(await read_body(request), "save_name")
        await st.api.delete_save_file(tok, name)
        return {"ok": True, "message": f"Deleted save '{name}'."}

    @app.post("/api/saves/delete-session")
    async def api_saves_delete_session(request: Request):
        tok = api_token(request)
        session = required(await read_body(request), "session_name")
        await st.api.delete_save_session(tok, session)
        return {"ok": True, "message": f"Deleted session '{session}'."}

    @app.post("/api/saves/upload")
    async def api_saves_upload(
        request: Request,
        file: UploadFile,
        save_name: str = Form(""),
        load: bool = Form(False),
        ags: bool = Form(False),
    ):
        tok = api_token(request)
        name = save_name.strip() or (file.filename or "upload").rsplit(".", 1)[0]
        await st.api.upload_save(tok, name, await file.read(), load, ags)
        if load:
            asyncio.create_task(after_load(tok))
        return {
            "ok": True,
            "message": f"Uploaded '{name}'" + (" and loading." if load else "."),
        }

    @app.get("/api/saves/download")
    async def api_saves_download(request: Request, save_name: str):
        content = await st.api.download_save(api_token(request), save_name)
        safe = "".join(c for c in save_name if c.isalnum() or c in "-_. ") or "save"
        return Response(
            content,
            media_type="application/octet-stream",
            headers={"Content-Disposition": f'attachment; filename="{safe}.sav"'},
        )

    @app.get("/api/console")
    async def api_console(request: Request):
        api_token(request)
        text, offset, _ = read_tail(cfg.log_file, None)
        return {
            "history": list(reversed(st.console_history)),
            "log": {"text": text, "offset": offset},
            "log_file": str(cfg.log_file or ""),
        }

    @app.post("/api/console/run")
    async def api_console_run(request: Request):
        tok = api_token(request)
        command = required(await read_body(request), "command")
        entry = {
            "ts": datetime.now().strftime("%H:%M:%S"),
            "command": command,
            "result": "",
            "error": "",
        }
        try:
            entry["result"] = await st.api.run_command(tok, command)
        except Unauthorized:
            raise
        except ApiError as exc:
            entry["error"] = str(exc)
        st.console_history.append(entry)
        return {"history": list(reversed(st.console_history))}

    @app.get("/api/console/tail")
    async def api_console_tail(request: Request, offset: int = 0):
        api_token(request)
        text, new_offset, rotated = read_tail(cfg.log_file, offset)
        return {"text": text, "offset": new_offset, "rotated": rotated}

    @app.get("/api/updates")
    async def api_updates(request: Request):
        api_token(request)
        ctx = updates_ctx()
        return {
            "installed": ctx["installed"],
            "status": serialize.update_status(ctx["status"]),
            "steamcmd_available": ctx["steamcmd_available"],
            "steamcmd_path": ctx["steamcmd_path"],
            "server_root": ctx["server_root"],
            "local_buildid": ctx["local_buildid"],
            "update_available": ctx["update_available"],
            "process": serialize.process_info(ctx["proc"]),
            "app_id": ctx["app_id"],
            "beta": ctx["beta"],
        }

    @app.post("/api/updates/check")
    async def api_updates_check(request: Request):
        api_token(request)
        if st.steam.status.running:
            raise HTTPException(status_code=409, detail="An update is already running.")
        await st.steam.check()
        if st.steam.status.check_error:
            raise HTTPException(
                status_code=400, detail=f"Check failed: {st.steam.status.check_error}"
            )
        channel = cfg.steam_beta or "public"
        return {
            "ok": True,
            "message": f"Latest {channel} buildid: {st.steam.status.available_buildid}",
        }

    @app.post("/api/updates/run")
    async def api_updates_run(request: Request):
        tok = api_token(request)
        if st.steam.status.running:
            raise HTTPException(status_code=409, detail="An update is already running.")
        if not st.steam.available:
            raise HTTPException(
                status_code=400,
                detail="steamcmd not found. Set paths.steamcmd in config.json.",
            )
        was_running = st.pm.info().running

        async def before():
            await st.pm.stop(st.api, tok)

        async def after():
            if was_running:
                await st.pm.start()

        asyncio.create_task(st.steam.update(before, after))
        return {"ok": True, "message": "Update started. Follow the log below."}

    assets = webui / "assets"
    if assets.is_dir():
        app.mount("/assets", StaticFiles(directory=str(assets)), name="assets")

    async def spa(full_path: str = ""):
        """Serve Vite files; unknown paths fall back to index.html for client routing."""
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="not found")
        existing = _safe_webui_file(webui, full_path)
        if existing is not None:
            return FileResponse(existing)
        return FileResponse(webui / "index.html")

    @app.get("/")
    async def spa_root():
        return await spa("")

    @app.get("/{full_path:path}")
    async def spa_path(full_path: str):
        return await spa(full_path)

    return app
