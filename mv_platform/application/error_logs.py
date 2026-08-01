import json
import os
import re
import threading
from datetime import datetime
from pathlib import Path


_SECRET_KEY = re.compile(r"(api[-_]?key|authorization|password|secret|token)", re.IGNORECASE)
_SECRET_VALUE = re.compile(r"\b(sk-[A-Za-z0-9_-]{6,}|Bearer\s+\S+)", re.IGNORECASE)


class ErrorLogStore:
    """Append-only, local daily error logs for the Web application."""

    def __init__(self, workspace_root, data_root=".mvstudio"):
        workspace = Path(workspace_root).resolve()
        self.root = workspace / data_root / "logs"
        try:
            self.root.resolve().relative_to(workspace)
        except ValueError as exc:
            raise OSError("error log path escapes workspace") from exc
        self._lock = threading.Lock()

    @staticmethod
    def _clean(value, key=""):
        if _SECRET_KEY.search(str(key)):
            return "[REDACTED]"
        if isinstance(value, dict):
            return {str(item_key): ErrorLogStore._clean(item, item_key) for item_key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [ErrorLogStore._clean(item) for item in value[:100]]
        if isinstance(value, str):
            return _SECRET_VALUE.sub("[REDACTED]", value)[:12000]
        if value is None or isinstance(value, (bool, int, float)):
            return value
        return ErrorLogStore._clean(str(value))

    def _path(self, source, now=None):
        if source not in {"backend", "frontend"}:
            raise ValueError("invalid error log source")
        current = now or datetime.now().astimezone()
        return self.root / f"{source}-{current.date().isoformat()}.jsonl"

    def paths(self):
        return {
            "directory": str(self.root),
            "backend": str(self._path("backend")),
            "frontend": str(self._path("frontend")),
        }

    def append(self, source, event):
        path = self._path(source)
        record = {
            "timestamp": datetime.now().astimezone().isoformat(),
            "source": source,
            **self._clean(dict(event)),
        }
        line = json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
        with self._lock:
            self.root.mkdir(parents=True, exist_ok=True)
            if self.root.is_symlink() or path.is_symlink():
                raise OSError("error log path is unsafe")
            flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND
            if hasattr(os, "O_NOFOLLOW"):
                flags |= os.O_NOFOLLOW
            fd = os.open(path, flags, 0o600)
            try:
                os.write(fd, line.encode("utf-8"))
                os.fsync(fd)
            finally:
                os.close(fd)
        return str(path)
