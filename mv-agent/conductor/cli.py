"""CLI 驱动（mv-agent 版）。

用法：
  python -m conductor.cli init   <片名> <项目根>   项目根 = 用户物料所在目录（必填）
  python -m conductor.cli status <片名>
  python -m conductor.cli next   <片名>       跑下一个可执行步骤
  python -m conductor.cli run    <片名>       一路跑到需要拍板处
  python -m conductor.cli shot   <片名> <step> <镜号...>   逐镜/子集生成（仅 03/04）
  python -m conductor.cli ok     <片名> <step>
  python -m conductor.cli reject <片名> <step> [意见]

对话外壳（Codex / 本地 Web）最终就是把这些动作翻译成"下一步/过/打回"。

逐镜生成（shot）：03_keyframes / 04_shots 支持只生成点名的镜头，结果增量合并进索引，
不影响其余镜。镜号写法：SH003 · 3 · 3-6 · SH003-SH006 · 逗号列表 · all(全部) · missing(还缺的)。
省钱按需逐张出图/出片，不必一次烧满整批。

项目根约定（owner 2026-08-05 · docs/RULES/08_ASSETS_LIFECYCLE.md §3.0.1）：
  新项目的项目根 = 用户原始物料所在目录，骨架/产物落在那里，不进工具仓库。
  init 必须显式给项目根，缺参数直接报错，绝不落回 mv-agent/projects/。
  init 时把「片名 → 项目根」记入 _registry.json，之后按片名操作即可。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import yaml

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


# —— 逐镜生成（shot）：03/04 才支持子集生成 ——
# 每步「全集从哪读、已完成从哪读」的映射，用于展开 all/missing 等关键词。
_SHOT_STEPS = {
    "03_keyframes": {"all_file": ("02_storyboard", "shots.yaml",         "shots"),
                     "done_file": ("03_keyframes",  "keyframes_index.yaml", "keyframes"),
                     "noun": "首帧图"},
    "04_shots":     {"all_file": ("03_keyframes",  "keyframes_index.yaml", "shots"),
                     "done_file": ("04_shots",      "shots_index.yaml",     "shots"),
                     "noun": "视频片段"},
}


def _ids_from_yaml(path: Path, key: str) -> list[str]:
    """读某个索引/清单 yaml 里的镜号列表（文件不存在 → 空）。"""
    if not path.is_file():
        return []
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        return []
    items = data.get(key, []) if isinstance(data, dict) else []
    return [str(x["id"]) for x in items if isinstance(x, dict) and x.get("id")]


def _norm_id(tok: str) -> str:
    """把 '3' / 'sh3' / 'SH003' 统一成 'SH003'；非数字原样大写返回。"""
    tok = tok.strip().upper()
    m = re.fullmatch(r"(?:SH)?0*(\d+)", tok)
    return f"SH{int(m.group(1)):03d}" if m else tok


def _expand_targets(tokens: list[str], all_ids: list[str], done_ids: set[str]) -> list[str]:
    """把用户给的镜号 token 展开成有序去重的镜号列表。
    支持：SH003 · 3 · 3-6 / SH003-SH006（区间）· 逗号/中文逗号分隔 · all · missing/rest。"""
    order = {sid: i for i, sid in enumerate(all_ids)}
    picked: set[str] = set()
    for raw in tokens:
        for tok in re.split(r"[,，\s]+", raw.strip()):
            if not tok:
                continue
            low = tok.lower()
            if low in ("all", "全部", "整批"):
                picked.update(all_ids)
            elif low in ("missing", "rest", "remaining", "剩下", "还缺", "缺"):
                picked.update(sid for sid in all_ids if sid not in done_ids)
            elif "-" in tok and not tok.startswith("-"):
                a, _, b = tok.partition("-")
                ia, ib = order.get(_norm_id(a)), order.get(_norm_id(b))
                if ia is not None and ib is not None:
                    lo, hi = sorted((ia, ib))
                    picked.update(all_ids[lo:hi + 1])
            else:
                picked.add(_norm_id(tok))
    return sorted(picked, key=lambda s: order.get(s, 10**9))


def cmd_shot(name: str, step: str = "", *tokens: str):
    if step not in _SHOT_STEPS:
        raise SystemExit(
            f"❌ shot 只支持逐镜生成的步骤：{' / '.join(_SHOT_STEPS)}\n"
            f"   用法：shot {name} 03_keyframes SH003   （或 3 / 3-6 / all / missing）")
    if not tokens:
        raise SystemExit(
            f"❌ 请指定镜号：shot {name} {step} <镜号...>\n"
            f"   例：shot {name} {step} 3   ·   3-6   ·   SH003,SH007   ·   missing   ·   all")

    c = _c(name)
    spec = STEP_BY_ID[step]
    c.state.load()
    # 上游没批准就别烧钱
    not_ready = [u for u in spec.input_from if not c.state.is_done(u)]
    if not_ready:
        raise SystemExit(
            f"❌ 上游还没批准：{', '.join(not_ready)}。\n"
            f"   先 ok 掉上游再逐镜生成（否则拿不到 {STEP_BY_ID[step].title} 的输入）。")

    cfg = _SHOT_STEPS[step]
    all_ids = _ids_from_yaml(c.root / Path(*cfg["all_file"][:2]), cfg["all_file"][2])
    done_ids = set(_ids_from_yaml(c.root / Path(*cfg["done_file"][:2]), cfg["done_file"][2]))
    if not all_ids:
        raise SystemExit(
            f"❌ 找不到镜头清单（{'/'.join(cfg['all_file'][:2])}）。先跑通并批准上游。")

    only = _expand_targets(list(tokens), all_ids, done_ids)
    if not only:
        raise SystemExit(
            "❌ 没解析出任何镜号。检查写法（SH003 / 3 / 3-6 / all / missing），"
            f"或该步已全部生成（共 {len(all_ids)} 镜，已出 {len(done_ids)} 镜）。")

    print(render.before(spec))
    print(f"  🎯 本次只生成 {len(only)} 镜：{', '.join(only)}")
    res = c.run_step(spec, only=only)
    if not res.get("ok"):
        print(f"❌ 失败：{res.get('error')}")
        return
    print(render.after(spec, res.get("outputs") or spec.outputs, project=name))

    meta = res.get("meta") or {}
    total, indexed = meta.get("total", len(all_ids)), meta.get("indexed", 0)
    missing = meta.get("missing") or []
    print(f"  📊 {cfg['noun']}：本次出 {meta.get('generated', 0)} 张 · "
          f"累计 {indexed}/{total} 镜已完成")
    if meta.get("partial_error"):
        print(f"  ⚠️  有镜生成失败：{meta['partial_error']}（reject 报镜号可重试）")
    if meta.get("not_found"):
        print(f"  ⚠️  这些镜号不存在，已忽略：{', '.join(meta['not_found'])}")
    if missing:
        head = ", ".join(missing[:8]) + (" …" if len(missing) > 8 else "")
        print(f"  ⏳ 还缺 {len(missing)} 镜：{head}")
        print(f"     继续出下一张：shot {name} {step} <镜号>   ·   一次补齐：shot {name} {step} missing")
    else:
        print(f"  ✅ {total} 镜全部生成完毕，满意就批准：ok {name} {step}")


_CMDS = {
    "init":   cmd_init,
    "status": cmd_status,
    "next":   cmd_next,
    "run":    cmd_run,
    "shot":   cmd_shot,
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
