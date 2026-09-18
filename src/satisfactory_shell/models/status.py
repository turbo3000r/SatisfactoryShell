"""Status, dashboard, and metrics schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ProcessInfoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    running: bool
    pid: int | None
    owned: bool
    started_at: float | None
    uptime_seconds: float
    last_exit_code: int | None
    last_unexpected_exit: str | None
    unexpected_exits: int
    user_stopped: bool
    auto_restart: bool
    busy: str | None


class GameStateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    session_name: str
    players: int
    player_limit: int
    tech_tier: int | None = None
    game_phase: str
    active_schematic: str
    is_running: bool
    is_paused: bool
    duration_seconds: int | float
    tick_rate: float
    auto_load_session: str


class LightweightStateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    state: int
    state_name: str
    changelist: int
    modded: bool
    server_name: str


class RuntimeResponse(BaseModel):
    app_version: str
    mode: str
    python: str
    platform: str
    uptime: float
    bind: str
    config: str
    server_root: str
    steamcmd: str
    game_api: str


class ServerStateResponse(BaseModel):
    num: int
    name: str


class BootstrapStatusResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    state: str
    message: str
    ts: str | None = None


class StatusResponse(BaseModel):
    authed: bool
    state: ServerStateResponse
    health: str | None
    api_error: str | None
    lightweight: LightweightStateResponse | None
    process: ProcessInfoResponse
    game_state: GameStateResponse | None
    bootstrap: BootstrapStatusResponse
    version: dict[str, Any]
    manifest: dict[str, Any]
    runtime: RuntimeResponse


class ProcessEventResponse(BaseModel):
    ts: str | None
    message: str


class DashboardResponse(BaseModel):
    state_name: str
    api_error: str | None
    game_state: GameStateResponse | None
    options: dict[str, Any]
    pending: dict[str, Any]
    process: ProcessInfoResponse
    events: list[ProcessEventResponse]


class MetricsSampleResponse(BaseModel):
    ts: float
    proc_cpu: float | None
    proc_rss_mb: float | None
    host_cpu: float
    host_mem_pct: float
    uptime_s: float
    players: int | None = None
    tick_rate: float | None = None


class MetricsResponse(BaseModel):
    samples: list[MetricsSampleResponse] = Field(default_factory=list)
    process: ProcessInfoResponse
