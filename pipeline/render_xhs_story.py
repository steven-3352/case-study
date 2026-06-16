#!/usr/bin/env python3
"""小红书 story 图文 · 路线 1（兼容入口，转调 render_route1_carousel）."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
subprocess.run([sys.executable, str(ROOT / "pipeline" / "render_route1_carousel.py"), "xhs-story"], check=True)
