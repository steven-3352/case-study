#!/usr/bin/env python3
"""P011 · Seedance 2.0 i2v/t2v 生产工具.

参考 `pipeline/gen_video_frames.py`(grok golden reference)的完备度,做到:
  - yaml storyboard 批量输入(不用每条选题拷 py 脚本)
  - 单命令快调(--prompt one-off)
  - 重试(429/503/408 指数退避,可分类的错误)
  - 并发 worker 限制(默认 2 · 沿用 GPT_IMAGE_WORKERS 教训 · memory `feedback_gpt-image-model-fallback`)
  - sync/async 双兼容响应(与 grok 同)
  - 每段生成写 .status.json 恢复文件,已完成 slug 自动跳过
  - 后置 QA:调 `gate_check_media.py` 判定 (若存在)

**用法:**

  # 单段快调
  python3 pipeline/p011_seedance_i2v/gen_video.py \
      --prompt "..." --first-frame path/to.png --duration 5 --out out.mp4

  # yaml 批量
  python3 pipeline/p011_seedance_i2v/gen_video.py \
      --config storyboard.yaml --out-dir tmp/xxx/videos

  # 恢复(跳过 .status.json 里已完成的 slug)
  python3 pipeline/p011_seedance_i2v/gen_video.py \
      --config storyboard.yaml --out-dir tmp/xxx/videos --resume

**yaml 格式:**

  workers: 2        # 可选,默认 SEEDANCE_WORKERS 或 2
  aspect_ratio: 9:16
  resolution: 720p
  scenes:
    - slug: S01_kitchen
      prompt: |
        <motion prompt · 走 .agents/skills/i2v-video-prompt/ 骨架>
      duration: 5
      first_frame: tmp/short/frames/S01.png    # 相对 project root · 可省略走 t2v
      ref_frames:                              # 可选
        - tmp/short/frames/S01_ref.png
      negatives: |
        NO face morphing, NO body stretching, NO breath puff, NO neon purple/cyan.

参考:
  - .agents/skills/i2v-video-prompt/SKILL.md    prompt 工程主门
  - .agents/skills/video-form-*/                15 个形态专属子 skill
  - pipeline/gen_video_frames.py                grok 集成参考实现
  - README.md                                    P011 定位与完善路线
"""
from __future__ import annotations

import argparse
import base64
import json
import logging
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import requests
import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
log = logging.getLogger("p011.seedance")


# ============================================================================
# Config & DTO
# ============================================================================


@dataclass(frozen=True)
class SeedanceConfig:
    """Seedance API 凭证 + 中转 URL · 从 .env 读."""

    base_url: str
    api_key: str
    model: str
    workers: int = 2

    @classmethod
    def from_env(cls, workers_override: int | None = None) -> "SeedanceConfig":
        load_dotenv(ROOT / ".env")
        try:
            base_url = os.environ["SEEDANCE_BASE_URL"]
            api_key = os.environ["SEEDANCE_API_KEY"]
        except KeyError as exc:
            raise SystemExit(
                f"缺 env: {exc}. 参考 .env.example 补 SEEDANCE_API_KEY / "
                "SEEDANCE_BASE_URL / SEEDANCE_MODEL"
            ) from exc
        model = os.environ.get("SEEDANCE_MODEL", "doubao-seedance-2-0")
        w = workers_override or int(os.environ.get("SEEDANCE_WORKERS", "2"))
        return cls(base_url=base_url, api_key=api_key, model=model, workers=w)


@dataclass(frozen=True)
class VideoScene:
    """单段视频任务 · 支持 i2v(有 first_frame) 或 t2v(无)."""

    slug: str
    prompt: str
    duration: int
    first_frame: Path | None = None
    ref_frames: tuple[Path, ...] = ()
    aspect_ratio: str = "9:16"
    resolution: str = "720p"
    negatives: str | None = None

    @property
    def full_prompt(self) -> str:
        if self.negatives:
            return f"{self.prompt}\n\nIMPORTANT NEGATIVES: {self.negatives}"
        return self.prompt


@dataclass
class SceneResult:
    slug: str
    ok: bool
    video_path: Path | None = None
    error: str | None = None
    error_class: str | None = None  # auth / url / timeout / content-policy / unknown
    elapsed_s: float = 0.0
    task_id: str | None = None


# ============================================================================
# Encoding / requests
# ============================================================================


def png_to_data_url(path: Path) -> str:
    raw = path.read_bytes()
    b64 = base64.b64encode(raw).decode("ascii")
    return f"data:image/png;base64,{b64}"


def classify_error(status: int | None, body: str) -> str:
    """把 HTTP 错误映射到人可读类别."""
    if status is None:
        return "network"
    if status in (401, 403):
        return "auth"
    if status == 404:
        return "url"
    if status == 422:
        return "payload"
    if status == 429:
        return "rate-limit"
    if status in (408, 504):
        return "timeout"
    if status == 400 and any(k in body.lower() for k in ("policy", "content", "safety")):
        return "content-policy"
    if status is not None and 500 <= status < 600:
        return "server"
    return "unknown"


def submit_with_retry(
    cfg: SeedanceConfig,
    scene: VideoScene,
    max_retries: int = 3,
    base_delay: float = 5.0,
) -> dict[str, Any]:
    """POST /v1/videos/generations 带重试;429/503/timeout 指数退避;auth/url 不重试."""
    url = cfg.base_url.rstrip("/") + "/v1/videos/generations"
    payload: dict[str, Any] = {
        "model": cfg.model,
        "prompt": scene.full_prompt,
        "resolution": scene.resolution,
        "aspect_ratio": scene.aspect_ratio,
        "duration": scene.duration,
    }
    if scene.first_frame is not None:
        if not scene.first_frame.exists():
            raise FileNotFoundError(f"首帧图缺失: {scene.first_frame}")
        payload["image"] = {"url": png_to_data_url(scene.first_frame)}
    if scene.ref_frames:
        payload["reference_images"] = [
            {"url": png_to_data_url(p)} for p in scene.ref_frames if p.exists()
        ]

    headers = {
        "Authorization": f"Bearer {cfg.api_key}",
        "Content-Type": "application/json",
    }

    last_exc: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            log.info(
                "[%s] submit attempt %d/%d · model=%s · dur=%ds · payload≈%dKB",
                scene.slug,
                attempt,
                max_retries,
                cfg.model,
                scene.duration,
                len(json.dumps(payload)) // 1024,
            )
            resp = requests.post(url, headers=headers, json=payload, timeout=120)
            if resp.status_code == 200:
                return resp.json()

            err_class = classify_error(resp.status_code, resp.text)
            log.warning(
                "[%s] HTTP %d (%s) · body_head: %s",
                scene.slug,
                resp.status_code,
                err_class,
                resp.text[:300],
            )
            if err_class in ("auth", "url", "payload", "content-policy"):
                # 硬错误不重试
                raise RuntimeError(
                    f"[{scene.slug}] HTTP {resp.status_code} ({err_class}): "
                    f"{resp.text[:300]}"
                )
            # 软错误退避重试
            if attempt < max_retries:
                delay = base_delay * (2 ** (attempt - 1))
                log.info("[%s] %ss 后重试...", scene.slug, delay)
                time.sleep(delay)
        except requests.RequestException as exc:
            last_exc = exc
            log.warning("[%s] 网络异常: %s", scene.slug, exc)
            if attempt < max_retries:
                delay = base_delay * (2 ** (attempt - 1))
                time.sleep(delay)

    raise RuntimeError(
        f"[{scene.slug}] submit 失败 {max_retries} 次 · 最后: {last_exc}"
    )


def extract_video_url(resp: dict[str, Any]) -> str | None:
    if isinstance(resp.get("video"), dict):
        v = resp["video"].get("url")
        if isinstance(v, str):
            return v
    for key in ("video_url", "url", "output_url", "result_url"):
        if isinstance(resp.get(key), str):
            return resp[key]
    if isinstance(resp.get("data"), list) and resp["data"]:
        item = resp["data"][0]
        for key in ("url", "video_url", "output_url"):
            if isinstance(item.get(key), str):
                return item[key]
    if isinstance(resp.get("output"), dict):
        for key in ("url", "video_url"):
            v = resp["output"].get(key)
            if isinstance(v, str):
                return v
    return None


def extract_task_id(resp: dict[str, Any]) -> str | None:
    for key in ("task_id", "job_id", "id", "request_id"):
        v = resp.get(key)
        if isinstance(v, str):
            return v
    return None


def poll_task(
    cfg: SeedanceConfig, task_id: str, max_wait: int = 600
) -> str | None:
    candidates = [
        cfg.base_url.rstrip("/") + f"/v1/videos/generations/{task_id}",
        cfg.base_url.rstrip("/") + f"/v1/videos/{task_id}",
        cfg.base_url.rstrip("/") + f"/v1/tasks/{task_id}",
    ]
    headers = {"Authorization": f"Bearer {cfg.api_key}"}
    poll_url: str | None = None
    for cand in candidates:
        try:
            r = requests.get(cand, headers=headers, timeout=15)
            if r.status_code == 200:
                poll_url = cand
                log.info("轮询 endpoint 命中: %s", cand)
                break
        except requests.RequestException as exc:
            log.debug("探测 %s 失败: %s", cand, exc)

    if poll_url is None:
        log.warning("找不到有效 poll endpoint · 候选: %s", candidates)
        return None

    start = time.time()
    delay = 5
    while time.time() - start < max_wait:
        try:
            r = requests.get(poll_url, headers=headers, timeout=15)
            if r.status_code != 200:
                log.warning("轮询 HTTP %d: %s", r.status_code, r.text[:200])
                time.sleep(delay)
                continue
            data = r.json()
            log.info(
                "轮询 %ds · status=%s",
                int(time.time() - start),
                data.get("status", "?"),
            )
            v_url = extract_video_url(data)
            if v_url:
                return v_url
            if str(data.get("status", "")).lower() in {"failed", "error"}:
                log.error("任务失败: %s", data)
                return None
            time.sleep(delay)
            delay = min(delay + 2, 15)
        except requests.RequestException as exc:
            log.warning("轮询异常: %s", exc)
            time.sleep(delay)

    log.error("轮询超时 %ds", max_wait)
    return None


def download_video(url: str, out: Path, max_retries: int = 3) -> bool:
    for attempt in range(1, max_retries + 1):
        try:
            log.info("下载 %s → %s (attempt %d)", url[:80], out.name, attempt)
            out.parent.mkdir(parents=True, exist_ok=True)
            with requests.get(url, stream=True, timeout=180) as r:
                r.raise_for_status()
                with out.open("wb") as f:
                    for chunk in r.iter_content(chunk_size=1 << 20):
                        if chunk:
                            f.write(chunk)
            size_kb = out.stat().st_size // 1024
            log.info("✓ 下载完成: %s (%d KB)", out, size_kb)
            return True
        except (requests.RequestException, OSError) as exc:
            log.warning("下载失败: %s", exc)
            if attempt < max_retries:
                time.sleep(5 * attempt)
    return False


# ============================================================================
# QA hook
# ============================================================================


def run_post_qa(video_path: Path) -> dict[str, Any]:
    """跑 gate_check_media.py(若存在)对成品做机器 QC · 不阻断,只报告."""
    gate = ROOT / "pipeline" / "gate_check_media.py"
    if not gate.exists():
        log.info("[QA] gate_check_media.py 未找到,跳过后置 QC")
        return {"skipped": True}
    try:
        result = subprocess.run(
            ["python3", str(gate), str(video_path)],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        ok = result.returncode == 0
        log.info(
            "[QA] gate_check_media → %s (rc=%d)",
            "PASS" if ok else "FAIL",
            result.returncode,
        )
        if not ok:
            log.warning("[QA] stderr: %s", result.stderr[:500])
        return {
            "ok": ok,
            "returncode": result.returncode,
            "stdout_head": result.stdout[:300],
        }
    except subprocess.TimeoutExpired:
        log.warning("[QA] gate_check 超时")
        return {"ok": False, "error": "timeout"}


# ============================================================================
# Scene execution
# ============================================================================


def run_scene(cfg: SeedanceConfig, scene: VideoScene, out_dir: Path) -> SceneResult:
    start = time.time()
    out_path = out_dir / f"{scene.slug}.mp4"
    log.info("========= [%s] START =========", scene.slug)
    try:
        resp = submit_with_retry(cfg, scene)
    except (RuntimeError, FileNotFoundError) as exc:
        return SceneResult(
            slug=scene.slug,
            ok=False,
            error=str(exc),
            error_class="submit-failed",
            elapsed_s=time.time() - start,
        )

    video_url = extract_video_url(resp)
    task_id: str | None = None
    if video_url is None:
        task_id = extract_task_id(resp)
        if task_id is None:
            return SceneResult(
                slug=scene.slug,
                ok=False,
                error=f"响应无 video URL 也无 task_id: {resp}",
                error_class="protocol",
                elapsed_s=time.time() - start,
            )
        log.info("[%s] 异步任务 id=%s · 开始轮询", scene.slug, task_id)
        video_url = poll_task(cfg, task_id)
        if video_url is None:
            return SceneResult(
                slug=scene.slug,
                ok=False,
                error="轮询未拿到 video URL",
                error_class="poll-timeout",
                elapsed_s=time.time() - start,
                task_id=task_id,
            )

    if not download_video(video_url, out_path):
        return SceneResult(
            slug=scene.slug,
            ok=False,
            error="下载失败",
            error_class="download",
            elapsed_s=time.time() - start,
            task_id=task_id,
        )

    # 后置 QA
    qa = run_post_qa(out_path)
    elapsed = time.time() - start
    log.info(
        "========= [%s] DONE %.1fs · QA=%s =========",
        scene.slug,
        elapsed,
        qa.get("ok", "skipped"),
    )
    return SceneResult(
        slug=scene.slug,
        ok=True,
        video_path=out_path,
        elapsed_s=elapsed,
        task_id=task_id,
    )


# ============================================================================
# YAML / status
# ============================================================================


def load_scenes_from_yaml(path: Path) -> tuple[list[VideoScene], dict[str, Any]]:
    """返回 (scenes, defaults 字典 · workers/aspect/resolution 可能覆盖 env)."""
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    defaults = {
        "workers": data.get("workers"),
        "aspect_ratio": data.get("aspect_ratio", "9:16"),
        "resolution": data.get("resolution", "720p"),
    }
    scenes: list[VideoScene] = []
    for item in data.get("scenes", []):
        first_frame = item.get("first_frame")
        first_frame_path = (
            (ROOT / first_frame).resolve() if first_frame else None
        )
        ref_frames = tuple(
            (ROOT / r).resolve() for r in item.get("ref_frames", []) or []
        )
        scenes.append(
            VideoScene(
                slug=item["slug"],
                prompt=item["prompt"],
                duration=int(item["duration"]),
                first_frame=first_frame_path,
                ref_frames=ref_frames,
                aspect_ratio=item.get("aspect_ratio", defaults["aspect_ratio"]),
                resolution=item.get("resolution", defaults["resolution"]),
                negatives=item.get("negatives"),
            )
        )
    return scenes, defaults


def status_path(out_dir: Path) -> Path:
    return out_dir / ".status.json"


def load_status(out_dir: Path) -> dict[str, Any]:
    p = status_path(out_dir)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}


def save_status(out_dir: Path, status: dict[str, Any]) -> None:
    status_path(out_dir).write_text(
        json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8"
    )


# ============================================================================
# Batch runner
# ============================================================================


def run_batch(
    cfg: SeedanceConfig,
    scenes: list[VideoScene],
    out_dir: Path,
    resume: bool = False,
) -> list[SceneResult]:
    out_dir.mkdir(parents=True, exist_ok=True)
    status = load_status(out_dir) if resume else {}
    completed_slugs = {
        slug for slug, meta in status.items() if meta.get("ok")
    }

    todo = [s for s in scenes if s.slug not in completed_slugs]
    if len(todo) < len(scenes):
        log.info(
            "resume: 跳过已完成 %d 个 (%s)",
            len(scenes) - len(todo),
            sorted(completed_slugs),
        )
    if not todo:
        log.info("所有 scene 已完成,退出")
        return []

    log.info(
        "batch: %d 段 · workers=%d · out=%s",
        len(todo),
        cfg.workers,
        out_dir,
    )

    results: list[SceneResult] = []
    with ThreadPoolExecutor(max_workers=cfg.workers) as ex:
        futures = {ex.submit(run_scene, cfg, s, out_dir): s for s in todo}
        for fut in as_completed(futures):
            r = fut.result()
            results.append(r)
            status[r.slug] = {
                "ok": r.ok,
                "video_path": str(r.video_path) if r.video_path else None,
                "error": r.error,
                "error_class": r.error_class,
                "elapsed_s": round(r.elapsed_s, 1),
                "task_id": r.task_id,
            }
            save_status(out_dir, status)
    return results


# ============================================================================
# CLI
# ============================================================================


def _cli() -> int:
    p = argparse.ArgumentParser(
        description="P011 Seedance 2.0 i2v/t2v · 生产工具",
    )
    p.add_argument("--config", type=Path, help="yaml storyboard 批量模式")
    p.add_argument("--out-dir", type=Path, help="批量输出目录(与 --config 配对)")
    p.add_argument("--resume", action="store_true", help="跳过 .status.json 里已完成的 slug")
    p.add_argument("--only", help="批量模式下只跑指定 slug(逗号分隔)")
    p.add_argument("--workers", type=int, help="并发数覆盖(默认 SEEDANCE_WORKERS 或 2)")

    p.add_argument("--prompt", help="单段模式:motion prompt")
    p.add_argument("--first-frame", type=Path, help="单段模式:i2v 首帧图")
    p.add_argument("--duration", type=int, default=5, help="单段模式:秒数")
    p.add_argument("--negatives", help="单段模式:NEGATIVES 段")
    p.add_argument("--out", type=Path, help="单段模式:输出 mp4 路径")

    args = p.parse_args()

    if args.config:
        if not args.out_dir:
            log.error("--config 需要配对 --out-dir")
            return 2
        cfg = SeedanceConfig.from_env(workers_override=args.workers)
        scenes, _defaults = load_scenes_from_yaml(args.config)
        if args.only:
            wanted = set(args.only.split(","))
            scenes = [s for s in scenes if s.slug in wanted]
            if not scenes:
                log.error("--only 未匹配任何 slug")
                return 3
        results = run_batch(cfg, scenes, args.out_dir, resume=args.resume)
        ok = sum(1 for r in results if r.ok)
        log.info("=== 批量完成: %d/%d 成功 ===", ok, len(results))
        for r in results:
            if not r.ok:
                log.error("FAIL [%s] %s: %s", r.slug, r.error_class, r.error)
        return 0 if ok == len(results) else 5

    if args.prompt:
        if not args.out:
            log.error("单段模式需要 --out")
            return 2
        cfg = SeedanceConfig.from_env(workers_override=args.workers)
        scene = VideoScene(
            slug=args.out.stem,
            prompt=args.prompt,
            duration=args.duration,
            first_frame=args.first_frame,
            negatives=args.negatives,
        )
        result = run_scene(cfg, scene, args.out.parent)
        if result.ok and result.video_path:
            # 若 --out 名字与 slug 生成的不同,rename
            if result.video_path != args.out:
                result.video_path.rename(args.out)
                log.info("重命名 → %s", args.out)
            return 0
        log.error("生成失败: %s (%s)", result.error, result.error_class)
        return 1

    p.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(_cli())
