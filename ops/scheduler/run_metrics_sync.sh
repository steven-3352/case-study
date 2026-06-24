#!/bin/bash
# 平台数据定时同步 · launchd 调用
# 过期时自动弹浏览器 + macOS 对话框扫码

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

PY="${ROOT}/.venv/bin/python"
if [[ ! -x "$PY" ]]; then
  PY=python3
fi

exec "$PY" "${ROOT}/pipeline/fetch_platform_metrics.py" --scheduled \
  --week "${ROOT}/publish/2026-W26" \
  >> "${ROOT}/ops/logs/metrics_sync.log" 2>&1
