"""SteamCMD check and update orchestration."""

from __future__ import annotations

from ..models.common import ActionResponse
from ..models.status import ProcessInfoResponse
from ..models.updates import InstalledInfoResponse, UpdatesResponse, UpdateStatusResponse
from ..utils import serialize
from ..utils.exceptions import AppError
from .state import AppState


class UpdatesService:
    def __init__(self, state: AppState):
        self._state = state

    def snapshot(self) -> UpdatesResponse:
        ctx = self._updates_ctx()
        return UpdatesResponse(
            installed=InstalledInfoResponse.model_validate(ctx["installed"]),
            status=UpdateStatusResponse.model_validate(serialize.update_status(ctx["status"])),
            steamcmd_available=ctx["steamcmd_available"],
            steamcmd_path=ctx["steamcmd_path"],
            server_root=ctx["server_root"],
            local_buildid=ctx["local_buildid"],
            update_available=ctx["update_available"],
            process=ProcessInfoResponse.model_validate(serialize.process_info(ctx["proc"])),
            app_id=ctx["app_id"],
            beta=ctx["beta"],
            auto_check=ctx["auto_check"],
            check_interval_hours=ctx["check_interval_hours"],
        )

    async def check(self) -> ActionResponse:
        if self._state.steam.status.running:
            raise AppError("An update is already running.", status_code=409)
        await self._state.steam.check()
        if self._state.steam.status.check_error:
            raise AppError(
                f"Check failed: {self._state.steam.status.check_error}",
                status_code=400,
            )
        channel = self._state.cfg.steam_beta or "public"
        return ActionResponse(
            ok=True,
            message=f"Latest {channel} buildid: {self._state.steam.status.available_buildid}",
        )

    async def run(self, token: str) -> ActionResponse:
        if self._state.steam.status.running:
            raise AppError("An update is already running.", status_code=409)
        if not self._state.steam.available:
            raise AppError(
                "steamcmd not found. Set paths.steamcmd in config.json.",
                status_code=400,
            )
        was_running = self._state.pm.info().running

        async def before() -> None:
            await self._state.pm.stop(self._state.api, token)

        async def after() -> None:
            if was_running:
                await self._state.pm.start()

        self._state.spawn(self._state.steam.update(before, after), name="steam-update")
        return ActionResponse(ok=True, message="Update started. Follow the log below.")

    def _updates_ctx(self) -> dict:
        inst = self._state.steam.installed()
        local_bid = inst["manifest"].get("buildid")
        avail = self._state.steam.status.available_buildid
        cfg = self._state.cfg
        return {
            "installed": inst,
            "status": self._state.steam.status,
            "steamcmd_available": self._state.steam.available,
            "steamcmd_path": str(cfg.steamcmd or ""),
            "server_root": str(cfg.server_root or ""),
            "local_buildid": local_bid,
            "update_available": bool(avail and local_bid and avail != local_bid),
            "proc": self._state.pm.info(),
            "app_id": cfg.app_id,
            "beta": cfg.steam_beta,
            "auto_check": cfg.steam_auto_check,
            "check_interval_hours": cfg.steam_check_interval_hours,
        }
