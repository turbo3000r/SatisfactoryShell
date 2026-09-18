"""SteamCMD update schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from .status import ProcessInfoResponse


class UpdateStatusResponse(BaseModel):
    running: bool
    phase: str
    started_at: str | None
    finished_at: str | None
    exit_code: int | None
    log_lines: list[str] = Field(default_factory=list)
    available_buildid: str | None
    checked_at: str | None
    check_error: str | None


class InstalledInfoResponse(BaseModel):
    version: dict[str, Any] = Field(default_factory=dict)
    manifest: dict[str, Any] = Field(default_factory=dict)


class UpdatesResponse(BaseModel):
    installed: InstalledInfoResponse
    status: UpdateStatusResponse
    steamcmd_available: bool
    steamcmd_path: str
    server_root: str
    local_buildid: str | None
    update_available: bool
    process: ProcessInfoResponse
    app_id: int
    beta: str
