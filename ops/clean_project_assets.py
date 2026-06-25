#!/usr/bin/env python3
"""List or delete project-scoped heavy media assets.

Default is dry-run. The tool only targets media/output files under publish/,
projects/*/assets, projects/*/out, and pipeline/**/out.
"""
from __future__ import annotations

import argparse
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]

MEDIA_EXTS = {
    ".mp4", ".mov", ".webm", ".m4v",
    ".png", ".jpg", ".jpeg", ".webp", ".gif",
    ".mp3", ".wav", ".aiff", ".m4a",
}

DEFAULT_TARGETS = (
    "publish",
    "projects",
    "pipeline",
)


def is_heavy_asset(path: pathlib.Path) -> bool:
    if path.suffix.lower() in MEDIA_EXTS:
        return True
    parts = path.relative_to(ROOT).parts
    return "out" in parts or "_tmp" in parts


def is_allowed_scope(path: pathlib.Path) -> bool:
    rel = path.relative_to(ROOT)
    parts = rel.parts
    if not parts:
        return False
    if parts[0] == "publish":
        return True
    if parts[0] == "projects" and ("assets" in parts or "out" in parts):
        return True
    if parts[0] == "pipeline" and "out" in parts:
        return True
    return False


def iter_assets(base: pathlib.Path) -> list[pathlib.Path]:
    if not base.exists():
        raise SystemExit(f"Path not found: {base}")
    if base.is_file():
        candidates = [base]
    else:
        candidates = [p for p in base.rglob("*") if p.is_file()]
    return sorted(
        p for p in candidates
        if p.is_relative_to(ROOT) and is_allowed_scope(p) and is_heavy_asset(p)
    )


def format_size(n: int) -> str:
    units = ("B", "KB", "MB", "GB")
    size = float(n)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.1f}{unit}"
        size /= 1024
    return f"{size:.1f}GB"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "paths",
        nargs="*",
        help="Project folders to scan, e.g. publish/2026-W26/D08-xxx. Defaults to publish projects pipeline.",
    )
    ap.add_argument("--delete", action="store_true", help="Delete matched files. Default only lists.")
    args = ap.parse_args()

    bases = [ROOT / p for p in (args.paths or DEFAULT_TARGETS)]
    assets: list[pathlib.Path] = []
    for base in bases:
        assets.extend(iter_assets(base.resolve()))

    total = 0
    for path in sorted(set(assets)):
        size = path.stat().st_size
        total += size
        rel = path.relative_to(ROOT)
        print(f"{format_size(size):>9}  {rel}")
        if args.delete:
            path.unlink()

    action = "deleted" if args.delete else "matched"
    print(f"\n{action}: {len(set(assets))} files · {format_size(total)}")
    if not args.delete:
        print("dry-run only. Re-run with --delete to remove these files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
