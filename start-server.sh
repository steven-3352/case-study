#!/usr/bin/env bash
# MVStudio 多租户服务器启动脚本
#
# 与 systemd 的 mvstudio.service 等价(见 docs/design/MULTIUSER_SERVER_DEPLOYMENT.md)。
# 正式部署用 systemd(开机自启 + 崩溃拉起);本脚本用于手动/临时启动、调试。
#
# 用法:
#   ./start-server.sh              # 默认监听 127.0.0.1:8787,前面挂 nginx 对外
#   HOST=0.0.0.0 ./start-server.sh # 直接对外(无 nginx 时;注意 .env 不做凭据来源)
#   PORT=9000 ./start-server.sh    # 换端口
set -euo pipefail

# 切到脚本所在目录 = 项目根,保证相对导入/工作区解析一致
cd "$(dirname "$(readlink -f "$0")")"

HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8787}"

# 优先用项目内 venv 的 python,没有就退回 PATH 里的 python3
if [[ -x .venv/bin/python ]]; then
  PY=.venv/bin/python
else
  PY="$(command -v python3)"
fi

export PYTHONUNBUFFERED=1
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

echo "启动 MVStudio 多租户服务器 → http://${HOST}:${PORT}  (create_app 工厂 = 多用户模式)"
exec "$PY" -m uvicorn apps.mv_api:create_app --factory --host "$HOST" --port "$PORT"
