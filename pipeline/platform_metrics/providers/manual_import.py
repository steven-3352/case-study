"""手动 JSON/CSV 导入 · API 兜底."""
from __future__ import annotations

import json
import pathlib
from typing import Any


def load_import_file(path: pathlib.Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        data = json.loads(text)
    else:
        raise ValueError("仅支持 .json 导入（见 templates/design/platform_metrics_import.example.json）")

    if "metrics" in data:
        m = dict(data["metrics"])
        m["_source"] = data.get("source", "manual_json")
        return {
            "project_id": data.get("project_id"),
            "platform": data.get("platform", "douyin"),
            "metrics": m,
        }
    raise ValueError("JSON 须含 project_id, platform, metrics")
