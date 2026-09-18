"""SteamCMD integration: installed build info, available build check, update run."""

from __future__ import annotations

import asyncio
import json
import logging
import re
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from ..configs.settings import Config

log = logging.getLogger("satisfactory_shell.steamcmd")

_ACF_KV = re.compile(r'^\s*"([^"]+)"\s+"([^"]*)"\s*$', re.M)


def read_version_file(path: Path | None) -> dict:
    if not path or not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {}


def read_appmanifest(path: Path | None) -> dict:
    """Flat top-level key/values from a Steam .acf (buildid, LastUpdated, name...)."""
    if not path or not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8", errors="replace")
    # only top-level AppState block: cut at first nested block
    head = text.split("\n\t{", 1)[0] if "\n\t{" in text else text
    out = dict(_ACF_KV.findall(head))
    for k in ("LastUpdated", "LastPlayed"):
        if out.get(k, "").isdigit():
            out[k + "_iso"] = datetime.fromtimestamp(int(out[k])).isoformat(
                sep=" ", timespec="seconds"
            )
    return out


def _parse_public_buildid(text: str, beta: str) -> str | None:
    """Pull branch buildid out of ``app_info_print`` VDF output."""
    branch = beta or "public"
    m = re.search(r'"branches"\s*\{(.*)', text, re.S)
    if not m:
        return None
    block = m.group(1)
    bm = re.search(rf'"{re.escape(branch)}"\s*\{{\s*"buildid"\s*"(\d+)"', block, re.S)
    return bm.group(1) if bm else None


@dataclass
class UpdateStatus:
    running: bool = False
    phase: str = ""
    started_at: datetime | None = None
    finished_at: datetime | None = None
    exit_code: int | None = None
    log_lines: list[str] = field(default_factory=list)
    available_buildid: str | None = None
    checked_at: datetime | None = None
    check_error: str | None = None


class SteamCmd:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.status = UpdateStatus()
        self.last_log_file = cfg.data_dir / "steamcmd-last.log"
        self._lock = asyncio.Lock()
        if self.last_log_file.is_file():
            try:
                self.status.log_lines = self.last_log_file.read_text(
                    encoding="utf-8", errors="replace"
                ).splitlines()[-500:]
            except OSError:
                pass

    @property
    def available(self) -> bool:
        return bool(self.cfg.steamcmd and self.cfg.steamcmd.is_file())

    def installed(self) -> dict:
        return {
            "version": read_version_file(self.cfg.version_file),
            "manifest": read_appmanifest(self.cfg.appmanifest),
        }

    def _run_sync(self, args: list[str], on_line) -> int:
        proc = subprocess.Popen(  # pylint: disable=consider-using-with
            [str(self.cfg.steamcmd), *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        assert proc.stdout is not None
        for line in proc.stdout:
            on_line(line.rstrip("\r\n"))
        return proc.wait()

    async def check(self) -> None:
        if not self.available:
            self.status.check_error = "steamcmd path not configured"
            return
        async with self._lock:
            lines: list[str] = []
            args = [
                "+login",
                "anonymous",
                "+app_info_update",
                "1",
                "+app_info_print",
                str(self.cfg.app_id),
                "+quit",
            ]
            self.status.phase = "checking"
            try:
                code = await asyncio.to_thread(self._run_sync, args, lines.append)
                text = "\n".join(lines)
                bid = _parse_public_buildid(text, self.cfg.steam_beta)
                self.status.available_buildid = bid
                self.status.check_error = None if bid else f"could not parse buildid (exit {code})"
            except OSError as exc:
                self.status.check_error = str(exc)
            finally:
                self.status.checked_at = datetime.now()
                self.status.phase = ""

    async def run_auto_check(self) -> None:
        """Check for a newer dedicated-server build on a configured interval."""
        while True:
            if not self.cfg.steam_auto_check:
                return
            if self.available and not self.status.running:
                try:
                    await self.check()
                    local = self.installed()["manifest"].get("buildid")
                    latest = self.status.available_buildid
                    if local and latest and local != latest:
                        log.info(
                            "Dedicated server update available: local=%s latest=%s",
                            local,
                            latest,
                        )
                except Exception as exc:  # pylint: disable=broad-exception-caught
                    log.debug("auto update check failed: %s", exc)
            hours = self.cfg.steam_check_interval_hours
            if hours <= 0:
                return
            await asyncio.sleep(hours * 3600)

    async def update(self, before, after) -> None:
        """``before`` / ``after`` are async callables (stop server / start server)."""
        if not self.available:
            raise RuntimeError("steamcmd path not configured")
        if not self.cfg.server_root:
            raise RuntimeError("server_root unresolved")
        async with self._lock:
            st = self.status
            st.running = True
            st.started_at = datetime.now()
            st.finished_at = None
            st.exit_code = None
            st.log_lines = []
            fh = self.last_log_file.open("w", encoding="utf-8")

            def on_line(line: str) -> None:
                st.log_lines.append(line)
                del st.log_lines[:-2000]
                fh.write(line + "\n")
                fh.flush()

            try:
                st.phase = "stopping server"
                on_line(f"[{time.strftime('%H:%M:%S')}] shell: stopping server")
                await before()
                args = [
                    "+force_install_dir",
                    str(self.cfg.server_root),
                    "+login",
                    "anonymous",
                    "+app_update",
                    str(self.cfg.app_id),
                ]
                if self.cfg.steam_beta:
                    args += ["-beta", self.cfg.steam_beta]
                if self.cfg.steam_validate:
                    args.append("validate")
                args.append("+quit")
                st.phase = "running steamcmd"
                on_line(
                    f"[{time.strftime('%H:%M:%S')}] shell: {self.cfg.steamcmd} {' '.join(args)}"
                )
                st.exit_code = await asyncio.to_thread(self._run_sync, args, on_line)
                on_line(f"[{time.strftime('%H:%M:%S')}] shell: steamcmd exited with {st.exit_code}")
                if any("0x606" in line for line in st.log_lines):
                    on_line(
                        "shell: state 0x606 usually means the Steam client holds this "
                        "install. Close Steam and retry."
                    )
                st.phase = "starting server"
                await after()
            except Exception as exc:  # pylint: disable=broad-exception-caught
                on_line(f"shell: update failed: {exc}")
                if st.exit_code is None:
                    st.exit_code = -1
            finally:
                fh.close()
                st.running = False
                st.phase = ""
                st.finished_at = datetime.now()
