"""Domain exceptions mapped to HTTP responses in the application factory."""

from __future__ import annotations

from typing import Any


class ApiError(Exception):
    """Failure returned by the dedicated-server HTTPS API."""

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


class AppError(Exception):
    """Application error mapped to ``{"detail": message}`` with ``status_code``."""

    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def api_error_http_status(exc: ApiError) -> int:
    """HTTP status used for an ``ApiError`` raised from a route."""
    if isinstance(exc, Unauthorized):
        return 401
    if isinstance(exc, ApiUnavailable):
        return 503
    return 400
