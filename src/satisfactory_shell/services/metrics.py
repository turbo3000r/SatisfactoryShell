"""In-memory metrics ring buffer sampled from psutil and the game API."""

from __future__ import annotations

import asyncio
import logging
import time
from collections import deque
from dataclasses import asdict, dataclass

import psutil

from ..configs.settings import Config
from ..utils.exceptions import ApiError
from ..utils.helpers import pick
from .process_manager import ProcessManager
from .sf_client import ClientAuth, HttpsClient

log = logging.getLogger("satisfactory_shell.metrics")


@dataclass
class Sample:
    ts: float
    proc_cpu: float | None
    proc_rss_mb: float | None
    host_cpu: float
    host_mem_pct: float
    uptime_s: float
    players: int | None
    tick_rate: float | None


class MetricsCollector:
    def __init__(self, cfg: Config, pm: ProcessManager, api: HttpsClient, client_auth: ClientAuth):
        self.cfg = cfg
        self.pm = pm
        self.api = api
        self.client_auth = client_auth
        maxlen = max(10, int(cfg.metrics_history_minutes * 60 / max(cfg.metrics_interval, 1)))
        self.samples: deque[Sample] = deque(maxlen=maxlen)
        self.last_state: dict | None = None
        self.last_state_ts: float | None = None
        self.last_error: str | None = None
        self._cpu_count = psutil.cpu_count(logical=True) or 1
        self._primed_pid: int | None = None

    def snapshot(self) -> list[dict]:
        return [asdict(s) for s in self.samples]

    async def run(self) -> None:
        psutil.cpu_percent(None)
        while True:
            try:
                await self._sample()
            except Exception as exc:  # pylint: disable=broad-exception-caught
                log.debug("metrics sample failed: %s", exc)
            await asyncio.sleep(self.cfg.metrics_interval)

    async def _sample(self) -> None:
        ps = self.pm.psutil_process
        proc_cpu = proc_rss = None
        if ps is not None:
            try:
                if self._primed_pid != ps.pid:
                    ps.cpu_percent(None)
                    self._primed_pid = ps.pid
                    proc_cpu = 0.0
                else:
                    proc_cpu = ps.cpu_percent(None) / self._cpu_count
                proc_rss = ps.memory_info().rss / (1024 * 1024)
            except psutil.Error:
                pass

        players = tick = None
        if ps is not None:
            try:
                state = await self.client_auth.query_server_state()
                self.last_state = state
                self.last_state_ts = time.time()
                self.last_error = None
                players = pick(state, "numConnectedPlayers")
                tick = pick(state, "averageTickRate")
            except ApiError as exc:
                self.last_error = exc.code
        else:
            self.last_state = None

        self.samples.append(
            Sample(
                ts=time.time(),
                proc_cpu=proc_cpu,
                proc_rss_mb=proc_rss,
                host_cpu=psutil.cpu_percent(None),
                host_mem_pct=psutil.virtual_memory().percent,
                uptime_s=self.pm.info().uptime_seconds,
                players=players,
                tick_rate=tick,
            )
        )
