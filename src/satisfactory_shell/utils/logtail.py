"""Byte-offset tail of FactoryGame.log (UE writes UTF-8, sometimes with BOM)."""

from __future__ import annotations

from pathlib import Path

MAX_INITIAL = 64 * 1024


def read_tail(path: Path | None, offset: int | None = None) -> tuple[str, int, bool]:
    """Return (text, new_offset, rotated).

    ``offset=None`` returns the last MAX_INITIAL bytes. If the file shrank
    (rotation on server start) we restart from the beginning.
    """
    if not path or not path.is_file():
        return "", 0, False
    size = path.stat().st_size
    rotated = False
    if offset is None or offset > size:
        rotated = offset is not None and offset > size
        offset = max(0, size - MAX_INITIAL) if offset is None else 0
    with path.open("rb") as fh:
        fh.seek(offset)
        data = fh.read()
    text = data.decode("utf-8", "replace").lstrip("\ufeff")
    if offset == 0 and size > MAX_INITIAL and not rotated:
        # skip partial first line
        text = text.split("\n", 1)[-1]
    return text, offset + len(data), rotated
