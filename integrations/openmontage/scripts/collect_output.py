#!/usr/bin/env python3
"""Collect OpenMontage production artifacts back into case-study."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


ARTIFACT_NAMES = [
    "final.mp4",
    "final_silent.mp4",
    "contact_sheet.png",
    "generation_results.json",
    "render_report.json",
    "asset_manifest.json",
    "edit_decisions.json",
    "subtitle.srt",
    "review.md",
    "decision_log.md",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", required=True, help="OpenMontage project directory")
    parser.add_argument("--content-dir", required=True, help="case-study publish content directory")
    parser.add_argument(
        "--source-dir",
        help="Directory containing render outputs. Defaults to <project-dir>/case_study_output.",
    )
    parser.add_argument("--output-name", default="openmontage_production")
    return parser.parse_args()


def copy_if_exists(src: Path, dst: Path) -> bool:
    if not src.is_file():
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return True


def main() -> None:
    args = parse_args()
    project_dir = Path(args.project_dir).resolve()
    content_dir = Path(args.content_dir).resolve()
    source_dir = Path(args.source_dir).resolve() if args.source_dir else project_dir / "case_study_output"
    output_dir = content_dir / args.output_name
    output_dir.mkdir(parents=True, exist_ok=True)

    copied: list[str] = []
    for name in ARTIFACT_NAMES:
        candidates = [
            source_dir / name,
            project_dir / "renders_production" / name,
            project_dir / "artifacts" / name,
        ]
        for candidate in candidates:
            if copy_if_exists(candidate, output_dir / name):
                copied.append(name)
                break

    print("Copied:")
    for name in copied:
        print(f"- {output_dir / name}")


if __name__ == "__main__":
    main()
