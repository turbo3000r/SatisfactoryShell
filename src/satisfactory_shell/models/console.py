"""In-game console schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class ConsoleEntryResponse(BaseModel):
    ts: str
    command: str
    result: str
    error: str


class ConsoleLogResponse(BaseModel):
    text: str
    offset: int


class ConsoleResponse(BaseModel):
    history: list[ConsoleEntryResponse] = Field(default_factory=list)
    log: ConsoleLogResponse
    log_file: str


class ConsoleRunRequest(BaseModel):
    command: str

    @field_validator("command")
    @classmethod
    def _command(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("command is required")
        return stripped


class ConsoleRunResponse(BaseModel):
    history: list[ConsoleEntryResponse] = Field(default_factory=list)


class TailResponse(BaseModel):
    text: str
    offset: int
    rotated: bool
