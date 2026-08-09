"""控制器：读 state 选下一步 → 备齐输入 → 调工具 → 写产物 → 更新 state。

不含任何业务判断、不写提示词、不碰模型。纯搬运 + 编排。
"""
from __future__ import annotations

import os
from pathlib import Path

from . import layout
from .contracts import AWAITING, DONE, PENDING, REJECTED, RUNNING, StepSpec
from .pipeline import STEP_BY_ID, STEP_ORDER, STEPS
from .state import State, sha256_file


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

    # ---- 选下一个可执行步骤 ----
    def next_step(self) -> StepSpec | None:
        self.state.load()
        for sid in STEP_ORDER:
            st = self.state.step(sid).get("status")
            if st in (PENDING, REJECTED):
                spec = STEP_BY_ID[sid]
                if all(self.state.is_done(u) for u in spec.input_from):
                    return spec
        return None

    # ---- 跑一步（幂等）----
    def run_step(self, spec: StepSpec, only: list[str] | None = None) -> dict:
        """跑一步。only 给镜号列表时只处理那几镜（单镜/子集生成），
        并跳过幂等短路——单镜生成总是要真跑工具，不能被"已 done"挡住。"""
        self.state.load()
        # 幂等跳过：产物齐 + 状态已 done + hash 未变（only 模式不短路）
        if not only and self._outputs_ready(spec) \
                and self.state.step(spec.step_id).get("status") == DONE:
            return {"skipped": True, "step": spec.step_id}

        self.state.set_status(spec.step_id, RUNNING)
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
            self.state.set_status(spec.step_id, REJECTED, error=res.error)
            return {"ok": False, "step": spec.step_id, "error": res.error, "meta": res.meta}

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
        self.state.set_status(spec.step_id, nxt, hash=h)
        return {"ok": True, "step": spec.step_id, "status": nxt, "hash": h,
                "outputs": list(res.outputs), "meta": res.meta}

    # ---- 用户拍板：过 ----
    def approve(self, sid: str) -> dict:
        self.state.load()
        self.state.set_status(sid, DONE)
        return {"approved": sid}

    # ---- 用户拍板：打回（带意见） ----
    def reject(self, sid: str, feedback: str = "", units: list[str] | None = None) -> dict:
        self.state.load()
        step = self.state.step(sid)
        step["revision"] = step.get("revision", 1) + 1
        sub = layout.ensure_step_dirs(self.root, sid)
        (sub["meta"] / "feedback.md").write_text(
            feedback or "(无具体意见)", encoding="utf-8"
        )
        self.state.set_status(sid, REJECTED, feedback=feedback, rerun_units=units or ["*"])
        touched = self.state.invalidate_downstream(sid, STEP_ORDER)
        return {"rejected": sid, "revision": step["revision"], "downstream_reset": touched}
