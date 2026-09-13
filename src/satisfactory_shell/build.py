"""``poetry run build-exe``: freeze Satisfactory Shell into a single Windows executable."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from . import paths


def main() -> int:
    root = paths.starter_root()
    pkg = root / "src" / "satisfactory_shell"
    sep = ";" if sys.platform == "win32" else ":"
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--name",
        "satisfactory-shell",
        "--add-data",
        f"{pkg / 'templates'}{sep}satisfactory_shell/templates",
        "--add-data",
        f"{pkg / 'static'}{sep}satisfactory_shell/static",
        "--hidden-import",
        "uvicorn.logging",
        "--hidden-import",
        "uvicorn.loops.auto",
        "--hidden-import",
        "uvicorn.protocols.http.auto",
        "--hidden-import",
        "uvicorn.protocols.websockets.auto",
        "--hidden-import",
        "uvicorn.lifespan.on",
        "--paths",
        str(root / "src"),
        str(Path(__file__).with_name("launcher.py")),
    ]
    print(" ".join(cmd))
    return subprocess.call(cmd, cwd=root)


if __name__ == "__main__":
    raise SystemExit(main())
