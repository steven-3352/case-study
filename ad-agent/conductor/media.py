"""共享媒体/配置助手（ad-agent 版）— tools.py 六步工具都用它。

职责单一：环境与 provider 配置、图片尺寸/校验、画幅映射、sha256 摘要、
产品原图贴到 AI 背景的保真合成（PIL）、静态/Ken Burns 转 mp4（ffmpeg）、结构化错误。
不做业务判断、不碰状态机。

所有 provider 类来自 src/mvstudio/*（只读复用，不改引擎）。
保真铁律：产品原图像素一律不重绘——合成时按比例缩放后原样 paste，产品区 = 原始字节。
"""
from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

# ── 让 mv_platform / mvstudio 可 import（项目根 = ad-agent 的上两级）
_REPO_ROOT = Path(__file__).resolve().parents[2]
for _p in (str(_REPO_ROOT), str(_REPO_ROOT / "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ── 加载 ad-agent/.env
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=False)
except ImportError:
    pass

try:
    from mv_platform.application.control_plane import ENV_MAP
    _MV_PLATFORM_OK = True
except ImportError:
    ENV_MAP, _MV_PLATFORM_OK = {}, False


IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp"}
TEXT_EXT = {".txt", ".md"}

# 画幅 → (图像生成尺寸, 成片画布 WxH, Seedance 比例)
#   gpt-image 支持 1024x1536 / 1536x1024 / 1024x1024；
#   Seedance i2v 只支持 9:16 / 16:9 —— 1:1 目标的 i2v 镜按 9:16 出片再由 compose 填充到方画布。
ASPECT_MAP = {
    "9:16": {"image_size": "1024x1536", "canvas": (720, 1280),  "video_ratio": "9:16"},
    "16:9": {"image_size": "1536x1024", "canvas": (1280, 720),  "video_ratio": "16:9"},
    "1:1":  {"image_size": "1024x1024", "canvas": (1080, 1080), "video_ratio": "9:16"},
}
DEFAULT_ASPECT = "9:16"


def err(code: str, message: str, hint: str = "") -> dict:
    """结构化错误（控制器会把它路由到 reject，用户看得懂的中文）。"""
    return {"code": code, "message": message, "hint": hint}


def sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def ffmpeg_bin() -> str:
    return os.environ.get("MVSTUDIO_FFMPEG_PATH") or shutil.which("ffmpeg") or "ffmpeg"


def ffprobe_bin() -> str:
    return os.environ.get("MVSTUDIO_FFPROBE_PATH") or shutil.which("ffprobe") or "ffprobe"


def provider_config() -> dict:
    """os.environ → 嵌套 {section:{key:val}}，键遵循 ENV_MAP。"""
    cfg: dict = {}
    for dotted, env_key in ENV_MAP.items():
        section, key = dotted.split(".", 1)
        val = os.environ.get(env_key, "")
        if val:
            cfg.setdefault(section, {})[key] = val
    return cfg


def max_shots() -> Optional[int]:
    """小样验证的镜头上限：环境变量 AD_MAX_SHOTS（未设=不限）。"""
    raw = os.environ.get("AD_MAX_SHOTS", "").strip()
    if not raw:
        return None
    try:
        n = int(raw)
        return n if n > 0 else None
    except ValueError:
        return None


def normalize_aspect(raw: str) -> str:
    """把用户填的画幅规整成 ASPECT_MAP 的键；不认识就回退默认。"""
    s = (raw or "").strip().replace("：", ":").replace("x", ":").replace("X", ":")
    return s if s in ASPECT_MAP else DEFAULT_ASPECT


def aspect_spec(aspect: str) -> dict:
    return ASPECT_MAP[normalize_aspect(aspect)]


def image_size(path: Path) -> tuple[int, int]:
    """读图片像素尺寸 (w, h)。失败抛 RuntimeError。"""
    from PIL import Image
    try:
        with Image.open(path) as im:
            return im.size
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"读取图片尺寸失败：{path}（{exc}）") from exc


def run_ff(cmd: list, cwd=None, timeout: int = 1800) -> tuple[bool, str]:
    """跑 ffmpeg/ffprobe，返回 (ok, stderr尾部)。不抛异常。"""
    try:
        r = subprocess.run(cmd, capture_output=True, cwd=cwd, timeout=timeout)
    except (OSError, subprocess.SubprocessError) as exc:
        return False, str(exc)
    if r.returncode != 0:
        return False, r.stderr.decode("utf-8", "replace")[-500:]
    return True, ""


def video_duration_seconds(path: Path) -> float:
    """ffprobe 取时长（秒）。失败返回 0.0。"""
    cmd = [ffprobe_bin(), "-v", "error", "-show_entries", "format=duration",
           "-of", "default=noprint_wrappers=1:nokey=1", str(path)]
    ok, _ = run_ff(cmd, timeout=60)
    if not ok:
        return 0.0
    try:
        out = subprocess.run(cmd, capture_output=True, timeout=60)
        return float(out.stdout.decode().strip())
    except (OSError, subprocess.SubprocessError, ValueError):
        return 0.0


def compose_product_on_background(bg_bytes: bytes, product_path: Path,
                                  canvas: tuple[int, int], margin_ratio: float = 0.12) -> bytes:
    """保真合成：AI 背景铺满画布，产品原图按比例缩放后**原样 paste**（像素不重绘）。

    产品区 = 原始像素，构造上 100% 保真。产品居中，四周留 margin_ratio 边距。
    返回 PNG 字节。
    """
    import io
    from PIL import Image

    cw, ch = canvas
    bg = Image.open(io.BytesIO(bg_bytes)).convert("RGB")
    # 背景先 cover 铺满画布（等比缩放到覆盖，再中心裁剪）
    bg_ratio, canvas_ratio = bg.width / bg.height, cw / ch
    if bg_ratio > canvas_ratio:
        nh = ch
        nw = int(round(ch * bg_ratio))
    else:
        nw = cw
        nh = int(round(cw / bg_ratio))
    bg = bg.resize((nw, nh), Image.LANCZOS)
    left, top = (nw - cw) // 2, (nh - ch) // 2
    canvas_im = bg.crop((left, top, left + cw, top + ch))

    # 产品原图：等比缩放到 (1 - 2*margin) 的可用框内，保持原始细节
    with Image.open(product_path) as _p:
        product = _p.convert("RGBA")
    max_w, max_h = int(cw * (1 - 2 * margin_ratio)), int(ch * (1 - 2 * margin_ratio))
    scale = min(max_w / product.width, max_h / product.height)
    pw, ph = max(1, int(product.width * scale)), max(1, int(product.height * scale))
    product = product.resize((pw, ph), Image.LANCZOS)
    px, py = (cw - pw) // 2, (ch - ph) // 2
    canvas_im.paste(product, (px, py), product)

    buf = io.BytesIO()
    canvas_im.save(buf, format="PNG")
    return buf.getvalue()


def fit_image_to_canvas(src_bytes: bytes, canvas: tuple[int, int]) -> bytes:
    """把生成图 cover 到画布（等比缩放 + 中心裁切），不产生黑边。返回 PNG。"""
    import io
    from PIL import Image
    cw, ch = canvas
    im = Image.open(io.BytesIO(src_bytes)).convert("RGB")
    scale = max(cw / im.width, ch / im.height)
    nw, nh = max(1, int(im.width * scale)), max(1, int(im.height * scale))
    im = im.resize((nw, nh), Image.LANCZOS)
    left, top = (nw - cw) // 2, (nh - ch) // 2
    canvas_im = im.crop((left, top, left + cw, top + ch))
    buf = io.BytesIO()
    canvas_im.save(buf, format="PNG")
    return buf.getvalue()


def still_to_mp4(png_path: Path, out_path: Path, seconds: float, canvas: tuple[int, int]) -> bool:
    """静态展示镜：一张 PNG → 定格 mp4（30fps/h264/无音轨），铺满画布。"""
    cw, ch = canvas
    scale = (f"scale={cw}:{ch}:force_original_aspect_ratio=decrease,"
             f"pad={cw}:{ch}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30")
    cmd = [ffmpeg_bin(), "-y", "-loop", "1", "-i", str(png_path), "-t", f"{seconds:.3f}",
           "-vf", scale, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-an", str(out_path)]
    ok, _ = run_ff(cmd)
    return ok and out_path.is_file()


def ken_burns_to_mp4(png_path: Path, out_path: Path, seconds: float,
                     canvas: tuple[int, int], zoom: float = 1.12) -> bool:
    """Ken Burns 展示镜：一张 PNG → 缓慢推近的 mp4（产品不重绘，只是镜头运动）。"""
    cw, ch = canvas
    fps = 30
    frames = max(1, int(round(seconds * fps)))
    # 先放大到画布 * 2 供 zoompan 采样，避免抖动；zoom 从 1 缓慢到 zoom。
    zp = (f"scale={cw*2}:{ch*2}:force_original_aspect_ratio=increase,"
          f"crop={cw*2}:{ch*2},"
          f"zoompan=z='min(zoom+{(zoom-1)/frames:.6f},{zoom})':"
          f"d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
          f"s={cw}x{ch}:fps={fps},setsar=1")
    cmd = [ffmpeg_bin(), "-y", "-loop", "1", "-i", str(png_path), "-t", f"{seconds:.3f}",
           "-vf", zp, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-an", str(out_path)]
    ok, msg = run_ff(cmd)
    if ok and out_path.is_file():
        return True
    # zoompan 在某些 ffmpeg 构建上挑剔 → 回退成静态定格，保证不阻断流程
    return still_to_mp4(png_path, out_path, seconds, canvas)
