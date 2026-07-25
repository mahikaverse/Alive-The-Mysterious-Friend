"""Request context management.

Provides a request-wide context using contextvars so that
every component in the pipeline can access the current
request ID without passing it explicitly through every call.
"""

import contextvars
import uuid
from dataclasses import dataclass, field

request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="")


def generate_request_id() -> str:
    """Return a short, unique request identifier."""
    return uuid.uuid4().hex[:12]


def get_current_request_id() -> str:
    """Return the request ID active in the current context, or empty string."""
    return request_id_var.get()


def set_request_id(rid: str) -> contextvars.Token:
    """Set the request ID for the current execution context.

    Returns a Token that can be used to restore the previous value.
    """
    return request_id_var.set(rid)


def reset_request_id(token: contextvars.Token) -> None:
    """Restore the previous request ID using a stored Token."""
    request_id_var.reset(token)


@dataclass
class RequestContext:
    """Holds metadata for a single API request lifecycle."""

    request_id: str = field(default_factory=generate_request_id)
    start_time: float = 0.0
