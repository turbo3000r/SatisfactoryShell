"""Session and login schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    password: str = ""


class LoginResponse(BaseModel):
    authed: bool


class LogoutResponse(BaseModel):
    authed: bool


class SessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    authed: bool
    login_at: str | None = None
    app_version: str = Field(min_length=0)
