"""Locate and safely resolve files from the Vite WebUI build."""

from __future__ import annotations

from pathlib import Path

from . import paths


def webui_or_raise() -> Path:
    webui = paths.webui_dir()
    index = webui / "index.html"
    if not index.is_file():
        if paths.is_frozen():
            hint = f"Keep the webui folder next to the exe ({webui})."
        else:
            hint = "Run `npm run build` in frontend/."
        raise FileNotFoundError(f"WebUI assets not found at {index}. {hint}")
    return webui


def safe_webui_file(webui: Path, relative: str) -> Path | None:
    if not relative or relative.endswith("/"):
        return None
    candidate = (webui / relative).resolve()
    try:
        candidate.relative_to(webui.resolve())
    except ValueError:
        return None
    return candidate if candidate.is_file() else None
