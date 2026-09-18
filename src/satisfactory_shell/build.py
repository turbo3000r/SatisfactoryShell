"""``poetry run build-exe``: freeze Satisfactory Shell and stage the WebUI beside it."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from .utils import paths


def _npm() -> str:
    npm = shutil.which("npm") or shutil.which("npm.cmd")
    if not npm:
        raise SystemExit("npm not found. Install Node.js to build the WebUI.")
    return npm


def _run(cmd: list[str], cwd: Path) -> None:
    print(" ".join(cmd))
    code = subprocess.call(cmd, cwd=cwd)
    if code != 0:
        raise SystemExit(code)


def build_frontend(root: Path) -> Path:
    frontend = root / "frontend"
    npm = _npm()
    if not (frontend / "node_modules").is_dir():
        lock = frontend / "package-lock.json"
        _run([npm, "ci" if lock.is_file() else "install"], frontend)
    _run([npm, "run", "build"], frontend)
    dist = frontend / "dist"
    if not (dist / "index.html").is_file():
        raise SystemExit(f"frontend build did not produce {dist / 'index.html'}")
    return dist


def copy_webui(frontend_dist: Path, dest: Path) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(frontend_dist, dest)
    print(f"copied WebUI to {dest}")


def main() -> int:
    root = paths.starter_root()
    frontend_dist = build_frontend(root)
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--name",
        "satisfactory-shell",
        "--noconsole",
        "--icon",
        str(root / "assets" / "app.ico"),
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
    code = subprocess.call(cmd, cwd=root)
    if code != 0:
        return code
    copy_webui(frontend_dist, root / "dist" / "webui")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
