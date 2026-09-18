"""FactoryServer.exe lifecycle: start / stop / restart / crash watchdog."""

from __future__ import annotations

import asyncio
import logging
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import psutil

from .config import Config
from .sf_client import ApiError, HttpsClient

log = logging.getLogger("satisfactory_shell.process")


@dataclass
class ProcessInfo:
    running: bool
    pid: int | None
    owned: bool
    started_at: float | None
    uptime_seconds: float
    last_exit_code: int | None
    last_unexpected_exit: datetime | None
    unexpected_exits: int
    user_stopped: bool
    auto_restart: bool
    busy: str | None


class ProcessManager:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self._proc: subprocess.Popen | None = None
        self._ps: psutil.Process | None = None
        self._owned = False
        self._started_at: float | None = None
        self._user_stopped = False
        self._last_exit_code: int | None = None
        self._last_unexpected_exit: datetime | None = None
        self._unexpected_exits = 0
        self._busy: str | None = None
        self._lock = asyncio.Lock()
        self._watch_task: asyncio.Task | None = None
        self.events: list[tuple[datetime, str]] = []

    # ------------------------------------------------------------------ info
    def _record(self, msg: str) -> None:
        log.info(msg)
        self.events.append((datetime.now(), msg))
        del self.events[:-50]

    @property
    def psutil_process(self) -> psutil.Process | None:
        if self._ps is not None:
            try:
                if self._ps.is_running() and self._ps.status() != psutil.STATUS_ZOMBIE:
                    return self._ps
            except psutil.Error:
                pass
            self._ps = None
        return None

    def is_running(self) -> bool:
        return self.psutil_process is not None

    def info(self) -> ProcessInfo:
        running = self.is_running()
        pid = self._ps.pid if running and self._ps else None
        return ProcessInfo(
            running=running,
            pid=pid,
            owned=self._owned and running,
            started_at=self._started_at if running else None,
            uptime_seconds=(time.time() - self._started_at)
            if running and self._started_at
            else 0.0,
            last_exit_code=self._last_exit_code,
            last_unexpected_exit=self._last_unexpected_exit,
            unexpected_exits=self._unexpected_exits,
            user_stopped=self._user_stopped,
            auto_restart=self.cfg.auto_restart,
            busy=self._busy,
        )

    # ------------------------------------------------------------- discovery
    def adopt_existing(self) -> bool:
        """Attach to a FactoryServer.exe that someone else started (e.g. old launch.bat)."""
        exe = self.cfg.server_exe
        if not exe:
            return False
        want = f"-Port={self.cfg.game_port}".lower()
        for p in psutil.process_iter(["name", "exe", "cmdline", "create_time"]):
            try:
                name = (p.info["name"] or "").lower()
                if not name.startswith("factoryserver"):
                    continue
                cmd = " ".join(p.info["cmdline"] or []).lower()
                exe_path = p.info["exe"] or ""
                same_install = exe_path and Path(exe_path).resolve().is_relative_to(
                    exe.parent.resolve()
                )
                if same_install or want in cmd:
                    self._ps = p
                    self._owned = False
                    self._started_at = p.info["create_time"]
                    self._record(f"Adopted existing FactoryServer.exe pid={p.pid}")
                    return True
            except (psutil.Error, OSError, ValueError):
                continue
        return False

    # ---------------------------------------------------------------- start
    async def start(self) -> None:
        async with self._lock:
            if self.is_running():
                return
            if self.adopt_existing():
                self._user_stopped = False
                return
            exe = self.cfg.server_exe
            if not exe or not exe.is_file():
                raise RuntimeError(
                    f"FactoryServer.exe not found (server_root={self.cfg.server_root})"
                )
            args = [
                str(exe),
                f"-Port={self.cfg.game_port}",
                f"-ReliablePort={self.cfg.reliable_port}",
                *self.cfg.extra_args,
            ]
            self._busy = "starting"
            try:
                creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) | getattr(
                    subprocess, "CREATE_NO_WINDOW", 0
                )
                self._proc = subprocess.Popen(  # pylint: disable=consider-using-with
                    args, cwd=str(exe.parent), creationflags=creationflags
                )
                self._ps = psutil.Process(self._proc.pid)
                self._owned = True
                self._started_at = time.time()
                self._user_stopped = False
                self._record(
                    f"Started FactoryServer.exe pid={self._proc.pid}: {' '.join(args[1:])}"
                )
            finally:
                self._busy = None

    # ----------------------------------------------------------------- stop
    async def stop(self, api: HttpsClient | None = None, token: str | None = None) -> None:
        async with self._lock:
            self._user_stopped = True
            ps = self.psutil_process
            if ps is None:
                return
            self._busy = "stopping"
            try:
                graceful = False
                if api and token:
                    try:
                        await api.shutdown(token)
                        graceful = True
                        self._record("Sent HTTPS Shutdown")
                    except ApiError as exc:
                        self._record(
                            f"HTTPS Shutdown failed ({exc.code}); falling back to terminate"
                        )
                if not graceful:
                    ps.terminate()
                    self._record("Sent terminate()")
                deadline = time.monotonic() + self.cfg.shutdown_timeout
                while time.monotonic() < deadline and ps.is_running():
                    await asyncio.sleep(0.5)
                if ps.is_running():
                    ps.kill()
                    self._record("Process did not exit in time; killed")
                    await asyncio.sleep(0.5)
            except psutil.Error:
                pass
            finally:
                self._collect_exit(expected=True)
                self._busy = None

    async def restart(self, api: HttpsClient | None = None, token: str | None = None) -> None:
        await self.stop(api, token)
        await asyncio.sleep(1.0)
        await self.start()

    def _collect_exit(self, *, expected: bool) -> None:
        code: int | None = None
        if self._proc is not None:
            code = self._proc.poll()
            self._proc = None
        self._last_exit_code = code
        self._ps = None
        self._owned = False
        if not expected:
            self._unexpected_exits += 1
            self._last_unexpected_exit = datetime.now()
            self._record(f"FactoryServer.exe exited unexpectedly (code={code})")
        else:
            self._record(f"FactoryServer.exe stopped (code={code})")

    # ------------------------------------------------------------- watchdog
    async def run_watchdog(self) -> None:
        """Background task: auto-start once, then restart on unexpected exit."""
        if self.cfg.auto_start:
            try:
                await self.start()
            except Exception as exc:  # pylint: disable=broad-exception-caught
                self._record(f"Auto-start failed: {exc}")
        else:
            self.adopt_existing()
        while True:
            await asyncio.sleep(2.0)
            if self._busy or self._lock.locked():
                continue
            if self._ps is not None and not self.is_running():
                # died without stop() being called
                self._collect_exit(expected=self._user_stopped)
                if self.cfg.auto_restart and not self._user_stopped:
                    self._record(f"Restarting in {self.cfg.restart_delay:.0f}s")
                    await asyncio.sleep(self.cfg.restart_delay)
                    try:
                        await self.start()
                    except Exception as exc:  # pylint: disable=broad-exception-caught
                        self._record(f"Auto-restart failed: {exc}")

    def set_auto_restart(self, value: bool) -> None:
        self.cfg.auto_restart = value
        self.cfg.save()
        self._record(f"auto_restart={'on' if value else 'off'}")
