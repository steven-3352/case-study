#!/bin/bash
# 首次登录 · 抖音 + 小红书扫码（弹浏览器 + 对话框）
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
exec "${ROOT}/.venv/bin/python" "${ROOT}/pipeline/fetch_platform_metrics.py" --login-all
