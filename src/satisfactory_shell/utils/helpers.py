"""Small shared helpers used by the game client and response shaping."""

from __future__ import annotations

from typing import Any


def pick(obj: dict | None, *names: str, default: Any = None) -> Any:
    """Case-insensitive key lookup (server mixes PascalCase and camelCase)."""
    if not obj:
        return default
    lower = {k.lower(): v for k, v in obj.items()}
    for name in names:
        if name in obj:
            return obj[name]
        if name.lower() in lower:
            return lower[name.lower()]
    return default
