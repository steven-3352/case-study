"""工具层(M1 stub):只写占位产物,不接真模型、不花钱。

每个工具签名统一:run(inputs, out_dir, params, prompt_file=None) -> ToolResult。
M2+ 逐个替换成真实现(复用 src/mvstudio、pipeline/mv_engine 的确定性能力)。
"""
from __future__ import annotations

from pathlib import Path

from .contracts import ToolResult


def _write(out_dir: Path, name: str, body: str) -> str:
    p = Path(out_dir) / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")
    return str(p.relative_to(Path(out_dir).parents[1]))


def _stub(kind: str):
    """生成一个占位工具:落每步该有的产物文件,内容标 [STUB]。"""

    def run(inputs, out_dir, params, prompt_file=None):
        out_dir = Path(out_dir)
        outputs = []
        for name in params.get("outputs", []):
            note = f"[STUB · {kind}] 占位产物 · 待 M2+ 接真实现\n"
            if prompt_file:
                note += f"用到的提示词: {prompt_file}\n"
            outputs.append(_write(out_dir, name, note))
        return ToolResult(ok=True, outputs=outputs, meta={"stub": True, "cost": 0.0})

    return run


# 六步各自的 stub 工具(签名一致,行为占位)
intake_validate = _stub("intake_validate")
llm_analyze = _stub("llm_analyze")
llm_storyboard = _stub("llm_storyboard")
gen_keyframe = _stub("gen_keyframe")
gen_video = _stub("gen_video")
compose = _stub("compose")
