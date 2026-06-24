#!/bin/bash
# 安装 macOS 定时任务 · 每天 9:00 / 21:00 拉取平台数据
# 用法: bash ops/scheduler/install_launchd.sh

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PLIST_SRC="${ROOT}/ops/scheduler/com.casestudy.platform-metrics.plist"
PLIST_DST="${HOME}/Library/LaunchAgents/com.casestudy.platform-metrics.plist"
RUN_SH="${ROOT}/ops/scheduler/run_metrics_sync.sh"

chmod +x "$RUN_SH"
mkdir -p "${ROOT}/ops/logs"

# 写入绝对路径
sed "s|__ROOT__|${ROOT}|g" "$PLIST_SRC" > "$PLIST_DST"

launchctl bootout "gui/$(id -u)/com.casestudy.platform-metrics" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST_DST"
launchctl enable "gui/$(id -u)/com.casestudy.platform-metrics"
launchctl kickstart -k "gui/$(id -u)/com.casestudy.platform-metrics" 2>/dev/null || true

echo "✓ 已安装 LaunchAgent: $PLIST_DST"
echo "  日志: ${ROOT}/ops/logs/metrics_sync.log"
launchctl print "gui/$(id -u)/com.casestudy.platform-metrics" 2>/dev/null | head -20 || true
