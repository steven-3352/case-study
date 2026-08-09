"""执行透明化渲染：统一格式的「跑前 / 跑后」提示。

CLI 直接调用；Codex 也照这个格式念给用户，保证两条通道口径一致。
只做纯文本拼装，不碰状态、不跑工具。
"""
from __future__ import annotations

from .contracts import StepSpec

_BAR = "━" * 43


def before(spec: StepSpec) -> str:
    """跑一步之前：当前执行哪个脚本、干什么用的。"""
    return (
        f"{_BAR}\n"
        f"▶ 步骤 {spec.step_id} · 脚本 {spec.tool_name or spec.tool.__name__}\n"
        f"  用途：{spec.purpose or spec.title}\n"
        f"{_BAR}"
    )


def after(spec: StepSpec, outputs: list[str], project: str = "<片名>") -> str:
    """跑完之后：产出了哪些文件、各自什么用途。

    若本步用到提示词，追加一段「怎么改、怎么重跑」的标注，
    让用户知道创意内容从哪个文件调、改完如何生效。
    """
    lines = [f"✅ 完成 · 产出 {len(outputs)} 个文件"]
    width = max((len(o) for o in outputs), default=0)
    for name in outputs:
        desc = spec.outputs_desc.get(name, "")
        lines.append(f"  {name:<{width}}  {desc}")

    if spec.prompts:
        lines.append(f"📝 想调这步的提示词？编辑 projects/{project}/prompts/ 下：")
        lines.append("   " + " · ".join(spec.prompts))
        lines.append(f'   改完重跑：reject {project} {spec.step_id} "调整提示词" → run {project}')

    return "\n".join(lines)


def skipped(spec: StepSpec) -> str:
    """幂等跳过时的提示。"""
    return f"⏭  步骤 {spec.step_id} · 脚本 {spec.tool_name} 已完成且未变，跳过"
