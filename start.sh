#!/usr/bin/env bash
set -euo pipefail

# MVStudio · Web Service Startup Script (macOS / Linux)
# Usage:  ./start.sh [port]
#         MV_PORT=9000 ./start.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ── config ───────────────────────────────────────────────────────
PORT="${1:-${MV_PORT:-8787}}"
HOST="127.0.0.1"
VENV_DIR=".venv"
RED='\033[0;31m'; YELLOW='\033[1;33m'; GREEN='\033[0;32m'; CYAN='\033[0;36m'; NC='\033[0m'

ok()   { echo -e "${GREEN}[OK]${NC}   $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
fail() { echo -e "${RED}[FAIL]${NC} $*" >&2; exit 1; }
info() { echo -e "${CYAN}       $*${NC}"; }
hr()   { echo "──────────────────────────────────────────────────"; }

hr; echo "  MVStudio Web Service  ·  $(date '+%Y-%m-%d %H:%M:%S')"; hr

# ── 1. Python 3.9+ ───────────────────────────────────────────────
echo; echo "▸ Python"
PYTHON_CMD=""
for cmd in python3 python; do
  if command -v "$cmd" &>/dev/null; then
    PY_VER=$("$cmd" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || echo "0.0")
    MAJOR="${PY_VER%%.*}"; MINOR="${PY_VER##*.}"
    if [ "$MAJOR" -ge 3 ] && [ "$MINOR" -ge 9 ]; then
      PYTHON_CMD="$cmd"; ok "Python $("$cmd" --version 2>&1)"; break
    fi
  fi
done
[ -z "$PYTHON_CMD" ] && fail "Python 3.9+ not found.\n       macOS: brew install python3\n       Linux: apt install python3"

# ── 2. Virtual environment ───────────────────────────────────────
echo; echo "▸ Virtual environment"
if [ ! -d "$VENV_DIR" ]; then
  warn ".venv not found — creating (first-time setup)..."
  "$PYTHON_CMD" -m venv "$VENV_DIR" || fail "venv creation failed"
  ok "Created $VENV_DIR"
else
  ok ".venv exists"
fi
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

# ── 3. Python packages ───────────────────────────────────────────
echo; echo "▸ Python packages"
if ! python -c "import uvicorn, fastapi, dotenv, pydantic, PIL, yaml" &>/dev/null 2>&1; then
  warn "Missing packages — installing from requirements.txt..."
  pip install -r requirements.txt -q || fail "pip install failed"
  ok "Packages installed"
else
  ok "Core packages present (uvicorn, fastapi, pydantic, PIL, yaml)"
fi

# ── 4. Playwright chromium ───────────────────────────────────────
echo; echo "▸ Playwright"
if ! python -c "import playwright" &>/dev/null 2>&1; then
  warn "playwright not installed — installing..."
  pip install playwright -q
fi
if ! python -m playwright install --dry-run 2>&1 | grep -q "chromium"; then
  warn "Chromium browser not found — installing (one-time ~150 MB)..."
  python -m playwright install chromium || warn "Chromium install failed — browser tests will not work"
else
  ok "Playwright + Chromium ready"
fi

# ── 5. ffmpeg ────────────────────────────────────────────────────
echo; echo "▸ System: ffmpeg"
if command -v ffmpeg &>/dev/null; then
  ok "$(ffmpeg -version 2>&1 | head -1)"
else
  warn "ffmpeg not found — video rendering will fail"
  info "macOS:  brew install ffmpeg"
  info "Ubuntu: sudo apt install ffmpeg"
  info "Arch:   sudo pacman -S ffmpeg"
fi

# ── 6. .env file & key checks ────────────────────────────────────
echo; echo "▸ Environment (.env)"
if [ ! -f ".env" ]; then
  warn ".env not found — run: cp .env.example .env  then fill in API keys"
  info "Service will start but API-dependent features will fail"
else
  ok ".env found"
  _chkkey() {
    local key="$1"
    local val
    val=$(grep -E "^${key}=" .env 2>/dev/null | cut -d= -f2- | xargs || true)
    if [ -z "$val" ]; then warn "  .env: ${key} is empty"; fi
  }
  _chkkey LLM_API_KEY;       _chkkey LLM_BASE_URL
  _chkkey GPT_IMAGE_API_KEY; _chkkey GPT_IMAGE_BASE_URL
  _chkkey TTS_API_KEY;       _chkkey TTS_BASE_URL
  _chkkey SEEDANCE_API_KEY;  _chkkey SEEDANCE_BASE_URL
  _chkkey GROK_API_KEY;      _chkkey GROK_BASE_URL
  _chkkey MINIMAX_API_KEY;   _chkkey MINIMAX_BASE_URL
fi

# ── 7. Port availability ─────────────────────────────────────────
echo; echo "▸ Port $PORT"
_kill_port() {
  local pids=""
  if command -v lsof &>/dev/null; then
    pids=$(lsof -ti TCP:"$PORT" -sTCP:LISTEN 2>/dev/null || true)
  elif command -v ss &>/dev/null; then
    pids=$(ss -tlnp 2>/dev/null | grep ":${PORT} " | grep -oE 'pid=[0-9]+' | cut -d= -f2 | sort -u || true)
  elif command -v netstat &>/dev/null; then
    pids=$(netstat -tlnp 2>/dev/null | awk "/:${PORT} /{print \$7}" | cut -d/ -f1 | sort -u || true)
  fi
  [ -z "$pids" ] && return 1
  for pid in $pids; do
    warn "Port $PORT busy — killing PID $pid..."
    kill -TERM "$pid" 2>/dev/null || true
  done
  # Poll up to 5 s; escalate to SIGKILL after 2 s
  local waited=0
  while [ "$waited" -lt 10 ]; do
    sleep 0.5
    waited=$((waited + 1))
    local still=""
    if command -v lsof &>/dev/null; then
      still=$(lsof -ti TCP:"$PORT" -sTCP:LISTEN 2>/dev/null || true)
    fi
    [ -z "$still" ] && return 0
    if [ "$waited" -eq 4 ]; then
      for pid in $pids; do kill -KILL "$pid" 2>/dev/null || true; done
    fi
  done
  return 0
}

port_busy=0
if command -v lsof &>/dev/null; then
  lsof -iTCP:"$PORT" -sTCP:LISTEN -n &>/dev/null 2>&1 && port_busy=1
elif command -v ss &>/dev/null; then
  ss -tln 2>/dev/null | grep -q ":${PORT} " && port_busy=1
elif command -v netstat &>/dev/null; then
  netstat -an 2>/dev/null | grep -q "[:.]${PORT} .*LISTEN" && port_busy=1
fi
if [ "$port_busy" -eq 1 ]; then
  _kill_port || true
fi
ok "Port $PORT ready"

# ── 8. Launch ────────────────────────────────────────────────────
echo
hr; echo "  http://${HOST}:${PORT}  (Ctrl-C to stop)"; hr
echo

export PYTHONPATH="$SCRIPT_DIR"
export MV_HOST="$HOST"
export MV_PORT="$PORT"

exec python -m uvicorn apps.mv_api:create_app \
  --factory \
  --host "$HOST" \
  --port "$PORT"
