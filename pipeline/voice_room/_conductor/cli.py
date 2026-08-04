"""CLI 驱动:看流程用。

  python -m _conductor.cli init   <片名>
  python -m _conductor.cli status <片名>
  python -m _conductor.cli next   <片名>     跑下一个可执行步骤
  python -m _conductor.cli run    <片名>     一路跑到需要拍板处
  python -m _conductor.cli ok     <片名> <step>
  python -m _conductor.cli reject <片名> <step> [意见]

对话外壳(skill / 本地 Web)最终就是把这些动作翻译成"下一步 / 过 / 打回"。
"""
from __future__ import annotations

import sys
from pathlib import Path

# 允许 `python pipeline/voice_room/_conductor/cli.py` 直接跑
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from _conductor.conductor import Conductor  # noqa: E402
from _conductor.contracts import AWAITING, DONE  # noqa: E402
from _conductor.pipeline import STEP_BY_ID, STEP_ORDER  # noqa: E402

BASE = Path(__file__).resolve().parents[1]  # pipeline/voice_room/


def _c(name: str) -> Conductor:
    return Conductor(BASE, name)


def cmd_init(name: str):
    c = _c(name)
    c.init_project()
    print(f"✅ 初始化 {name}:骨架 + prompts + state.json 已建")
    cmd_status(name)


def cmd_status(name: str):
    c = _c(name)
    c.state.load()
    print(f"\n📁 {name}  (tier={c.state.data.get('production_tier')})")
    for sid in STEP_ORDER:
        st = c.state.step(sid)
        mark = {"done": "✅", "awaiting_approval": "⏸️ ", "rejected": "↩️ ",
                "running": "⏳", "pending": "  "}.get(st.get("status"), "  ")
        rev = f" rev{st['revision']}" if st.get("revision") else ""
        print(f"  {mark} {sid:14s} {STEP_BY_ID[sid].title}{rev}  [{st.get('status')}]")
    cost = c.state.data.get("cost", {})
    print(f"  💰 预估 {cost.get('estimated')} · 已花 {cost.get('spent')} "
          f"· 计费确认={cost.get('confirmed')}")


def cmd_next(name: str):
    c = _c(name)
    spec = c.next_step()
    if not spec:
        print("🎉 没有可执行步骤(全 done 或在等拍板)")
        return
    res = c.run_step(spec)
    print(f"▶️  跑了 {spec.step_id}:{res}")
    if res.get("status") == AWAITING:
        print(f"   ⏸️  等你拍板:ok {name} {spec.step_id}  /  reject {name} {spec.step_id} '意见'")


def cmd_run(name: str):
    """一路跑到第一个需要拍板处停下。"""
    c = _c(name)
    while True:
        spec = c.next_step()
        if not spec:
            print("🎉 到头了(全 done 或等拍板)")
            break
        res = c.run_step(spec)
        print(f"▶️  {spec.step_id}: {res.get('status', res)}")
        if res.get("status") == AWAITING:
            print(f"   ⏸️  等拍板:ok {name} {spec.step_id} / reject {name} {spec.step_id} '意见'")
            break
    cmd_status(name)


def cmd_ok(name: str, step: str):
    print(f"✅ {_c(name).approve(step)}")
    cmd_status(name)


def cmd_reject(name: str, step: str, *fb: str):
    print(f"↩️  {_c(name).reject(step, ' '.join(fb))}")
    cmd_status(name)


def main(argv: list[str]):
    if len(argv) < 3:
        print(__doc__)
        return
    cmd, name = argv[1], argv[2]
    rest = argv[3:]
    fn = {"init": cmd_init, "status": cmd_status, "next": cmd_next, "run": cmd_run,
          "ok": cmd_ok, "reject": cmd_reject}.get(cmd)
    if not fn:
        print(__doc__)
        return
    fn(name, *rest)


if __name__ == "__main__":
    main(sys.argv)
