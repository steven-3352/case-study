"""状态层：读写 state.json、步骤状态机、hash、级联失效。

控制器唯一读懂的业务状态。其余全在文件夹里。
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from .contracts import PENDING, DONE


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return "sha256:" + h.hexdigest()[:16]


def sha256_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


class State:
    """薄封装 state.json。"""

    def __init__(self, root: Path):
        self.root = Path(root)
        self.path = self.root / "state.json"
        self.data: dict = {}

    # ---- 生命周期 ----
    def init(self, project: str, step_ids: list[str], tier: str = "standard") -> None:
        self.data = {
            "project": project,
            "created_at": _now(),
            "production_tier": tier,
            "steps": {sid: {"status": PENDING} for sid in step_ids},
            "cost": {"estimated": 0.0, "spent": 0.0, "confirmed": False, "ledger": []},
        }
        self.save()

    def load(self) -> "State":
        self.data = json.loads(self.path.read_text(encoding="utf-8"))
        return self

    def save(self) -> None:
        self.path.write_text(
            json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    # ---- 步骤读写 ----
    def step(self, sid: str) -> dict:
        return self.data["steps"][sid]

    def set_status(self, sid: str, status: str, **extra) -> None:
        self.step(sid).update(status=status, updated_at=_now(), **extra)
        self.save()

    def is_done(self, sid: str) -> bool:
        return self.step(sid).get("status") == DONE

    # ---- 级联失效：某步被打回 → 下游标回 pending ----
    def invalidate_downstream(self, sid: str, order: list[str]) -> list[str]:
        touched = []
        for later in order[order.index(sid) + 1:]:
            if self.step(later).get("status") != PENDING:
                self.set_status(later, PENDING, reason=f"upstream {sid} changed")
                touched.append(later)
        return touched
