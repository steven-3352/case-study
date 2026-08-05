"""CLI 驱动（mv-agent 版）。

用法：
  python -m conductor.cli init   <片名> <项目根>   项目根 = 用户物料所在目录（必填）
  python -m conductor.cli status <片名>
  python -m conductor.cli next   <片名>       跑下一个可执行步骤
  python -m conductor.cli run    <片名>       一路跑到需要拍板处
  python -m conductor.cli ok     <片名> <step>
  python -m conductor.cli reject <片名> <step> [意见]

对话外壳（Codex / 本地 Web）最终就是把这些动作翻译成"下一步/过/打回"。

项目根约定（owner 2026-08-05 · docs/RULES/08_ASSETS_LIFECYCLE.md §3.0.1）：
  新项目的项目根 = 用户原始物料所在目录，骨架/产物落在那里，不进工具仓库。
  init 必须显式给项目根，缺参数直接报错，绝不落回 mv-agent/projects/。
  init 时把「片名 → 项目根」记入 _registry.json，之后按片名操作即可。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# 允许 `python conductor/cli.py` 直接跑（无需 `python -m`）
_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))   # mv-agent/
sys.path.insert(0, str(_HERE.parent.parent))  # 项目根，让 mv_platform 可 import

from conductor.conductor import Conductor  # noqa: E402
from conductor.contracts import AWAITING, DONE  # noqa: E402
from conductor.pipeline import STEP_BY_ID, STEP_ORDER  # noqa: E402
from conductor import render  # noqa: E402

# 注册表：片名 → 项目根（物料目录）。工具指针元数据，非用户数据。
_REGISTRY = _HERE.parent / "projects" / "_registry.json"


def _load_registry() -> dict:
    if _REGISTRY.is_file():
        try:
            return json.loads(_REGISTRY.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _save_registry(reg: dict) -> None:
    _REGISTRY.parent.mkdir(parents=True, exist_ok=True)
    _REGISTRY.write_text(
        json.dumps(reg, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _root_of(name: str) -> Path:
    """按片名查项目根；查不到直接报错（新约定下无仓库回退）。"""
    reg = _load_registry()
    entry = reg.get(name)
    if not entry:
        raise SystemExit(
            f"❌ 未登记的项目「{name}」。\n"
            f"   新项目请先：init {name} <项目根>（项目根 = 你的物料目录）。\n"
            f"   已建项目请确认片名拼写，或查 {_REGISTRY}。"
        )
    return Path(entry)


def _c(name: str) -> Conductor:
    return Conductor(None, name, root=_root_of(name))


def cmd_init(name: str, *rest):
    if not rest or not str(rest[0]).strip():
        raise SystemExit(
            f"❌ 新项目必须指定项目根：init {name} <项目根>\n"
            f"   项目根 = 你的原始物料所在目录（音乐/歌词/人物图）。\n"
            f"   骨架和产物会建在那里，不会进工具仓库。\n"
            f"   见 docs/RULES/08_ASSETS_LIFECYCLE.md §3.0.1。"
        )
    root = Path(str(rest[0]).strip()).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    c = Conductor(None, name, root=root)
    c.init_project()
    reg = _load_registry()
    reg[name] = str(root)
    _save_registry(reg)
    print(f"✅ 初始化 {name}：骨架 + prompts + state.json 已建于 {root}")
    print(f"   已登记片名 → 项目根（{_REGISTRY.name}）")
    cmd_status(name)


def cmd_status(name: str, *_):
    c = _c(name)
    c.state.load()
    print(f"\n📁 {name}  (tier={c.state.data.get('production_tier')})")
    for sid in STEP_ORDER:
        st = c.state.step(sid)
        mark = {
            "done":               "✅",
            "awaiting_approval":  "⏸️ ",
            "rejected":           "↩️ ",
            "running":            "⏳",
            "pending":            "  ",
        }.get(st.get("status"), "  ")
        rev = f" rev{st['revision']}" if st.get("revision") else ""
        print(f"  {mark} {sid:14s} {STEP_BY_ID[sid].title}{rev}  [{st.get('status')}]")
    cost = c.state.data.get("cost", {})
    print(f"  💰 预估 {cost.get('estimated')} · 已花 {cost.get('spent')} "
          f"· 计费确认={cost.get('confirmed')}")


def _run_one(c: Conductor, name: str, spec) -> dict:
    """跑一步并按统一格式渲染跑前/跑后提示。"""
    print(render.before(spec))
    res = c.run_step(spec)
    if res.get("skipped"):
        print(render.skipped(spec))
    elif res.get("ok"):
        print(render.after(spec, res.get("outputs") or spec.outputs, project=name))
    else:
        print(f"❌ 失败：{res.get('error')}")
    return res


def cmd_next(name: str, *_):
    c = _c(name)
    spec = c.next_step()
    if not spec:
        print("🎉 没有可执行步骤（全 done 或在等拍板）")
        return
    res = _run_one(c, name, spec)
    if res.get("status") == AWAITING:
        print(f"   ⏸️  等你拍板：ok {name} {spec.step_id}  /  reject {name} {spec.step_id} '意见'")


def cmd_run(name: str, *_):
    """一路跑到第一个需要拍板处 / 失败处停下。"""
    c = _c(name)
    while True:
        spec = c.next_step()
        if not spec:
            print("🎉 到头了（全 done 或等拍板）")
            break
        res = _run_one(c, name, spec)
        if not res.get("ok") and not res.get("skipped"):
            # 工具失败：已置 rejected，若不停会被 next_step 反复重选 → 死循环
            print(f"   ⛔ 步骤 {spec.step_id} 失败，已停下。修好上面提示的问题后重跑：run {name}")
            break
        if res.get("status") == AWAITING:
            print(f"   ⏸️  等拍板：ok {name} {spec.step_id} / reject {name} {spec.step_id} '意见'")
            break
    cmd_status(name)


def cmd_ok(name: str, step: str, *_):
    print(f"✅ {_c(name).approve(step)}")
    cmd_status(name)


def cmd_reject(name: str, step: str, *fb: str):
    print(f"↩️  {_c(name).reject(step, ' '.join(fb))}")
    cmd_status(name)


_CMDS = {
    "init":   cmd_init,
    "status": cmd_status,
    "next":   cmd_next,
    "run":    cmd_run,
    "ok":     cmd_ok,
    "reject": cmd_reject,
}


def main(argv: list[str]):
    if len(argv) < 3 or argv[1] not in _CMDS:
        print(__doc__)
        return
    cmd, name = argv[1], argv[2]
    _CMDS[cmd](name, *argv[3:])


if __name__ == "__main__":
    main(sys.argv)
