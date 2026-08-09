"""付费远程任务的幂等记录、预算授权与成本结算。"""
from __future__ import annotations

import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from mvstudio.media import sha256_bytes

from .state import State


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def idempotency_key(
    *,
    project: str,
    node: str,
    shot_id: str,
    provider_id: str,
    request: dict[str, Any] | None = None,
) -> str:
    """由稳定业务输入生成；请求内容只参与哈希，不写入 jobs，避免泄密。"""
    canonical = json.dumps(
        {
            "project": project,
            "node": node,
            "shot_id": shot_id,
            "provider_id": provider_id,
            "request": request or {},
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return "idem-" + sha256_bytes(canonical.encode("utf-8")).removeprefix("sha256:")[:32]


def budget_recommendations() -> list[dict[str, str]]:
    return [
        {
            "id": "raise_limit_and_resume",
            "title": "保留继续",
            "action": "提高 hard_limit 后从暂停镜继续，复用现有幂等键。",
            "expected_visual_quality": "high",
            "product_fidelity": "high",
            "cost_delta": "higher",
            "time_delta": "low",
            "invalidates": ["N11_PAUSED", "N13", "N14"],
        },
        {
            "id": "downgrade_remaining",
            "title": "保留降档",
            "action": "保留已产出镜，把剩余 i2v 镜改为 static 或 ken_burns。",
            "expected_visual_quality": "medium",
            "product_fidelity": "high",
            "cost_delta": "none",
            "time_delta": "medium",
            "invalidates": ["N11_REMAINING", "N13", "N14"],
        },
        {
            "id": "stop_and_keep",
            "title": "保留终止",
            "action": "停止后续提交，保留已下载产物和全部 jobs 记录。",
            "expected_visual_quality": "incomplete",
            "product_fidelity": "unchanged",
            "cost_delta": "none",
            "time_delta": "none",
            "invalidates": ["N13", "N14"],
        },
    ]


class JobStore:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.jobs_dir = self.root / ".adfilm" / "jobs"
        self.jobs_dir.mkdir(parents=True, exist_ok=True)
        self.state = State(self.root)

    def _load_state(self) -> State:
        return self.state.load()

    def _path(self, job_id: str) -> Path:
        return self.jobs_dir / f"{job_id}.yaml"

    @staticmethod
    def _read(path: Path) -> dict:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if not isinstance(data, dict):
            raise ValueError(f"invalid job record: {path}")
        return data

    def _write(self, job: dict) -> None:
        path = self._path(str(job["job_id"]))
        temp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
        temp.write_text(
            yaml.safe_dump(job, allow_unicode=True, sort_keys=False), encoding="utf-8"
        )
        temp.replace(path)

    def all(self) -> list[dict]:
        return [self._read(path) for path in sorted(self.jobs_dir.glob("job-*.yaml"))]

    def get(self, key_or_job_id: str) -> dict | None:
        direct = self._path(key_or_job_id)
        if direct.is_file():
            return self._read(direct)
        return next(
            (job for job in self.all() if job.get("idempotency_key") == key_or_job_id),
            None,
        )

    def prepare(
        self,
        *,
        node: str,
        shot_id: str,
        provider_id: str,
        request: dict[str, Any] | None = None,
        estimated_cost: float | None = None,
    ) -> dict:
        if estimated_cost is not None and (
            not math.isfinite(float(estimated_cost)) or float(estimated_cost) < 0
        ):
            raise ValueError("estimated_cost must be a finite non-negative number")
        state = self._load_state()
        key = idempotency_key(
            project=str(state.data.get("project") or self.root.name),
            node=node,
            shot_id=shot_id,
            provider_id=provider_id,
            request=request,
        )
        existing = self.get(key)
        if existing is not None:
            self._sync_cost_entry(state, existing)
            return {**existing, "reused": True}

        job_id = "job-" + key.removeprefix("idem-")[:16]
        status = "awaiting_confirmation" if estimated_cost is None else "queued"
        if estimated_cost is not None and not state.can_reserve_cost(float(estimated_cost)):
            status = "blocked_budget"
        job = {
            "job_id": job_id,
            "node": node,
            "shot_id": shot_id,
            "provider_id": provider_id,
            "idempotency_key": key,
            "status": status,
            "estimated_cost": None if estimated_cost is None else float(estimated_cost),
            "actual_cost": None,
            "submitted_at": None,
            "created_at": _now(),
            "confirmed_at": None,
            "reused": False,
        }
        self._write(job)
        if status == "queued":
            state.upsert_cost_entry(
                key, estimated_cost=job["estimated_cost"], status=status, job_id=job_id,
            )
        return job

    def historical_cost_range(
        self,
        *,
        provider_id: str | None = None,
        node: str | None = None,
    ) -> dict:
        jobs = self.all()
        values = [
            float(job["actual_cost"])
            for job in jobs
            if job.get("actual_cost") is not None
            and (provider_id is None or job.get("provider_id") == provider_id)
            and (node is None or job.get("node") == node)
        ]
        currency = self._load_state().cost().get("currency", "USD")
        return {
            "count": len(values),
            "min": min(values) if values else None,
            "max": max(values) if values else None,
            "currency": currency,
        }

    def authorize_submission(
        self,
        key_or_job_id: str,
        *,
        confirm: bool = False,
        confirmation_scope: str = "shot",
    ) -> dict:
        job = self.get(key_or_job_id)
        if job is None:
            raise KeyError(key_or_job_id)
        state = self._load_state()
        self._sync_cost_entry(state, job)
        state.load()
        cost = state.cost()

        if job.get("status") in {"running", "done"}:
            return {"ok": True, "submit": False, "duplicate": True, "job": job}
        if cost.get("paused"):
            return self._blocked_decision(state, job, "budget is paused")

        estimate = job.get("estimated_cost")
        batch_confirmation = cost.get("unknown_cost_confirmation") or {}
        batch_confirmed = (
            batch_confirmation.get("scope") == "batch"
            and batch_confirmation.get("provider_id") == job.get("provider_id")
            and batch_confirmation.get("node") == job.get("node")
        )
        if estimate is None and not (confirm or job.get("confirmed_at") or batch_confirmed):
            return {
                "ok": False,
                "submit": False,
                "exit_code": 2,
                "error": {
                    "code": "confirmation_required",
                    "message": "无法精确估算本次费用，提交前需要知情确认。",
                    "hint": "确认本镜，或按整批确认策略继续；触顶时仍会暂停。",
                },
                "historical_cost_range": self.historical_cost_range(
                    provider_id=job.get("provider_id"), node=job.get("node")
                ),
                "job": job,
            }

        if estimate is not None and job.get("status") == "queued":
            limit = cost.get("hard_limit")
            projected = float(cost.get("spent") or 0.0) + float(cost.get("estimated") or 0.0)
            if limit is not None and projected > float(limit):
                job["status"] = "blocked_budget"
                self._write(job)
                state.upsert_cost_entry(
                    str(job["idempotency_key"]), estimated_cost=float(estimate),
                    status="blocked_budget", job_id=str(job["job_id"]),
                )
                return self._blocked_decision(
                    state, job, "spent plus queued estimate exceeds hard_limit"
                )

        if estimate is not None and job.get("status") == "blocked_budget":
            if not state.can_reserve_cost(float(estimate)):
                return self._blocked_decision(state, job, "estimated cost exceeds hard_limit")
            job["status"] = "queued"
            state.upsert_cost_entry(
                str(job["idempotency_key"]), estimated_cost=float(estimate),
                status="queued", job_id=str(job["job_id"]),
            )

        if estimate is None and (confirm or batch_confirmed) and not job.get("confirmed_at"):
            job["confirmed_at"] = _now()
            job["status"] = "queued"
            cost["confirmed"] = True
            if confirm and confirmation_scope == "batch":
                cost["unknown_cost_confirmation"] = {
                    "scope": "batch",
                    "provider_id": job.get("provider_id"),
                    "node": job.get("node"),
                    "confirmed_at": job["confirmed_at"],
                }
            elif confirm and confirmation_scope != "shot":
                raise ValueError("confirmation_scope must be 'shot' or 'batch'")
            state.save()
            state.append_event("unknown_cost_confirmed", job_id=job["job_id"])
            state.upsert_cost_entry(
                str(job["idempotency_key"]), estimated_cost=None,
                status="queued", job_id=str(job["job_id"]),
            )

        self._write(job)
        return {"ok": True, "submit": True, "duplicate": False, "job": job}

    def mark_running(self, key_or_job_id: str) -> dict:
        job = self._require(key_or_job_id)
        if job.get("status") == "done":
            return job
        job["status"] = "running"
        job["submitted_at"] = job.get("submitted_at") or _now()
        self._write(job)
        self._load_state().upsert_cost_entry(
            str(job["idempotency_key"]), estimated_cost=job.get("estimated_cost"),
            status="running", job_id=str(job["job_id"]),
        )
        return job

    def complete(self, key_or_job_id: str, *, actual_cost: float | None) -> dict:
        if actual_cost is not None and (
            not math.isfinite(float(actual_cost)) or float(actual_cost) < 0
        ):
            raise ValueError("actual_cost must be a finite non-negative number")
        job = self._require(key_or_job_id)
        if job.get("status") == "done":
            if job.get("actual_cost") != actual_cost:
                raise ValueError(f"actual cost already settled for {job['job_id']}")
            state = self._load_state()
            self._sync_cost_entry(state, job)
            cost = state.load().cost()
            paused = bool(cost.get("paused"))
            if paused and not cost.get("block"):
                state.pause_for_budget(
                    self._blocked_payload(state, "actual cost reached hard_limit")
                )
            return {
                "job": job,
                "paused": paused,
                "recommendations": budget_recommendations() if paused else [],
            }

        job["status"] = "done"
        job["actual_cost"] = None if actual_cost is None else float(actual_cost)
        job["completed_at"] = _now()
        self._write(job)
        state = self._load_state()
        state.upsert_cost_entry(
            str(job["idempotency_key"]), estimated_cost=job.get("estimated_cost"),
            actual_cost=job["actual_cost"], status="done", job_id=str(job["job_id"]),
        )
        cost = state.cost()
        limit = cost.get("hard_limit")
        paused = limit is not None and float(cost.get("spent") or 0.0) >= float(limit)
        if paused:
            block = self._blocked_payload(state, "actual cost reached hard_limit")
            state.pause_for_budget(block)
        return {"job": job, "paused": paused, "recommendations": budget_recommendations() if paused else []}

    def fail(self, key_or_job_id: str, *, error: dict | None = None) -> dict:
        job = self._require(key_or_job_id)
        job["status"] = "failed"
        job["error"] = error or {}
        job["completed_at"] = _now()
        self._write(job)
        self._load_state().upsert_cost_entry(
            str(job["idempotency_key"]), estimated_cost=job.get("estimated_cost"),
            status="failed", job_id=str(job["job_id"]),
        )
        return job

    def cost_summary(self) -> dict:
        cost = self._load_state().cost()
        limit = cost.get("hard_limit")
        spent = float(cost.get("spent") or 0.0)
        return {
            "currency": cost.get("currency", "USD"),
            "spent": spent,
            "estimated": float(cost.get("estimated") or 0.0),
            "hard_limit": limit,
            "remaining": None if limit is None else round(float(limit) - spent, 6),
            "paused": bool(cost.get("paused")),
        }

    def _require(self, key_or_job_id: str) -> dict:
        job = self.get(key_or_job_id)
        if job is None:
            raise KeyError(key_or_job_id)
        return job

    @staticmethod
    def _sync_cost_entry(state: State, job: dict) -> None:
        """修复 job 文件与 state 账本之间发生中断留下的半写状态。"""
        status = str(job.get("status") or "")
        if status not in {"queued", "running", "done", "failed"}:
            return
        kwargs: dict[str, Any] = {
            "estimated_cost": job.get("estimated_cost"),
            "status": status,
            "job_id": str(job["job_id"]),
        }
        if status == "done":
            kwargs["actual_cost"] = job.get("actual_cost")
        state.upsert_cost_entry(str(job["idempotency_key"]), **kwargs)

    def _blocked_payload(self, state: State, reason: str) -> dict:
        cost = state.cost()
        return {
            "status": "blocked_with_recommendations",
            "reason": reason,
            "spent": cost.get("spent", 0.0),
            "estimated": cost.get("estimated", 0.0),
            "hard_limit": cost.get("hard_limit"),
            "currency": cost.get("currency", "USD"),
            "recommendations": budget_recommendations(),
        }

    def _blocked_decision(self, state: State, job: dict, reason: str) -> dict:
        block = self._blocked_payload(state, reason)
        if not state.cost().get("paused"):
            state.pause_for_budget(block)
        return {
            "ok": False,
            "submit": False,
            "exit_code": 2,
            "error": {
                "code": "budget_hard_limit",
                "message": "预算硬上限已命中，未提交新的远程任务。",
                "hint": "选择保留继续、保留降档或保留终止。",
            },
            **block,
            "job": job,
        }
