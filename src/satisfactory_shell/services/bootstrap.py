"""Silent first-run claim: ``%APPDATA%\\SatisfactoryShell\\bootstrap.json``.

The installer writes this file on the “download server” path. Satisfactory Shell
retries until ClaimServer succeeds (or the server is already claimed), then deletes it.
Admin password is never copied into config.json.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Awaitable, Callable
from datetime import datetime
from pathlib import Path

from ..configs.settings import Config
from ..utils import paths
from ..utils.exceptions import ApiError, ApiUnavailable
from .sf_client import HttpsClient

log = logging.getLogger("satisfactory_shell.bootstrap")

STATES = ("none", "pending", "running", "claimed", "failed")


def bootstrap_path() -> Path:
    return paths.bootstrap_file()


def status_path(cfg: Config) -> Path:
    return cfg.data_dir / "bootstrap-status.json"


def log_path(cfg: Config) -> Path:
    return cfg.data_dir / "bootstrap.log"


def read_status(cfg: Config | None = None) -> dict:
    """Home-page status line. Missing file → no banner."""
    candidates = []
    if cfg:
        candidates.append(status_path(cfg))
    candidates.append(paths.user_data_dir() / "bootstrap-status.json")
    for p in candidates:
        if p.is_file():
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                if isinstance(data, dict) and data.get("state") not in (None, "none"):
                    return data
            except (OSError, json.JSONDecodeError):
                continue
    if bootstrap_path().is_file():
        return {
            "state": "pending",
            "message": "First-run claim will start when the server API is up.",
        }
    return {"state": "none", "message": ""}


def write_status(cfg: Config, state: str, message: str) -> None:
    cfg.data_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "state": state,
        "message": message,
        "ts": datetime.now().isoformat(timespec="seconds"),
    }
    status_path(cfg).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    line = f"{payload['ts']} [{state}] {message}\n"
    with log_path(cfg).open("a", encoding="utf-8") as fh:
        fh.write(line)
    log.info("%s: %s", state, message)


def load_job() -> dict | None:
    p = bootstrap_path()
    if not p.is_file():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def delete_job() -> None:
    p = bootstrap_path()
    try:
        p.unlink(missing_ok=True)
    except OSError as exc:
        log.warning("could not delete bootstrap.json: %s", exc)


class Bootstrapper:
    def __init__(self, cfg: Config, api: HttpsClient):
        self.cfg = cfg
        self.api = api

    async def run(self, wait_for_api: Callable[[float], Awaitable[bool]]) -> None:
        job = load_job()
        if not job:
            return
        write_status(self.cfg, "pending", "Waiting for the dedicated server HTTPS API…")
        if not await wait_for_api(600.0):
            write_status(
                self.cfg,
                "failed",
                "API did not become ready (will retry on next start).",
            )
            return
        write_status(self.cfg, "running", "Claiming the dedicated server…")
        try:
            await self._claim(job)
        except ApiUnavailable as exc:
            write_status(
                self.cfg,
                "failed",
                f"API unavailable: {exc} (will retry on next start).",
            )
        except ApiError as exc:
            write_status(
                self.cfg,
                "failed",
                f"{exc.code}: {exc.message or exc} (will retry on next start).",
            )
        except Exception as exc:  # pylint: disable=broad-exception-caught
            write_status(self.cfg, "failed", f"{exc} (will retry on next start).")

    async def _claim(self, job: dict) -> None:
        name = str(job.get("server_name") or "Satisfactory Server")
        admin = str(job.get("admin_password") or "")
        client = str(job.get("client_password") or "")
        do_claim = bool(job.get("claim", True))

        token: str | None = None
        if do_claim:
            if not admin:
                raise ApiError("bootstrap_failed", "admin_password missing from bootstrap.json")
            try:
                token = await self.api.passwordless_login("InitialAdmin")
            except ApiError as exc:
                if exc.code == "passwordless_login_not_possible":
                    write_status(
                        self.cfg,
                        "claimed",
                        "Server is already claimed; bootstrap finished.",
                    )
                    delete_job()
                    return
                raise
            try:
                new_token = await self.api.claim_server(token, name, admin)
                token = new_token or token
            except ApiError as exc:
                if exc.code == "server_claimed":
                    write_status(
                        self.cfg,
                        "claimed",
                        "Server was already claimed; admin password left unchanged.",
                    )
                    delete_job()
                    return
                raise

        if token and client:
            await self.api.set_client_password(token, client)

        if client and self.cfg.game.client_password != client:
            self.cfg.game.client_password = client
            self.cfg.save()

        write_status(
            self.cfg,
            "claimed",
            f'Server "{name}" claimed. Use the admin password on the Login page.',
        )
        delete_job()
