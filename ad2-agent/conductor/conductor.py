"""控制器：读 state 选下一步 → 备齐输入 → 调工具 → 写产物 → 更新 state。

不含任何业务判断、不写提示词、不碰模型。纯搬运 + 编排。
"""
from __future__ import annotations

import fcntl
import os
from functools import wraps
from pathlib import Path

from . import layout
from .contracts import (
    AWAITING,
    BLOCKED,
    DONE,
    FAILED_RETRYABLE,
    PENDING,
    REJECTED,
    RUNNING,
    STALE,
    StepSpec,
)
from .pipeline import STEP_BY_ID, STEP_ORDER, STEPS
from .state import State, sha256_file
from .recommendations import build_recommendation, validate_recommendation, write_recommendation


class ProjectBusyError(RuntimeError):
    pass


def _single_writer(method):
    """Fail fast when another process is mutating the same project."""
    @wraps(method)
    def guarded(self, *args, **kwargs):
        lock_path = self.root / ".adfilm.lock"
        self.root.mkdir(parents=True, exist_ok=True)
        with lock_path.open("a+", encoding="utf-8") as lock:
            try:
                fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise ProjectBusyError(
                    "project is being written by another session; retry after it finishes"
                ) from exc
            try:
                return method(self, *args, **kwargs)
            finally:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
    return guarded


class Conductor:
    def __init__(self, base: Path, name: str, root: Path | None = None):
        # root 显式给出时(新项目 = 用户物料目录)直接用;否则退回 base/name。
        # 见 docs/RULES/08_ASSETS_LIFECYCLE.md §3.0.1(物料锚定)。
        self.name = name
        self.root = Path(root) if root is not None else layout.project_root(base, name)
        self.prompts_dir = self.root / "prompts"
        self.state = State(self.root)

    # ---- 初始化项目骨架 ----
    def init_project(self, tier: str = "standard") -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.prompts_dir.mkdir(exist_ok=True)
        for spec in STEPS:
            layout.ensure_step_dirs(self.root, spec.step_id)
            for name in spec.prompts:
                pf = self.prompts_dir / name
                if not pf.exists():
                    # 从 mv-agent/prompts/ 复制模板（如有），否则建空占位
                    template = Path(__file__).parent.parent / "prompts" / name
                    if template.is_file():
                        import shutil
                        shutil.copy2(template, pf)
                    else:
                        pf.write_text(
                            f"# {name}\n(提示词占位 · 在此写中文)\n",
                            encoding="utf-8",
                        )
        self.state.init(self.name, STEP_ORDER, tier)

    # ---- 完成判定：产物齐即算可完成 ----
    def _outputs_ready(self, spec: StepSpec) -> bool:
        step_dir = self.root / spec.step_id
        return all((step_dir / o).exists() for o in spec.outputs)

    def _hash_outputs(self, spec: StepSpec) -> str:
        step_dir = self.root / spec.step_id
        parts = []
        for o in sorted(spec.outputs):
            p = step_dir / o
            if p.exists():
                parts.append(sha256_file(p))
        return "sha256:" + "+".join(x.split(":")[1] for x in parts)[:16] if parts else ""

    def reconcile(self) -> list[str]:
        """重算磁盘产物与依赖；CLI 重进时在选步/拍板前调用。"""
        self.state.load()
        dependencies = {spec.step_id: list(spec.input_from) for spec in STEPS}
        current_hashes = {
            spec.step_id: self._hash_outputs(spec) if self._outputs_ready(spec) else ""
            for spec in STEPS
        }
        return self.state.reconcile(STEP_ORDER, dependencies, current_hashes)

    # ---- 选下一个可执行步骤 ----
    def next_step(self) -> StepSpec | None:
        self.reconcile()
        for sid in STEP_ORDER:
            st = self.state.step(sid).get("status")
            if st in (PENDING, REJECTED, STALE, FAILED_RETRYABLE):
                spec = STEP_BY_ID[sid]
                if all(self.state.is_done(u) for u in spec.input_from):
                    return spec
        return None

    # ---- 跑一步（幂等）----
    @_single_writer
    def run_step(self, spec: StepSpec, only: list[str] | None = None) -> dict:
        """跑一步。only 给镜号列表时只处理那几镜（单镜/子集生成），
        并跳过幂等短路——单镜生成总是要真跑工具，不能被"已 done"挡住。"""
        self.state.load()
        # 幂等跳过：产物齐 + 状态已 done + hash 未变（only 模式不短路）
        if not only and self._outputs_ready(spec) \
                and self.state.step(spec.step_id).get("status") == DONE:
            return {"skipped": True, "step": spec.step_id}

        inputs = self.state.input_hashes(spec.input_from)
        self.state.set_status(spec.step_id, RUNNING, input_hashes=inputs)
        sub = layout.ensure_step_dirs(self.root, spec.step_id)
        layout.stage_inputs(self.root, spec.step_id, spec.input_from)
        layout.copy_prompt_used(self.root, spec.step_id, self.prompts_dir, spec.prompts)

        prompt_file = (self.prompts_dir / spec.prompts[0]) if spec.prompts else None
        params = {"outputs": spec.outputs, "step_id": spec.step_id}
        if only:
            params["only"] = list(only)
        res = spec.tool(
            inputs=[sub["input"]],
            out_dir=sub["step"],
            params=params,
            prompt_file=prompt_file,
        )
        scope = f"（仅 {', '.join(only)}）" if only else ""
        layout.append_log(
            self.root, spec.step_id,
            f"脚本 {spec.tool_name or spec.tool.__name__} · 用途：{spec.purpose}{scope} "
            f"· ok={res.ok} · 产出 {len(res.outputs)} 个：{', '.join(res.outputs)}",
        )

        if not res.ok:
            package = (res.meta or {}).get("recommendations")
            try:
                package = validate_recommendation(package)
            except (TypeError, ValueError):
                error = res.error or {}
                package = build_recommendation(
                    node=spec.step_id,
                    reason_code=str(error.get("code") or "TOOL_BLOCKED").upper(),
                    plain_reason=str(error.get("message") or "当前节点无法继续。"),
                    options=[
                        {
                            "id": "O1", "action": str(error.get("hint") or "修复输入或服务配置后重试"),
                            "expected_visual_quality": "high", "product_fidelity": "high",
                            "cost_delta": "unknown", "time_delta": "medium",
                            "invalidates": [spec.step_id],
                        },
                        {
                            "id": "O2", "action": "保留已有产物，修改该节点方案或终止本次制作",
                            "expected_visual_quality": "variable", "product_fidelity": "variable",
                            "cost_delta": "low", "time_delta": "low",
                            "invalidates": [spec.step_id],
                        },
                    ],
                    recommended_option="O1",
                    recommendation_reason="优先修复当前阻塞可保留已确认的上游结果。",
                    resume_from=spec.step_id,
                )
            recommendation_path = write_recommendation(
                sub["meta"] / "recommendations.yaml", package
            )
            self.state.set_status(
                spec.step_id, BLOCKED, error=res.error,
                recommendations=str(recommendation_path),
            )
            return {"ok": False, "step": spec.step_id, "status": BLOCKED,
                    "error": res.error, "recommendations": package, "meta": res.meta}

        h = self._hash_outputs(spec)
        if (spec.approval and spec.step_id == "03_keyframes"
                and os.environ.get("MVSTUDIO_STORYBOARD_AUTO_APPROVE") == "1"):
            nxt = DONE
            layout.append_log(
                self.root, spec.step_id,
                "MVSTUDIO_STORYBOARD_AUTO_APPROVE=1 → 跳过分镜拍板",
            )
        else:
            nxt = AWAITING if spec.approval else DONE
        self.state.set_status(
            spec.step_id, nxt, hash=h, input_hashes=inputs,
            stale_units=[], error=None,
        )
        return {"ok": True, "step": spec.step_id, "status": nxt, "hash": h,
                "outputs": list(res.outputs), "meta": res.meta}

    # ---- 用户拍板：过 ----
    @_single_writer
    def approve(self, sid: str) -> dict:
        self.reconcile()
        if sid not in STEP_BY_ID:
            raise ValueError(f"unknown step: {sid}")
        status = self.state.step(sid).get("status")
        if status == DONE:
            return {"approved": sid, "already_done": True}
        if status != AWAITING:
            raise ValueError(f"step {sid} is {status}, expected {AWAITING}")
        self.state.set_status(sid, DONE)
        return {"approved": sid}

    # ---- 用户拍板：打回（带意见） ----
    @_single_writer
    def reject(self, sid: str, feedback: str = "", units: list[str] | None = None) -> dict:
        self.state.load()
        if sid not in STEP_BY_ID:
            raise ValueError(f"unknown step: {sid}")
        status = self.state.step(sid).get("status")
        if status not in (AWAITING, DONE, REJECTED, FAILED_RETRYABLE, STALE):
            raise ValueError(f"step {sid} is {status} and cannot be rejected")
        step = self.state.step(sid)
        step["revision"] = step.get("revision", 1) + 1
        sub = layout.ensure_step_dirs(self.root, sid)
        (sub["meta"] / "feedback.md").write_text(
            feedback or "(无具体意见)", encoding="utf-8"
        )
        self.state.set_status(
            sid, REJECTED, feedback=feedback, rerun_units=units or ["*"],
            stale_units=units or [],
        )
        dependencies = {spec.step_id: list(spec.input_from) for spec in STEPS}
        touched = self.state.invalidate_downstream(
            sid, STEP_ORDER, dependencies=dependencies, units=units,
        )
        return {"rejected": sid, "revision": step["revision"], "downstream_reset": touched}

    @_single_writer
    def retry(self, sid: str) -> dict:
        self.state.load()
        self.state.retry(sid)
        return {"retry": sid, "status": FAILED_RETRYABLE}
