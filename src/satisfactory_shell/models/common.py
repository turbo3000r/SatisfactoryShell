"""Shared API response schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ActionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ok: bool
    message: str
