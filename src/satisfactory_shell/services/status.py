"""Public status, dashboard, and metrics snapshots."""

from __future__ import annotations

import platform
import time

from .. import __version__
from ..models.status import (
    BootstrapStatusResponse,
    DashboardResponse,
    GameStateResponse,
    LightweightStateResponse,
    MetricsResponse,
    MetricsSampleResponse,
    ProcessEventResponse,
    ProcessInfoResponse,
    RuntimeResponse,
    ServerStateResponse,
    StatusResponse,
)
from ..utils import paths, serialize
from ..utils.exceptions import ApiError, Unauthorized
from ..utils.helpers import pick
from .bootstrap import read_status as read_bootstrap_status
from .sf_client import SERVER_STATES, poll_lightweight
from .state import AppState
from .steamcmd import read_appmanifest, read_version_file


class StatusService:
    def __init__(self, state: AppState):
        self._state = state

    async def status(self, authed: bool) -> StatusResponse:
        snap = await self._public_snapshot()
        health = pick(snap["health"], "health", default=None)
        lightweight = serialize.lightweight(snap["lw"])
        game = serialize.game_state(snap["game_state"])
        return StatusResponse(
            authed=authed,
            state=ServerStateResponse(num=snap["state_num"], name=snap["state_name"]),
            health=health,
            api_error=snap["api_error"],
            lightweight=(
                LightweightStateResponse.model_validate(lightweight) if lightweight else None
            ),
            process=ProcessInfoResponse.model_validate(serialize.process_info(snap["proc"])),
            game_state=GameStateResponse.model_validate(game) if game else None,
            bootstrap=BootstrapStatusResponse.model_validate(snap["bootstrap"]),
            version=snap["version"],
            manifest=snap["manifest"],
            runtime=RuntimeResponse.model_validate(snap["runtime"]),
        )

    def metrics(self) -> MetricsResponse:
        return MetricsResponse(
            samples=[
                MetricsSampleResponse.model_validate(sample)
                for sample in self._state.metrics.snapshot()
            ],
            process=ProcessInfoResponse.model_validate(
                serialize.process_info(self._state.pm.info())
            ),
        )

    async def dashboard(self, token: str) -> DashboardResponse:
        ctx = await self._dashboard_ctx(token)
        game = serialize.game_state(ctx["game_state"])
        return DashboardResponse(
            state_name=ctx["state_name"],
            api_error=ctx["api_error"],
            game_state=GameStateResponse.model_validate(game) if game else None,
            options=ctx["options"] or {},
            pending=ctx["pending"] or {},
            process=ProcessInfoResponse.model_validate(serialize.process_info(ctx["proc"])),
            events=[
                ProcessEventResponse.model_validate(item)
                for item in serialize.events(ctx["events"])
            ],
        )

    async def _public_snapshot(self) -> dict:
        cfg = self._state.cfg
        lw = await poll_lightweight(cfg.game_host, cfg.game_port, timeout=0.8)
        health: dict | None = None
        game_state: dict | None = None
        api_error: str | None = None
        if lw and lw.state != 2:
            try:
                health = await self._state.api.health_check()
            except ApiError as exc:
                api_error = exc.code
            if health is not None:
                if (
                    self._state.metrics.last_state
                    and self._state.metrics.last_state_ts
                    and time.time() - self._state.metrics.last_state_ts < 30
                ):
                    game_state = self._state.metrics.last_state
                else:
                    try:
                        game_state = await self._state.client_auth.query_server_state()
                    except Unauthorized:
                        game_state = None
                    except ApiError as exc:
                        api_error = exc.code
        pinfo = self._state.pm.info()
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
                "uptime": time.time() - self._state.started_at,
                "bind": f"{cfg.webui_host}:{cfg.webui_port}",
                "config": str(cfg.file),
                "server_root": str(cfg.server_root or "not found"),
                "steamcmd": str(cfg.steamcmd or "not found"),
                "game_api": f"https://{cfg.game_host}:{cfg.game_port}/api/v1",
            },
        }

    async def _dashboard_ctx(self, token: str) -> dict:
        game_state = options = pending = None
        api_error = None
        try:
            game_state = await self._state.api.query_server_state(token)
            opts = await self._state.api.get_server_options(token)
            options = pick(opts, "serverOptions", default={}) or {}
            pending = pick(opts, "pendingServerOptions", default={}) or {}
        except Unauthorized:
            raise
        except ApiError as exc:
            api_error = exc.code
        lw = await poll_lightweight(
            self._state.cfg.game_host, self._state.cfg.game_port, timeout=0.6
        )
        return {
            "game_state": game_state,
            "options": options,
            "pending": pending,
            "api_error": api_error,
            "proc": self._state.pm.info(),
            "events": list(reversed(self._state.pm.events[-15:])),
            "lw": lw,
            "state_name": lw.state_name
            if lw
            else ("Starting" if self._state.pm.info().running else "Offline"),
        }
