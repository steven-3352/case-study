#!/usr/bin/env python3
"""按 week.yaml 生成本周发布包：目录 / content.yaml / publish.md（含定时）.

  python3 pipeline/week_build.py
  python3 pipeline/week_build.py --render          # 生成后跑 render.py
  python3 pipeline/week_build.py --render --id W26D01
"""
from __future__ import annotations

import argparse
import pathlib
import shutil
import subprocess
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

WEEK_DIR = ROOT / "publish" / "2026-W26"
TOPICS_PATH = WEEK_DIR / "topics_content.yaml"
WEEK_PATH = WEEK_DIR / "week.yaml"

SPEC = {
    "douyin": "1080×1920 · 竖屏 · 前 1s 大字钩子 · 目标 35–50s",
    "xhs": "1080×1920 · 视频≤60s 或 图文 5–7 张 · 演示满铺 + 底部字幕",
}
NAME = {"douyin": "抖音", "xhs": "小红书"}

SCORECARD_PASS = 90


def _run_gate(day_dir: pathlib.Path, phase: str, label: str) -> bool:
    from pipeline.gate_check import gate_check

    r = gate_check(day_dir, phase=phase)
    if r.ok:
        return True
    print(f"  ✗ {label} gate_check({phase}) FAIL — 铁律 blocked")
    for e in r.errors[:12]:
        print(f"      · {e}")
    if len(r.errors) > 12:
        print(f"      · …共 {len(r.errors)} 项 · python3 pipeline/gate_check.py --day {day_dir.name}")
    return False


def publish_md(
    *,
    week_id: str,
    day: str,
    slug: str,
    vertical: str,
    project_id: str,
    topic_id: str,
    plat: str,
    fmt: str,
    publish_at: str,
    topic: dict,
    spec: dict,
) -> str:
    tags = " ".join(f"#{t}" for t in (spec.get("tags") or []))
    cover = spec.get("cover") or {}
    assets = f"publish/{week_id}/{day}-{slug}/{plat}"
    lines = [
        f"# {NAME[plat]} · {week_id} · {day} · {slug}",
        "",
        f"> 板块：{vertical} · 选题 {topic_id} · 形式 **{fmt}** · 项目 `{project_id}`",
        f"> 痛点：{topic.get('pain', '')}",
        f"> 解决：{topic.get('solves', '')}",
        f"> 钩子：{topic.get('hook', '')}",
        "",
        "## 定时发布",
        f"- **发布时间**：`{publish_at}`（北京时间，发布前 10 分钟完成上传）",
        f"- **content_id**：`{topic_id}`",
        f"- **format_test**：`{fmt}`",
        "",
        "## 标题",
        spec.get("title", ""),
        "",
        "## 正文",
        spec.get("body", ""),
        "",
        "## 标签",
        tags,
        "",
        "## 互动钩子",
        spec.get("interaction", ""),
        "",
        "## 封面",
        f"大字钩子：{cover.get('hook', '').replace(chr(10), ' / ')}",
        f"封面图：`{assets}/cover.png`",
        "",
        "## 素材",
        f"- 视频：`{assets}/video.mp4`",
        f"- 封面：`{assets}/cover.png`",
        f"- 图文轮播（如有）：`{assets}/carousel/`",
        "",
        "## 规格",
        f"- {SPEC[plat]}",
        f"- 目标时长：{spec.get('duration_s', '?')}s",
        "",
        "## 口播分镜",
    ]
    for i, seg in enumerate(spec.get("segments") or [], 1):
        kind = seg.get("evidence_kind", "none")
        src = seg.get("source") if kind in ("none", None) else f"{seg.get('source')}/{kind}"
        lines.append(f"{i}. [{src}] 「{seg.get('sub')}」 {seg.get('vo')}")
    lines += [
        "",
        "## 发布后",
        f"- 填入 `ops/metrics.csv`：content_id={topic_id}, format={fmt}, platform={plat}",
        "- 48h / 7d 回填曝光、互动、私信",
    ]
    return "\n".join(lines)


def meta_yaml(day_cfg: dict, topic: dict, week_id: str, *, status: str = "draft") -> dict:
    return {
        "week_id": week_id,
        "day": day_cfg["day"],
        "slug": day_cfg["slug"],
        "vertical": day_cfg["vertical"],
        "project_id": day_cfg["project_id"],
        "topic_id": day_cfg["topic_id"],
        "status": status,
        "formats": {
            "douyin": day_cfg["douyin"]["format"],
            "xhs": day_cfg["xhs"]["format"],
        },
        "schedule": {
            "douyin": day_cfg["douyin"]["publish_at"],
            "xhs": day_cfg["xhs"]["publish_at"],
        },
        "topic": {
            "pain": topic.get("pain"),
            "hook": topic.get("hook"),
        },
    }


def build_one(day_cfg: dict, topics: dict, week_id: str, *, force: bool = False) -> None:
    pid = day_cfg["project_id"]
    topic = topics[pid]
    day_dir = WEEK_DIR / f"{day_cfg['day']}-{day_cfg['slug']}"
    verdict_path = day_dir / "room" / "verdict.yaml"
    verdict: dict = {}
    if verdict_path.exists():
        verdict = yaml.safe_load(verdict_path.read_text(encoding="utf-8")) or {}
    if not force:
        if not verdict_path.exists():
            print(f"  ⚠ {day_cfg['day']}-{day_cfg['slug']} 无 room/verdict.yaml，跳过（先跑 week_room.py）")
            return
        if verdict.get("status") != "approved":
            print(f"  ⚠ {day_cfg['day']}-{day_cfg['slug']} 讨论室未 approved，跳过")
            return
        # 铁律：永远跑 gate_check，不因 gates.*=true 跳过（防手填绕过）
        if not _run_gate(day_dir, "approve", f"{day_cfg['day']}-{day_cfg['slug']}"):
            return
    day_dir.mkdir(parents=True, exist_ok=True)
    proj_dir = ROOT / "projects" / pid
    proj_dir.mkdir(parents=True, exist_ok=True)

    content = {
        "topic": {
            "id": pid,
            "pain": topic["pain"],
            "solves": topic["solves"],
            "hook": topic["hook"],
            "angle": topic.get("angle", ""),
        },
        "shots": [],
        "douyin": topic["douyin"],
        "xhs": dict(topic["xhs"]),
    }
    xhs = content["xhs"]
    if "segments" not in topic["xhs"]:
        dy_segs = topic["douyin"].get("segments") or []
        xhs["segments"] = dy_segs[:4] if len(dy_segs) > 4 else dy_segs
        xhs["duration_s"] = min(42, topic["douyin"].get("duration_s", 42))
    (proj_dir / "content.yaml").write_text(
        yaml.dump(content, allow_unicode=True, sort_keys=False, width=120),
        encoding="utf-8",
    )

    (day_dir / "meta.yaml").write_text(
        yaml.dump(
            meta_yaml(day_cfg, topic, week_id, status=verdict.get("status", "draft")),
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    for plat in ("douyin", "xhs"):
        plat_cfg = day_cfg[plat]
        plat_dir = day_dir / plat
        plat_dir.mkdir(parents=True, exist_ok=True)
        (plat_dir / "carousel").mkdir(exist_ok=True)
        md = publish_md(
            week_id=week_id,
            day=day_cfg["day"],
            slug=day_cfg["slug"],
            vertical=day_cfg["vertical"],
            project_id=pid,
            topic_id=day_cfg["topic_id"],
            plat=plat,
            fmt=plat_cfg["format"],
            publish_at=plat_cfg["publish_at"],
            topic=topic,
            spec=topic[plat],
        )
        (plat_dir / "publish.md").write_text(md, encoding="utf-8")

    print(f"  ✓ {day_cfg['day']}-{day_cfg['slug']} → projects/{pid}/content.yaml + publish/{week_id}/...")


def sync_assets(pid: str, day_cfg: dict) -> None:
    """render 产出在 publish/.staging/{pid}/，同步到周目录."""
    day_dir = WEEK_DIR / f"{day_cfg['day']}-{day_cfg['slug']}"
    src_root = ROOT / "publish" / ".staging" / pid
    if not src_root.exists():
        # 兼容旧路径 publish/{pid}/
        src_root = ROOT / "publish" / pid
    if not src_root.exists():
        print(f"  ⚠ 无 render 产出 .staging/{pid}/，跳过同步")
        return
    for plat in ("douyin", "xhs"):
        src = src_root / plat
        dst = day_dir / plat
        if not src.exists():
            continue
        for name in ("video.mp4", "cover.png"):
            f = src / name
            if f.exists():
                shutil.copy2(f, dst / name)
        car = src / "carousel"
        if car.exists() and any(car.iterdir()):
            shutil.copytree(car, dst / "carousel", dirs_exist_ok=True)
    print(f"  ✓ 同步素材 → {day_dir.relative_to(ROOT)}")


def run_render(pid: str) -> None:
    subprocess.run(
        [sys.executable, str(ROOT / "pipeline" / "render.py"), "--id", pid],
        cwd=str(ROOT),
        check=False,
    )


def write_week_readme(week: dict) -> None:
    lines = [
        f"# {week['week_id']} · {week['title']}",
        "",
        f"周期：**{week['start_date']}** → **{week['end_date']}**",
        "",
        f"目标：{week['goal']}",
        "",
        "## 目录",
        "",
        "```",
        f"publish/{week['week_id']}/",
        "├── week.yaml          # 排期 + 形式矩阵",
        "├── topics_content.yaml",
        "├── D01-美甲撞档/",
        "│   ├── meta.yaml",
        "│   ├── douyin/        # publish.md + video.mp4 + cover.png",
        "│   └── xhs/",
        "└── … D02–D07",
        "```",
        "",
        "## 发布排期",
        "",
        "| 天 | 日期 | 抖音（时间·形式） | 小红书（时间·形式） |",
        "|----|------|-------------------|---------------------|",
    ]
    for d in week["days"]:
        dy = d["douyin"]
        xh = d["xhs"]
        date = dy["publish_at"][:10]
        lines.append(
            f"| {d['day']} | {date} | {dy['publish_at'][11:16]} {dy['format']} | "
            f"{xh['publish_at'][11:16]} {xh['format']} |"
        )
    lines += [
        "",
        "## 生成命令",
        "",
        "```bash",
        "python3 pipeline/week_build.py              # 文案 + content.yaml",
        "python3 pipeline/week_build.py --render     # 并渲染视频",
        "python3 pipeline/gate_check.py --all      # 铁律门禁（fail-closed）",
        "```",
        "",
        "## 形式说明",
        "",
    ]
    for k, v in week.get("formats", {}).items():
        lines.append(f"- **{k}**：{v}")
    (WEEK_DIR / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description="构建周发布包")
    ap.add_argument("--week", type=pathlib.Path, default=WEEK_PATH)
    ap.add_argument("--render", action="store_true", help="构建后执行 render.py")
    ap.add_argument("--force", action="store_true", help="忽略 Agent 讨论室门禁")
    ap.add_argument("--id", help="只处理/渲染指定 project_id，如 W26D01")
    args = ap.parse_args()

    week = yaml.safe_load(args.week.read_text(encoding="utf-8"))
    topics = yaml.safe_load(TOPICS_PATH.read_text(encoding="utf-8"))
    week_id = week["week_id"]

    print(f"构建 {week_id} …")
    write_week_readme(week)
    for day_cfg in week["days"]:
        build_one(day_cfg, topics, week_id, force=args.force)

    if args.render:
        days = week["days"]
        if args.id:
            days = [d for d in days if d["project_id"] == args.id]
        for day_cfg in days:
            pid = day_cfg["project_id"]
            day_dir = WEEK_DIR / f"{day_cfg['day']}-{day_cfg['slug']}"
            if not args.force:
                # 铁律：TTS/render 有成本 · 须 pre_render 全工种 90+（不论 verdict status）
                if not _run_gate(day_dir, "pre_render", f"{pid} pre_render"):
                    print(f"  ⛔ {pid} 跳过 TTS/render — 先 gate_check(pre_render) PASS")
                    continue
            print(f"\n渲染 {pid} …")
            run_render(pid)
            sync_assets(pid, day_cfg)

    print(f"\n完成 → publish/{week_id}/")


if __name__ == "__main__":
    main()
