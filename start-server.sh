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

# 找出监听 $PORT 的进程 PID(优先 ss,退回 lsof/fuser),不同发行版都能用
pids_on_port() {
  if command -v ss >/dev/null 2>&1; then
    ss -ltnpH "sport = :${PORT}" 2>/dev/null | grep -oE 'pid=[0-9]+' | cut -d= -f2 | sort -u
  elif command -v lsof >/dev/null 2>&1; then
    lsof -tiTCP:"${PORT}" -sTCP:LISTEN 2>/dev/null | sort -u
  elif command -v fuser >/dev/null 2>&1; then
    fuser "${PORT}/tcp" 2>/dev/null | tr ' ' '\n' | grep -E '^[0-9]+$' | sort -u
  fi
}

# 端口被占 → 先停掉占用者,再启动(兼容:systemd 的 mvstudio 会 Restart=always,须先停服务)
if [[ -n "$(pids_on_port)" ]]; then
  echo "端口 ${PORT} 被占用,先释放……"
  # systemd 服务持有时:直接 kill 会被 Restart=always 立刻拉起并抢回端口,必须先停服务
  if command -v systemctl >/dev/null 2>&1 && systemctl is-active --quiet mvstudio 2>/dev/null; then
    echo "  检测到 mvstudio.service 在跑,systemctl stop mvstudio"
    sudo systemctl stop mvstudio || true
  fi
  # 停服务后仍残留(手动进程 / 别的进程)→ 逐个 kill,给 3 秒优雅退出再 -9
  for _ in 1 2 3; do
    remaining="$(pids_on_port)"
    [[ -z "$remaining" ]] && break
    echo "  kill PID: $(echo "$remaining" | tr '\n' ' ')"
    kill $remaining 2>/dev/null || true
    sleep 1
  done
  remaining="$(pids_on_port)"
  if [[ -n "$remaining" ]]; then
    echo "  仍未退出,强制 kill -9: $(echo "$remaining" | tr '\n' ' ')"
    kill -9 $remaining 2>/dev/null || true
    sleep 1
  fi
  if [[ -n "$(pids_on_port)" ]]; then
    echo "错误:端口 ${PORT} 仍被占用,无法启动。" >&2
    exit 1
  fi
fi

echo "启动 MVStudio 多租户服务器 → http://${HOST}:${PORT}  (create_app 工厂 = 多用户模式)"
exec "$PY" -m uvicorn apps.mv_api:create_app --factory --host "$HOST" --port "$PORT"
