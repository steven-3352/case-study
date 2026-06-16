#!/usr/bin/env python3
"""① 抓原料 · GitHub 仓库 + 线上 demo → context.md.

把项目原料压成一份纯文本投喂包，供 author.py 让 Claude 理解项目、提炼卖点。

用法:
  python3 pipeline/ingest.py --id P002 \
      --github https://github.com/owner/repo \
      --demo   https://demo.example.com \
      --note   "一句话定位（可选）"
"""
from __future__ import annotations

import argparse
import pathlib
import re
import subprocess
import sys
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]

# 投喂包体量上限（字符），避免把整个仓库塞进去
README_CAP = 24_000
SNIPPET_CAP = 2_400          # 单个源码文件
SOURCE_TOTAL_CAP = 48_000    # 所有源码片段合计
DEMO_TEXT_CAP = 8_000

MANIFESTS = [
    "package.json", "pyproject.toml", "requirements.txt", "Cargo.toml",
    "go.mod", "composer.json", "Gemfile", "pom.xml",
]
# 入口/代表性源码优先级（命中文件名包含即收）
ENTRY_HINTS = [
    "main.", "index.", "app.", "server.", "cli.", "__main__",
    "routes", "api", "handler", "core", "schema", "model",
]
SOURCE_EXT = {".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".rb", ".java", ".php", ".vue", ".svelte"}
SKIP_DIR = re.compile(r"(^|/)(node_modules|\.git|dist|build|vendor|\.venv|test|tests|__pycache__)/")


def run(cmd: list[str], cwd: pathlib.Path | None = None) -> str:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True).stdout


def clone(github: str, dest: pathlib.Path, force: bool) -> None:
    if dest.exists() and not force:
        print(f"  repo 已存在，跳过 clone（--force 重拉）: {dest}")
        return
    if dest.exists():
        subprocess.run(["rm", "-rf", str(dest)], check=True)
    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"  git clone --depth 1 {github}")
    r = subprocess.run(
        ["git", "clone", "--depth", "1", github, str(dest)],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        sys.exit(f"clone 失败：{r.stderr.strip()}")


def read_readme(repo: pathlib.Path) -> str:
    for name in ("README.md", "README.MD", "Readme.md", "README.rst", "README.txt", "README"):
        p = repo / name
        if p.exists():
            return p.read_text(encoding="utf-8", errors="replace")[:README_CAP]
    return "(无 README)"


def file_tree(repo: pathlib.Path) -> list[str]:
    out = run(["git", "ls-files"], cwd=repo)
    files = [f for f in out.splitlines() if f and not SKIP_DIR.search(f)]
    return files


def pick_sources(repo: pathlib.Path, files: list[str]) -> list[str]:
    cand = [f for f in files if pathlib.Path(f).suffix in SOURCE_EXT]
    cand.sort(key=lambda f: (0 if any(h in f.lower() for h in ENTRY_HINTS) else 1, len(f)))
    return cand


def snippet(repo: pathlib.Path, rel: str) -> str:
    try:
        txt = (repo / rel).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    return txt[:SNIPPET_CAP]


def fetch_demo_text(url: str) -> str:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except Exception as e:  # noqa: BLE001 — demo 可达性不该中断流程
        return f"(demo 抓取失败：{e})"
    html = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:DEMO_TEXT_CAP]


def build_context(args) -> str:
    out_dir = ROOT / "projects" / args.id
    repo = out_dir / "repo"
    clone(args.github, repo, args.force)

    readme = read_readme(repo)
    files = file_tree(repo)
    manifests = {m: (repo / m).read_text(encoding="utf-8", errors="replace")[:SNIPPET_CAP]
                 for m in MANIFESTS if (repo / m).exists()}
    commits = run(["git", "log", "--oneline", "-20"], cwd=repo).strip()
    demo_text = fetch_demo_text(args.demo) if args.demo else "(未提供 demo URL)"

    parts: list[str] = []
    parts.append(f"# 项目原料投喂包 · {args.id}\n")
    if args.note:
        parts.append(f"## 作者一句话定位\n{args.note}\n")
    parts.append(f"## 来源\n- GitHub: {args.github}\n- Demo: {args.demo or '(无)'}\n")
    parts.append(f"## README\n{readme}\n")
    if manifests:
        parts.append("## 依赖清单 / 技术栈")
        for name, body in manifests.items():
            parts.append(f"### {name}\n```\n{body}\n```")
        parts.append("")
    parts.append(f"## 文件树（{len(files)} 个，已过滤依赖/构建目录）\n```\n" + "\n".join(files[:300]) + "\n```\n")

    parts.append("## 关键源码片段")
    used = 0
    for rel in pick_sources(repo, files):
        if used >= SOURCE_TOTAL_CAP:
            break
        body = snippet(repo, rel)
        if not body.strip():
            continue
        chunk = f"### {rel}\n```\n{body}\n```"
        parts.append(chunk)
        used += len(chunk)
    parts.append("")

    parts.append(f"## 近期提交\n```\n{commits}\n```\n")
    parts.append(f"## Demo 页面文本（去标签）\n{demo_text}\n")
    return "\n".join(parts)


def main() -> None:
    ap = argparse.ArgumentParser(description="抓原料 → context.md")
    ap.add_argument("--id", required=True)
    ap.add_argument("--github", required=True)
    ap.add_argument("--demo", default="")
    ap.add_argument("--note", default="")
    ap.add_argument("--force", action="store_true", help="重新 clone")
    args = ap.parse_args()

    out_dir = ROOT / "projects" / args.id
    out_dir.mkdir(parents=True, exist_ok=True)
    ctx = build_context(args)
    out = out_dir / "context.md"
    out.write_text(ctx, encoding="utf-8")
    print(f"\n✓ {out} · {len(ctx)} 字")


if __name__ == "__main__":
    main()
