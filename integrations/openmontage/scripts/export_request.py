#!/usr/bin/env python3
"""Export a case-study OpenMontage request into an OpenMontage project."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--content-dir", required=True, help="case-study publish content directory")
    parser.add_argument("--project-dir", required=True, help="OpenMontage project directory")
    parser.add_argument("--request-name", default="openmontage_request.md")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    content_dir = Path(args.content_dir).resolve()
    project_dir = Path(args.project_dir).resolve()
    request_path = content_dir / args.request_name
    if not request_path.is_file():
        raise SystemExit(f"Missing request file: {request_path}")

    artifacts = project_dir / "artifacts"
    artifacts.mkdir(parents=True, exist_ok=True)
    shutil.copy2(request_path, artifacts / "case_study_openmontage_request.md")

    manifest = {
        "source_content_dir": str(content_dir),
        "request": str(request_path),
        "project_dir": str(project_dir),
        "expected_output_dir": str(content_dir / "openmontage_production"),
    }
    (artifacts / "case_study_handoff.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
