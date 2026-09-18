"""Satisfactory Dedicated Server API clients.

* HTTPS JSON-RPC ``POST https://host:port/api/v1`` (self-signed TLS, Bearer tokens)
* UDP Lightweight Query on the same port (state / changelist / server name)
"""

from __future__ import annotations

import asyncio
import json
import socket
import struct
import time
from dataclasses import dataclass, field
from typing import Any

import httpx

SERVER_STATES = {0: "Offline", 1: "Idle", 2: "Loading", 3: "Playing"}
PRIVILEGE_ADMIN = "Administrator"


class ApiError(Exception):
    def __init__(self, code: str, message: str = "", status: int = 0, data: Any = None):
        super().__init__(f"{code}: {message}" if message else code)
        self.code = code
        self.message = message
        self.status = status
        self.data = data


class ApiUnavailable(ApiError):
    """Connection refused / reset: server offline (state 0) or loading (state 2)."""

    def __init__(self, reason: str):
        super().__init__("api_unavailable", reason)


class Unauthorized(ApiError):
    """401 (missing/expired token) or 403 (insufficient privilege)."""

    def __init__(self, message: str = "token missing, invalid or expired", status: int = 401):
        super().__init__("unauthorized" if status == 401 else "forbidden", message, status=status)


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


@dataclass
class ApiResponse:
    status: int
    body: Any
    content: bytes = b""
    headers: dict[str, str] = field(default_factory=dict)

    @property
    def data(self) -> dict:
        return pick(self.body, "data", default={}) or {}


class HttpsClient:
    def __init__(self, host: str, port: int, timeout: float = 30.0):
        self.host = host
        self.port = port
        self.url = f"https://{host}:{port}/api/v1"
        self._client = httpx.AsyncClient(verify=False, timeout=timeout)

    async def aclose(self) -> None:
        await self._client.aclose()

    # -- core --------------------------------------------------------------
    async def call(
        self,
        function: str,
        data: dict | None = None,
        token: str | None = None,
        *,
        raw: bool = False,
    ) -> ApiResponse:
        headers = {"Content-Type": "application/json; charset=utf-8"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        payload = {"function": function, "data": data or {}}
        try:
            resp = await self._client.post(
                self.url, content=json.dumps(payload).encode("utf-8"), headers=headers
            )
        except (
            httpx.ConnectError,
            httpx.ReadError,
            httpx.RemoteProtocolError,
            httpx.ConnectTimeout,
        ) as exc:
            raise ApiUnavailable(str(exc) or exc.__class__.__name__) from exc
        return self._handle(resp, raw=raw)

    async def call_multipart(
        self, function: str, data: dict, token: str, filename: str, file_bytes: bytes
    ) -> ApiResponse:
        headers = {"Authorization": f"Bearer {token}"}
        envelope = json.dumps({"function": function, "data": data})
        files = {
            "data": (None, envelope, "application/json"),
            "saveGameFile": (filename, file_bytes, "application/octet-stream"),
        }
        try:
            resp = await self._client.post(self.url, files=files, headers=headers, timeout=300.0)
        except (
            httpx.ConnectError,
            httpx.ReadError,
            httpx.RemoteProtocolError,
            httpx.ConnectTimeout,
        ) as exc:
            raise ApiUnavailable(str(exc) or exc.__class__.__name__) from exc
        return self._handle(resp)

    def _handle(self, resp: httpx.Response, *, raw: bool = False) -> ApiResponse:
        ctype = resp.headers.get("content-type", "")
        content = resp.content
        body: Any = None
        if content and ("json" in ctype or (not raw and content[:1] in (b"{", b"["))):
            try:
                body = json.loads(content.decode("utf-8"))
            except json.JSONDecodeError:
                body = None
        if resp.status_code in (401, 403):
            raise Unauthorized(
                pick(body, "errorMessage", default="") or "", status=resp.status_code
            )
        if body and isinstance(body, dict) and pick(body, "errorCode"):
            raise ApiError(
                pick(body, "errorCode"),
                pick(body, "errorMessage", default="") or "",
                status=resp.status_code,
                data=pick(body, "errorData"),
            )
        if resp.status_code >= 400:
            raise ApiError(
                "http_error",
                content.decode("utf-8", "replace")[:300],
                status=resp.status_code,
            )
        return ApiResponse(resp.status_code, body, content, dict(resp.headers))

    # -- helpers -----------------------------------------------------------
    async def health_check(self) -> dict:
        r = await self.call("HealthCheck", {"ClientCustomData": ""})
        return r.data

    async def password_login(self, password: str, privilege: str = PRIVILEGE_ADMIN) -> str:
        r = await self.call(
            "PasswordLogin", {"MinimumPrivilegeLevel": privilege, "Password": password}
        )
        token = pick(r.data, "authenticationToken")
        if not token:
            raise ApiError("no_token", "login returned no authenticationToken")
        return token

    async def passwordless_login(self, privilege: str = PRIVILEGE_ADMIN) -> str:
        r = await self.call("PasswordlessLogin", {"MinimumPrivilegeLevel": privilege})
        token = pick(r.data, "authenticationToken")
        if not token:
            raise ApiError("no_token", "login returned no authenticationToken")
        return token

    async def verify_token(self, token: str) -> bool:
        try:
            await self.call("VerifyAuthenticationToken", {}, token)
            return True
        except Unauthorized:
            return False

    async def query_server_state(self, token: str | None = None) -> dict:
        r = await self.call("QueryServerState", {}, token)
        return pick(r.data, "serverGameState", default={}) or {}

    async def get_server_options(self, token: str | None = None) -> dict:
        r = await self.call("GetServerOptions", {}, token)
        return r.data

    async def get_advanced_game_settings(self, token: str) -> dict:
        r = await self.call("GetAdvancedGameSettings", {}, token)
        return r.data

    async def enumerate_sessions(self, token: str) -> dict:
        r = await self.call("EnumerateSessions", {}, token)
        return r.data

    async def save_game(self, token: str, name: str) -> None:
        await self.call("SaveGame", {"SaveName": name}, token)

    async def load_game(self, token: str, name: str, ags: bool = False) -> int:
        r = await self.call(
            "LoadGame", {"SaveName": name, "EnableAdvancedGameSettings": ags}, token
        )
        return r.status

    async def delete_save_file(self, token: str, name: str) -> None:
        await self.call("DeleteSaveFile", {"SaveName": name}, token)

    async def delete_save_session(self, token: str, session: str) -> None:
        await self.call("DeleteSaveSession", {"SessionName": session}, token)

    async def download_save(self, token: str, name: str) -> bytes:
        r = await self.call("DownloadSaveGame", {"SaveName": name}, token, raw=True)
        return r.content

    async def upload_save(
        self, token: str, name: str, file_bytes: bytes, load: bool, ags: bool
    ) -> int:
        r = await self.call_multipart(
            "UploadSaveGame",
            {"SaveName": name, "LoadSaveGame": load, "EnableAdvancedGameSettings": ags},
            token,
            f"{name}.sav",
            file_bytes,
        )
        return r.status

    async def create_new_game(
        self, token: str, session: str, map_name: str = "", start: str = ""
    ) -> int:
        data = {"SessionName": session, "SkipOnboarding": True}
        if map_name:
            data["MapName"] = map_name
        if start:
            data["StartingLocation"] = start
        r = await self.call("CreateNewGame", {"NewGameData": data}, token)
        return r.status

    async def set_auto_load(self, token: str, session: str) -> None:
        await self.call("SetAutoLoadSessionName", {"SessionName": session}, token)

    async def claim_server(self, token: str, name: str, admin_password: str) -> str | None:
        r = await self.call(
            "ClaimServer", {"ServerName": name, "AdminPassword": admin_password}, token
        )
        return pick(r.data, "authenticationToken")

    async def set_client_password(self, token: str, password: str) -> None:
        await self.call("SetClientPassword", {"Password": password}, token)

    async def run_command(self, token: str, command: str) -> str:
        r = await self.call("RunCommand", {"Command": command}, token)
        return pick(r.data, "commandResult", default="") or ""

    async def shutdown(self, token: str) -> None:
        await self.call("Shutdown", {}, token)


# ---------------------------------------------------------------------------
# Lightweight Query API (UDP)
# ---------------------------------------------------------------------------

_MAGIC = 0xF6D5
_MSG_POLL = 0
_MSG_RESPONSE = 1
_PROTOCOL = 1


@dataclass
class LightweightState:
    state: int
    changelist: int
    flags: int
    sub_states: dict[int, int]
    server_name: str

    @property
    def state_name(self) -> str:
        return SERVER_STATES.get(self.state, f"Unknown({self.state})")

    @property
    def modded(self) -> bool:
        return bool(self.flags & 1)


def _build_poll(cookie: int) -> bytes:
    return struct.pack("<HBBQ", _MAGIC, _MSG_POLL, _PROTOCOL, cookie) + b"\x01"


def _parse_response(buf: bytes, cookie: int) -> LightweightState | None:
    if len(buf) < 4 + 8 + 1 + 4 + 8 + 1:
        return None
    magic, msg_type, _proto = struct.unpack_from("<HBB", buf, 0)
    if magic != _MAGIC or msg_type != _MSG_RESPONSE:
        return None
    off = 4
    (resp_cookie,) = struct.unpack_from("<Q", buf, off)
    off += 8
    if resp_cookie != cookie:
        return None
    state = buf[off]
    off += 1
    (changelist,) = struct.unpack_from("<I", buf, off)
    off += 4
    (flags,) = struct.unpack_from("<Q", buf, off)
    off += 8
    n_sub = buf[off]
    off += 1
    subs: dict[int, int] = {}
    for _ in range(n_sub):
        if off + 3 > len(buf):
            break
        sid = buf[off]
        (ver,) = struct.unpack_from("<H", buf, off + 1)
        subs[sid] = ver
        off += 3
    name = ""
    if off + 2 <= len(buf):
        (name_len,) = struct.unpack_from("<H", buf, off)
        off += 2
        name = buf[off : off + name_len].decode("utf-8", "replace")
    return LightweightState(state, changelist, flags, subs, name)


def poll_lightweight_sync(host: str, port: int, timeout: float = 1.0) -> LightweightState | None:
    cookie = time.time_ns() & 0xFFFFFFFFFFFFFFFF
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(timeout)
    try:
        sock.sendto(_build_poll(cookie), (host, port))
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                buf, _ = sock.recvfrom(4096)
            except socket.timeout:
                return None
            parsed = _parse_response(buf, cookie)
            if parsed:
                return parsed
        return None
    except OSError:
        return None
    finally:
        sock.close()


async def poll_lightweight(host: str, port: int, timeout: float = 1.0) -> LightweightState | None:
    return await asyncio.to_thread(poll_lightweight_sync, host, port, timeout)


class ClientAuth:
    """Cached Client-privilege token from ``game.client_password`` (PasswordLogin).

    Used for public read calls such as QueryServerState so Home/metrics do not
    need an admin session. The password is never returned to callers.
    """

    def __init__(self, api: HttpsClient, password: str = ""):
        self.api = api
        self._password = password
        self.token: str | None = None
        self.last_error: str | None = None
        self._lock = asyncio.Lock()

    @property
    def configured(self) -> bool:
        return bool(self._password)

    async def login(self) -> str | None:
        if not self._password:
            return None
        async with self._lock:
            try:
                self.token = await self.api.password_login(self._password, privilege="Client")
                self.last_error = None
                return self.token
            except ApiError as exc:
                self.last_error = exc.code
                self.token = None
                return None

    async def query_server_state(self) -> dict:
        token = self.token
        if token is None:
            token = await self.login()
        try:
            return await self.api.query_server_state(token)
        except Unauthorized:
            token = await self.login()
            return await self.api.query_server_state(token)
