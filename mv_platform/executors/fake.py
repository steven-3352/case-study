import os
import tempfile
import time
from pathlib import Path


def validate_input(value):
    if value is None:
        value = {}
    if not isinstance(value, dict):
        raise ValueError("executor input must be a mapping")
    allowed = {"steps", "delay_seconds", "fail_at", "artifact_text"}
    if set(value) - allowed:
        raise ValueError("unknown executor input key")
    steps = value.get("steps", 1)
    delay = value.get("delay_seconds", 0.0)
    fail_at = value.get("fail_at")
    artifact = value.get("artifact_text")
    if isinstance(steps, bool) or not isinstance(steps, int) or not 1 <= steps <= 100:
        raise ValueError("steps must be an integer from 1 through 100")
    if isinstance(delay, bool) or not isinstance(delay, (int, float)) or not 0 <= delay <= 0.2:
        raise ValueError("delay_seconds must be from 0 through 0.2")
    if fail_at is not None and (isinstance(fail_at, bool) or not isinstance(fail_at, int) or not 1 <= fail_at <= steps):
        raise ValueError("fail_at must be a step number")
    if artifact is not None and (not isinstance(artifact, str) or len(artifact) > 10000):
        raise ValueError("artifact_text must be a string of at most 10000 characters")
    return {"steps": steps, "delay_seconds": float(delay), "fail_at": fail_at, "artifact_text": artifact}


def run_fake(value, staging, cancelled, send):
    value = validate_input(value)
    for step in range(1, value["steps"] + 1):
        if cancelled.is_set():
            send({"kind": "cancelled"})
            return
        if value["delay_seconds"]:
            time.sleep(value["delay_seconds"])
        if cancelled.is_set():
            send({"kind": "cancelled"})
            return
        send({"kind": "progress", "step": step, "steps": value["steps"]})
        if value["fail_at"] == step:
            send({"kind": "failed", "error_code": "fake_failure"})
            return
    if cancelled.is_set():
        send({"kind": "cancelled"})
        return
    if value["artifact_text"] is not None:
        destination = Path(staging) / "result.txt"
        fd, temporary = tempfile.mkstemp(prefix=".result-", dir=str(staging))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(value["artifact_text"])
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, destination)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
    send({"kind": "succeeded"})
