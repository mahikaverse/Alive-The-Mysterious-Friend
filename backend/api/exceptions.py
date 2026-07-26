"""HTTP exception classes.

Maps application errors to standardised HTTP status codes
as documented in API.md §17.
"""

from typing import Any


class AppException(Exception):
    """Base exception for all application-level errors."""

    status_code: int = 500
    detail: str = "Internal server error."
    extra: dict[str, Any] | None = None

    def __init__(self, detail: str | None = None, extra: dict[str, Any] | None = None) -> None:
        if detail is not None:
            self.detail = detail
        self.extra = extra
        super().__init__(self.detail)


class BadRequestException(AppException):
    """400 Bad Request."""

    status_code = 400
    detail = "Invalid request format."


class UnauthorizedException(AppException):
    """401 Unauthorized."""

    status_code = 401
    detail = "Unauthorized."


class NotFoundException(AppException):
    """404 Not Found."""

    status_code = 404
    detail = "Endpoint not found."


class RateLimitException(AppException):
    """429 Too Many Requests."""

    status_code = 429
    detail = "Rate limit exceeded."


class InternalErrorException(AppException):
    """500 Internal Server Error."""

    status_code = 500
    detail = "Internal server error."
