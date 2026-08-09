"""共享媒体/配置助手（ad-agent 版）— tools.py 六步工具都用它。

职责单一：环境与 provider 配置、图片尺寸/校验、画幅映射、sha256 摘要、
产品原图确定性合成到 AI 背景（PIL）、静态/Ken Burns 转 mp4（ffmpeg）、结构化错误。
不做业务判断、不碰状态机。

所有 provider 类来自 src/mvstudio/*（只读复用，不改引擎）。
保真铁律：产品素材不送生成模型重绘；合成只做可复现的缩放和 alpha paste，
用 source_digest / composite_digest 记录来源与结果，不能宣称编码后字节不变。
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

# ── 让 mv_platform / mvstudio 可 import（项目根 = ad-agent 的上两级）
_REPO_ROOT = Path(__file__).resolve().parents[2]
for _p in (str(_REPO_ROOT), str(_REPO_ROOT / "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ── 加载项目根 .env（统一 KEY 源，不再用 ad-agent/.env）
try:
    from dotenv import load_dotenv
    load_dotenv(_REPO_ROOT / ".env", override=False)
except ImportError:
    pass

from mvstudio.media import (
    err,
    ffmpeg_bin,
    ffprobe_bin,
    max_shots as _max_shots,
    provider_config,
    sha256_bytes,
    sha256_file,
)


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
POSE_REFERENCE_MIN_COVERAGE = 0.65


def max_shots() -> Optional[int]:
    return _max_shots("AD_MAX_SHOTS")


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
    """受控合成：AI 背景铺满画布，产品素材只做确定性缩放和 alpha paste。

    原始文件只读、不进入生成模型；缩放与 PNG 编码会改变字节，因此调用方应分别记录
    source_digest 和 composite_digest，而不是宣称产品区等于原文件字节。
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


def pose_reference_from_video(source: Path, out_path: Path, *,
                             model: Optional[Path] = None,
                             label: bool = True) -> dict:
    """把任意人物视频转成「无外貌信息」的动作骨架视频（复用 mvstudio.media 公共库）。

    只保留 MediaPipe 姿态骨架的运动/时序，丢弃长相与身份——可作为 i2v 的
    编舞/节奏参考而不带脸。重活（cv2/mediapipe）在公共库里惰性导入，缺依赖时
    抛结构化错误、不阻断其他步骤。

    返回 {"output","frames","detected","coverage","fps"}；失败保留公共库的
    PoseReferenceError 类型，调用方据此转成 ToolResult，不靠解析普通异常猜原因。
    """
    from mvstudio.media import generate_pose_reference  # 惰性导入：无 CV 依赖时不拖累其他步骤
    result = generate_pose_reference(
        source,
        out_path,
        model=model,
        min_coverage=POSE_REFERENCE_MIN_COVERAGE,
        label=label,
    )
    return {
        "output": str(result.output),
        "frames": result.frames,
        "detected": result.detected,
        "coverage": round(result.coverage, 4),
        "fps": result.fps,
    }
