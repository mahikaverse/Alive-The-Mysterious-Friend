"""Notification manager.

Records important runtime events (provider exhaustion, daily limit
reached, compaction events) in an in-memory ring buffer while also
emitting a structured log line for each notification.

A frontend can poll ``GET /notifications`` to surface these to the
user without needing direct log access.
"""

import logging
import threading
import time
import uuid
from typing import Any

logger = logging.getLogger(__name__)

_DEFAULT_MAX_ENTRIES: int = 100


class NotificationManager:
    """Thread-safe in-memory notification store.

    Each entry carries a level, message, source, timestamp and a
    unique id.  Entries beyond ``max_entries`` are dropped (FIFO).
    """

    def __init__(self, max_entries: int = _DEFAULT_MAX_ENTRIES) -> None:
        self._max_entries: int = max_entries
        self._lock = threading.Lock()
        self._entries: list[dict[str, Any]] = []

    def notify(
        self,
        message: str,
        level: str = "info",
        source: str = "system",
        **extra: Any,
    ) -> dict[str, Any]:
        """Record and log a notification.

        Parameters
        ----------
        message : str
            Human-readable description of the event.
        level : str
            One of ``"debug"``, ``"info"``, ``"warning"``, ``"error"``.
        source : str
            Component that produced the event (e.g. ``"llm"``).

        Returns
        -------
        dict
            The stored notification entry.
        """
        entry: dict[str, Any] = {
            "id": uuid.uuid4().hex[:12],
            "level": level,
            "message": message,
            "source": source,
            "timestamp": int(time.time()),
            **extra,
        }

        with self._lock:
            self._entries.append(entry)
            if len(self._entries) > self._max_entries:
                self._entries = self._entries[-self._max_entries:]

        log_level = getattr(logging, level.upper(), logging.INFO)
        logger.log(
            log_level,
            "[notification source=%s] %s",
            source,
            message,
        )
        return entry

    def list(self, since: int | None = None, limit: int = 50) -> list[dict[str, Any]]:
        """Return recent notifications, newest first.

        Parameters
        ----------
        since : int | None
            Only return entries with ``timestamp >= since``.
        limit : int
            Maximum number of entries to return.
        """
        with self._lock:
            entries = list(self._entries)

        entries.reverse()

        if since is not None:
            entries = [e for e in entries if e["timestamp"] >= since]

        return entries[:limit]

    def clear(self) -> None:
        """Remove all stored notifications."""
        with self._lock:
            self._entries.clear()


notification_manager = NotificationManager()
