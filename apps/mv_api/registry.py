"""Per-user service registry for the multi-user server.

Each authenticated user gets an independent :class:`ApplicationService` bound to
its own workspace directory under ``<base>/users/<user_id>/``. Services are
built lazily on first use and cached; an LRU cap bounds resident memory by
evicting the least-recently-used *idle* service (one with no active jobs).

The registry owns nothing about credentials — a user's provider keys live in
that user's own workspace settings file, never in shared process state.
"""

from __future__ import annotations

import logging
import re
import threading
import time
from pathlib import Path

from mv_platform.application.error_logs import ErrorLogStore

logger = logging.getLogger(__name__)

# user ids are minted by AuthStore as "u-" + 32 hex chars. Validate before we
# ever use one as a directory name so a poisoned id cannot escape the base.
_USER_ID_RE = re.compile(r"^u-[0-9a-f]{32}$")

_DEFAULT_MAX_RESIDENT = 32


class RegistryEntry:
    __slots__ = ("service", "error_logs", "last_access")

    def __init__(self, service, error_logs):
        self.service = service
        self.error_logs = error_logs
        self.last_access = time.monotonic()


def _has_active_jobs(service) -> bool:
    supervisor = getattr(service, "supervisor", None)
    workers = getattr(supervisor, "_workers", None)
    return bool(workers)


class UserServiceRegistry:
    """Thread-safe map of ``user_id -> ApplicationService``.

    ``build`` is injected (defaults to :func:`apps.runtime.build_service`) so the
    registry stays testable and free of import cycles.
    """

    def __init__(self, base_root, build=None, settings=None, max_resident=_DEFAULT_MAX_RESIDENT):
        self.base_root = Path(base_root).expanduser().absolute()
        self.users_root = self.base_root / "users"
        self._settings = settings
        self._max_resident = max(1, int(max_resident))
        self._entries: dict[str, RegistryEntry] = {}
        self._lock = threading.RLock()
        if build is None:
            from apps.runtime import build_service
            build = build_service
        self._build = build

    def user_workspace_root(self, user_id: str) -> Path:
        if not _USER_ID_RE.match(user_id or ""):
            raise ValueError("invalid user id")
        return self.users_root / user_id

    def get(self, user_id: str) -> RegistryEntry:
        """Return the cached entry for ``user_id``, building it on first use."""
        with self._lock:
            entry = self._entries.get(user_id)
            if entry is not None:
                entry.last_access = time.monotonic()
                return entry
            # Build under the lock: construction is local SQLite + mkdir work
            # (sub-second) and this keeps a user's very first two concurrent
            # requests from racing to create two services for the same account.
            root = self.user_workspace_root(user_id)
            logger.info("building service for user %s at %s", user_id, root)
            # Per-user pointer file, kept inside the user's own workspace, so a
            # settings save cannot repoint any shared/global workspace.
            pointer = root / ".workspace-pointer.json"
            service = self._build(
                workspace_root=root, settings=self._settings, pointer_path=pointer,
                read_process_env=False,
            )
            error_logs = None
            if hasattr(service, "workspace_root") and hasattr(service, "settings"):
                error_logs = ErrorLogStore(service.workspace_root, service.settings.data_root)
            entry = RegistryEntry(service, error_logs)
            self._entries[user_id] = entry
            self._evict_if_needed(keep=user_id)
            return entry

    def _evict_if_needed(self, keep: str) -> None:
        # Caller holds the lock.
        while len(self._entries) > self._max_resident:
            victim_id = None
            victim_access = None
            for uid, entry in self._entries.items():
                if uid == keep:
                    continue
                if _has_active_jobs(entry.service):
                    continue
                if victim_access is None or entry.last_access < victim_access:
                    victim_id, victim_access = uid, entry.last_access
            if victim_id is None:
                # Everyone else is busy; let the cap be exceeded rather than
                # killing a running job.
                return
            self._shutdown_entry(victim_id)

    def _shutdown_entry(self, user_id: str) -> None:
        entry = self._entries.pop(user_id, None)
        if entry is None:
            return
        try:
            entry.service.shutdown()
        except Exception:  # pragma: no cover - defensive; eviction must not crash a request
            logger.exception("error shutting down service for user %s", user_id)

    def tick_all(self) -> None:
        """Advance every resident supervisor once. Called by the background driver."""
        with self._lock:
            services = [e.service for e in self._entries.values()]
        for service in services:
            supervisor = getattr(service, "supervisor", None)
            tick = getattr(supervisor, "tick", None)
            if callable(tick):
                try:
                    tick()
                except Exception:  # pragma: no cover - one bad supervisor must not stall the rest
                    logger.exception("supervisor tick failed")

    def shutdown_all(self) -> None:
        with self._lock:
            for user_id in list(self._entries):
                self._shutdown_entry(user_id)
