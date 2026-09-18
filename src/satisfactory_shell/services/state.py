"""Shared application state constructed once per process."""

from __future__ import annotations

import asyncio
import time
from collections import deque
from collections.abc import Coroutine
from typing import Any

from ..configs.settings import Config
from ..utils.exceptions import ApiError
from .bootstrap import Bootstrapper
from .metrics import MetricsCollector
from .process_manager import ProcessManager
from .sf_client import ClientAuth, HttpsClient
from .steamcmd import SteamCmd


class AppState:
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

    def spawn(self, coro: Coroutine[Any, Any, Any], *, name: str | None = None) -> asyncio.Task:
        """Start a background task that shutdown will cancel."""
        task = asyncio.create_task(coro, name=name)
        self.tasks.append(task)
        task.add_done_callback(self._discard_task)
        return task

    def _discard_task(self, task: asyncio.Task) -> None:
        try:
            self.tasks.remove(task)
        except ValueError:
            pass

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
