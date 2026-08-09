"""契约层：步骤契约 + 工具契约 + 重跑单元。

控制器只认这些声明式结构，不写死业务逻辑。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional


# 步骤状态机：pending → running → awaiting_approval → done / rejected
# 进程中断后的 running 会恢复为 failed_retryable；输入/产物变化会变为 stale。
PENDING  = "pending"
RUNNING  = "running"
AWAITING = "awaiting_approval"
DONE     = "done"
REJECTED = "rejected"
STALE = "stale"
FAILED_RETRYABLE = "failed_retryable"
BLOCKED = "blocked_with_recommendations"


@dataclass
class ToolResult:
    """工具统一返回。失败时结构化返回，不抛异常让控制器猜。"""
    ok: bool
    outputs: List[str] = field(default_factory=list)
    error: Optional[dict] = None           # {code, message, hint}
    meta: dict = field(default_factory=dict)  # {model, tokens, cost, elapsed}


@dataclass
class Unit:
    """重跑单元（第 2 档粒度）：用户能单独重跑的最小单位。

    kind='step'  整步一个单元（如分析/合成）
    kind='shot'  逐镜（如逐镜关键帧/逐镜视频）
    kind='group' 逐组（如逐背景组）
    kind='char'  逐角色（如逐角色锚点）
    """
    uid: str
    kind: str
    prompt: Optional[str] = None   # 用哪个提示词文件（None=确定性，不花钱）
    costly: bool = False            # 是否花钱（决定要不要付费锁）


@dataclass
class StepSpec:
    """每步契约（声明式）。控制器读它就够。"""
    step_id: str
    title: str
    input_from: List[str]           # 依赖哪些上游步骤文件夹
    prompts: List[str]               # 需要哪些提示词文件
    tool: Callable                   # 该步的执行工具
    outputs: List[str]               # 产物清单（供完成判定）
    approval: bool = True            # 是否需要用户拍板
    unit_kind: str = "step"         # 重跑单元粒度：step/shot/group/char
    # ---- 执行透明化：跑前/跑后念给用户听 ----
    tool_name: str = ""              # 执行脚本名（如 llm_analyze）
    purpose: str = ""                # 本步用途（一句话）
    outputs_desc: dict = field(default_factory=dict)  # {产物文件: 用途说明}
