"""状态层：读写 state.json、步骤状态机、hash、级联失效。

控制器唯一读懂的业务状态。其余全在文件夹里。
"""
from __future__ import annotations

import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .contracts import (
    AWAITING,
    DONE,
    FAILED_RETRYABLE,
    PENDING,
    RUNNING,
    STALE,
)


# 业务字段变化的最小失效边界。调用方只声明“什么变了”，不自行改 state.json。
# shot_action 由已确认的分镜局部修改触发，因此保留 00-02，只重做该镜生产链。
INVALIDATION_RULES: dict[str, tuple[str, ...]] = {
    "materials": (
        "00_intake", "01_analysis", "02_storyboard",
        "03_keyframes", "04_shots", "05_delivery",
    ),
    "core_selling_point": (
        "01_analysis", "02_storyboard", "03_keyframes", "04_shots", "05_delivery",
    ),
    "storyboard": ("02_storyboard", "03_keyframes", "04_shots", "05_delivery"),
    "shot_action": ("03_keyframes", "04_shots", "05_delivery"),
}

_UNSET = object()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha256_file(path: Path) -> str:
    from mvstudio.media import sha256_file as shared_sha256_file
    return shared_sha256_file(path)


def sha256_text(text: str) -> str:
    from mvstudio.media import sha256_bytes
    return sha256_bytes(text.encode("utf-8"))


class State:
    """薄封装 state.json。"""

    def __init__(self, root: Path):
        self.root = Path(root)
        self.path = self.root / "state.json"
        self.events_path = self.root / "conversation.jsonl"
        self.data: dict = {}

    # ---- 生命周期 ----
    def init(self, project: str, step_ids: list[str], tier: str = "standard") -> None:
        self.data = {
            "schema_version": 2,
            "project": project,
            "created_at": _now(),
            "production_tier": tier,
            "steps": {sid: {"status": PENDING} for sid in step_ids},
            "cost": {
                "currency": "USD",
                "hard_limit": None,
                "estimated": 0.0,
                "spent": 0.0,
                "confirmed": False,
                "paused": False,
                "ledger": [],
            },
        }
        self.save()
        self.append_event("project_initialized", project=project, tier=tier)

    def load(self) -> "State":
        self.data = json.loads(self.path.read_text(encoding="utf-8"))
        return self

    def save(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_name(f".{self.path.name}.{os.getpid()}.tmp")
        temp.write_text(
            json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        temp.replace(self.path)

    def append_event(self, event: str, **payload) -> None:
        """追加事件；事件流不回写，退出时也不会丢掉既有历史。"""
        self.root.mkdir(parents=True, exist_ok=True)
        row = {"at": _now(), "event": event, **payload}
        with self.events_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

    # ---- 步骤读写 ----
    def step(self, sid: str) -> dict:
        return self.data["steps"][sid]

    def set_status(self, sid: str, status: str, **extra) -> None:
        previous = self.step(sid).get("status")
        self.step(sid).update(status=status, updated_at=_now(), **extra)
        self.save()
        self.append_event(
            "step_status_changed", step_id=sid, previous=previous,
            status=status, details=extra,
        )

    def is_done(self, sid: str) -> bool:
        return self.step(sid).get("status") == DONE

    def retry(self, sid: str) -> None:
        """Explicitly release a blocked/retryable node for another controlled run."""
        if sid not in self.data.get("steps", {}):
            raise ValueError(f"unknown step: {sid}")
        current = self.step(sid).get("status")
        if current not in {FAILED_RETRYABLE, STALE, "blocked_with_recommendations", "rejected"}:
            raise ValueError(f"step {sid} is {current} and cannot be retried")
        self.set_status(sid, FAILED_RETRYABLE, reason="retry requested")

    # ---- 成本预算：state.json 是预算 SSOT ----
    def cost(self) -> dict:
        cost = self.data.setdefault("cost", {})
        cost.setdefault("currency", "USD")
        cost.setdefault("hard_limit", None)
        cost.setdefault("estimated", 0.0)
        cost.setdefault("spent", 0.0)
        cost.setdefault("confirmed", False)
        cost.setdefault("paused", False)
        cost.setdefault("ledger", [])
        return cost

    def configure_budget(
        self,
        *,
        hard_limit: float | None,
        currency: str = "USD",
        resume: bool = False,
    ) -> dict:
        cost = self.cost()
        if hard_limit is not None and (
            not math.isfinite(float(hard_limit)) or float(hard_limit) < 0
        ):
            raise ValueError("hard_limit must be a finite non-negative number")
        cost["hard_limit"] = None if hard_limit is None else float(hard_limit)
        cost["currency"] = currency
        if resume:
            cost["paused"] = False
            cost.pop("block", None)
        self.save()
        self.append_event(
            "budget_configured", hard_limit=cost["hard_limit"],
            currency=currency, resumed=resume,
        )
        return dict(cost)

    def can_reserve_cost(self, estimated_cost: float | None) -> bool:
        cost = self.cost()
        if cost.get("paused"):
            return False
        limit = cost.get("hard_limit")
        if limit is None or estimated_cost is None:
            return True
        return float(cost.get("spent") or 0.0) + float(cost.get("estimated") or 0.0) \
            + float(estimated_cost) <= float(limit)

    def upsert_cost_entry(
        self,
        idempotency_key: str,
        *,
        estimated_cost: float | None = None,
        actual_cost: float | None | object = _UNSET,
        status: str,
        job_id: str,
    ) -> dict:
        """按幂等键更新账本；同一任务的实际成本只能结算一次。"""
        if estimated_cost is not None and (
            not math.isfinite(float(estimated_cost)) or float(estimated_cost) < 0
        ):
            raise ValueError("estimated_cost must be a finite non-negative number")
        if actual_cost is not _UNSET and actual_cost is not None and (
            not math.isfinite(float(actual_cost)) or float(actual_cost) < 0
        ):
            raise ValueError("actual_cost must be a finite non-negative number")
        cost = self.cost()
        ledger = cost["ledger"]
        entry = next(
            (item for item in ledger if item.get("idempotency_key") == idempotency_key),
            None,
        )
        if entry is None:
            entry = {
                "idempotency_key": idempotency_key,
                "job_id": job_id,
                "estimated_cost": estimated_cost,
                "actual_cost": None,
                "status": status,
            }
            ledger.append(entry)
        else:
            if entry.get("estimated_cost") is None and estimated_cost is not None:
                entry["estimated_cost"] = estimated_cost
            entry["status"] = status

        if actual_cost is not _UNSET:
            normalized = None if actual_cost is None else float(actual_cost)
            previous = entry.get("actual_cost")
            if previous is not None and normalized != previous:
                raise ValueError(f"actual cost already settled for {idempotency_key}")
            entry["actual_cost"] = normalized

        cost["spent"] = round(sum(
            float(item["actual_cost"])
            for item in ledger if item.get("actual_cost") is not None
        ), 6)
        cost["estimated"] = round(sum(
            float(item["estimated_cost"])
            for item in ledger
            if item.get("actual_cost") is None
            and item.get("estimated_cost") is not None
            and item.get("status") not in {"failed", "blocked_budget"}
        ), 6)

        limit = cost.get("hard_limit")
        if limit is not None and float(cost["spent"]) >= float(limit):
            cost["paused"] = True
        self.save()
        self.append_event(
            "cost_ledger_updated", job_id=job_id, status=status,
            spent=cost["spent"], estimated=cost["estimated"],
        )
        return dict(entry)

    def pause_for_budget(self, block: dict[str, Any]) -> None:
        cost = self.cost()
        cost["paused"] = True
        cost["block"] = block
        self.save()
        self.append_event("budget_paused", block=block)

    def input_hashes(self, dependencies: list[str]) -> dict[str, str]:
        return {dep: str(self.step(dep).get("hash") or "") for dep in dependencies}

    def invalidate_downstream(
        self,
        sid: str,
        order: list[str],
        *,
        dependencies: dict[str, list[str]] | None = None,
        units: list[str] | None = None,
    ) -> list[str]:
        """按依赖图级联 stale；旧调用未传依赖图时保持线性顺序语义。"""
        affected = set(order[order.index(sid) + 1:])
        if dependencies is not None:
            affected = set()
            frontier = [sid]
            while frontier:
                upstream = frontier.pop()
                for candidate, deps in dependencies.items():
                    if upstream in deps and candidate not in affected:
                        affected.add(candidate)
                        frontier.append(candidate)

        touched = []
        for later in order:
            if later not in affected:
                continue
            step = self.step(later)
            if units:
                step["stale_units"] = sorted(set(step.get("stale_units", [])) | set(units))
            if step.get("status") != PENDING:
                step.update(status=STALE, updated_at=_now(), reason=f"upstream {sid} changed")
                touched.append(later)
        if touched or units:
            self.save()
            self.append_event(
                "downstream_invalidated", source_step=sid,
                steps=touched, units=units or [],
            )
        return touched

    def invalidate_change(
        self,
        change: str,
        order: list[str],
        *,
        dependencies: dict[str, list[str]] | None = None,
        units: list[str] | None = None,
    ) -> list[str]:
        """应用显式变更边界，供表单/对话层表达局部修改。"""
        # dependencies is accepted to keep the public invalidation API parallel with
        # invalidate_downstream; the named table is deliberately the authoritative boundary.
        _ = dependencies
        targets = INVALIDATION_RULES.get(change)
        if not targets:
            raise ValueError(f"unknown change type: {change}")
        touched: list[str] = []
        for sid in targets:
            if sid not in self.data.get("steps", {}):
                continue
            step = self.step(sid)
            if units:
                step["stale_units"] = sorted(set(step.get("stale_units", [])) | set(units))
            if step.get("status") != PENDING:
                step.update(status=STALE, updated_at=_now(), reason=f"{change} changed")
                touched.append(sid)
        self.save()
        self.append_event("change_invalidated", change=change, steps=touched, units=units or [])
        return touched

    def reconcile(
        self,
        order: list[str],
        dependencies: dict[str, list[str]],
        current_hashes: dict[str, str],
    ) -> list[str]:
        """恢复中断任务，并依据产物/输入哈希把过期节点标为 stale。"""
        touched: list[str] = []
        stale_sources: list[str] = []

        for sid in order:
            step = self.step(sid)
            status = step.get("status")
            if status == RUNNING:
                step.update(
                    status=FAILED_RETRYABLE,
                    updated_at=_now(),
                    reason="previous process exited while this step was running",
                )
                touched.append(sid)
                continue

            if status not in (DONE, AWAITING):
                continue
            stored_output = str(step.get("hash") or "")
            current_output = str(current_hashes.get(sid) or "")
            recorded_inputs = step.get("input_hashes")
            inputs_now = self.input_hashes(dependencies.get(sid, []))
            output_changed = bool(stored_output) and current_output != stored_output
            inputs_changed = isinstance(recorded_inputs, dict) and recorded_inputs != inputs_now
            if output_changed or inputs_changed:
                reason = "output hash changed" if output_changed else "input hashes changed"
                step.update(status=STALE, updated_at=_now(), reason=reason)
                touched.append(sid)
                stale_sources.append(sid)

        for source in stale_sources:
            for sid in self._dependent_steps(source, order, dependencies):
                step = self.step(sid)
                if step.get("status") != PENDING and step.get("status") != STALE:
                    step.update(
                        status=STALE, updated_at=_now(),
                        reason=f"upstream {source} changed",
                    )
                    touched.append(sid)

        if touched:
            touched = list(dict.fromkeys(touched))
            self.save()
            self.append_event("state_reconciled", steps=touched)
        return touched

    @staticmethod
    def _dependent_steps(
        source: str,
        order: list[str],
        dependencies: dict[str, list[str]],
    ) -> list[str]:
        affected: set[str] = set()
        frontier = [source]
        while frontier:
            upstream = frontier.pop()
            for sid, deps in dependencies.items():
                if upstream in deps and sid not in affected:
                    affected.add(sid)
                    frontier.append(sid)
        return [sid for sid in order if sid in affected]
