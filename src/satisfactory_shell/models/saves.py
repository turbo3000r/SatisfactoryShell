"""Save-game request and response schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .status import GameStateResponse


class SaveHeaderResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    saveName: str
    sessionName: str
    playDuration: int | float | None = 0
    saveDateTime: str = ""
    mapName: str = ""
    buildVersion: str | int | None = ""
    saveVersion: str | int | None = ""
    modded: bool = False
    edited: bool = False
    creative: bool = False


class SaveSessionResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    sessionName: str
    headers: list[SaveHeaderResponse] = Field(default_factory=list)


class SavesResponse(BaseModel):
    sessions: list[SaveSessionResponse]
    current_index: int | None = -1
    api_error: str | None
    is_playing: bool
    game_state: GameStateResponse | None


def _required_str(value: str, name: str) -> str:
    stripped = value.strip()
    if not stripped:
        raise ValueError(f"{name} is required")
    return stripped


class SaveNameRequest(BaseModel):
    save_name: str

    @field_validator("save_name")
    @classmethod
    def _save_name(cls, value: str) -> str:
        return _required_str(value, "save_name")


class LoadSaveRequest(BaseModel):
    save_name: str
    ags: bool = False

    @field_validator("save_name")
    @classmethod
    def _save_name(cls, value: str) -> str:
        return _required_str(value, "save_name")


class NewGameRequest(BaseModel):
    session_name: str
    map_name: str = ""
    starting_location: str = ""

    @field_validator("session_name")
    @classmethod
    def _session_name(cls, value: str) -> str:
        return _required_str(value, "session_name")


class SessionNameRequest(BaseModel):
    session_name: str

    @field_validator("session_name")
    @classmethod
    def _session_name(cls, value: str) -> str:
        return _required_str(value, "session_name")
