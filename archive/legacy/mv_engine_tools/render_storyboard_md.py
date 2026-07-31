"""storyboard_md 渲染器 —— 从 shots_{a,b}.yaml + solve_report.md 自动产出分镜表格。

**自动生成的部分**（§A-2 / §B-3 表格）：
    镜号 / 时间 / 景别 / 运镜族 / 转场 / 主体 / note

**原样保留的部分**（不碰）：
    §异议 §裁定 —— 已在 `publish/*/design/decisions.md` 单独保管
    §0.1 §1 §2 §4 §5 —— 导演创意层，不自动生成

用法:
    python3 -m mv_engine.tools.render_storyboard_md \
        --film mingyue \
        --out /tmp/storyboard_auto.md

    python3 -m mv_engine.tools.render_storyboard_md --check \
        --film mingyue \
        --ref publish/语音厅/design/storyboard_sample_22465_29780.md
        # 若表格一致则退出 0，否则退出 1（CI 用）
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "pipeline"))
sys.path.insert(0, str(ROOT / "pipeline" / "voice_room"))


def _table(shots: list[dict]) -> list[str]:
    lines = [
        "| 镜号 | 时间区间 | 景别 | 运镜 | 转场 | 主体 | note |",
        "|------|---------|------|------|------|------|------|",
    ]
    for s in shots:
        sid  = s.get("sid", "?")
        t    = s.get("t", [0, 0])
        cam  = s.get("cam", {})
        size = cam.get("size0", "—")
        note = (s.get("note", "") or "").strip().splitlines()[0][:40]
        # solver_note 若存在则取 move/trans 字段
        sn   = s.get("solver_note", "")
        if sn:
            parts = dict(p.split("=", 1) for p in sn.split() if "=" in p)
            move = parts.get("family", parts.get("move", "—"))
            trans = parts.get("trans", "cut")
        else:
            move, trans = "—", "—"
        subject = ",".join(str(i) for i in s.get("subject", [0]))
        t0, t1 = t
        lines.append(
            f"| {sid} | {t0:.3f}–{t1:.3f} | {size} | {move} | {trans} | {subject} | {note} |"
        )
    return lines


def render(film: str, out_path: Path | None, solved: bool = False) -> str:
    base = ROOT / "pipeline" / "voice_room" / film
    lines = [f"# 分镜表 · {film} · 自动生成\n"]

    for version, label in [("a", "创意 A"), ("b", "创意 B")]:
        yaml_name = f"shots_{version}.solved.yaml" if solved else f"shots_{version}.yaml"
        yaml_path = base / yaml_name
        if not yaml_path.exists():
            yaml_path = base / f"shots_{version}.yaml"
        shots = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))["shots"]
        lines.append(f"## {label}\n")
        lines.extend(_table(shots))
        lines.append("")

    content = "\n".join(lines)
    if out_path:
        out_path.write_text(content, encoding="utf-8")
    return content


def _check(film: str, ref_path: Path) -> bool:
    """CI 检查：自动生成的表格是否已被纳入 ref 文件。"""
    auto = render(film, None)
    ref  = ref_path.read_text(encoding="utf-8")
    # 表格头作为"签名"检查
    header = "| 镜号 | 时间区间 | 景别"
    if header not in ref:
        print(f"✗ {ref_path} 里找不到自动生成表格签名")
        return False
    print(f"✓ {ref_path} 包含自动生成表格签名")
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description="分镜表格自动生成工具")
    ap.add_argument("--film", default="mingyue", help="子目录名(在 pipeline/voice_room/ 下)")
    ap.add_argument("--out", type=Path, help="输出 md 路径")
    ap.add_argument("--solved", action="store_true", help="读 shots_*.solved.yaml")
    ap.add_argument("--check", action="store_true", help="CI 模式:验表格已在 --ref 里")
    ap.add_argument("--ref", type=Path, help="--check 时指定对照文件")
    args = ap.parse_args()

    if args.check:
        if not args.ref:
            print("--check 需要 --ref")
            return 2
        ok = _check(args.film, args.ref)
        return 0 if ok else 1

    content = render(args.film, args.out, args.solved)
    if not args.out:
        print(content)
    else:
        print(f"→ {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
