#!/usr/bin/env python3
"""Seedance 2.0 i2v/t2v 视频生成 · 生产工具(能力封装版).

从散落的 pipeline 脚本抽出的可移植能力单元:不绑任何项目路径,
图片相对路径由 --asset-root 决定,凭证走 env(或 --env 指向的 .env),
后置 QA 由 --qa-script 可选注入(不给则跳过)。

功能(与原实现一致):
  - yaml storyboard 批量输入 + 单命令快调(--prompt one-off)
  - 重试(429/503/408 指数退避,可分类的硬/软错误)
  - 并发 worker 限制(默认 2)
  - sync/async 双兼容响应 + 轮询探测多候选 endpoint
  - 每段写 .status.json 恢复文件,--resume 跳过已完成 slug
  - 后置 QA:--qa-script 指向的脚本(如自带的媒体体检),不阻断只报告

用法:
  # 单段快调(i2v)
  python3 gen_video.py --prompt "..." --first-frame ./frames/S01.png --duration 5 --out ./out/S01.mp4

  # 单段(t2v,无首帧)
  python3 gen_video.py --prompt "..." --duration 5 --out ./out/S01.mp4

  # yaml 批量(图片相对 --asset-root,默认 yaml 所在目录)
  python3 gen_video.py --config storyboard.yaml --out-dir ./out --asset-root ./frames

  # 恢复
  python3 gen_video.py --config storyboard.yaml --out-dir ./out --resume

yaml 格式:
  workers: 2
  aspect_ratio: 9:16
  resolution: 720p
  scenes:
    - slug: S01_kitchen
      prompt: |
        <motion prompt>
      duration: 5
      first_frame: S01.png          # 相对 --asset-root · 省略走 t2v
      ref_frames:
        - S01_ref.png
      negatives: |
        NO face morphing, NO body stretching, NO neon purple/cyan.

依赖:requests · pyyaml(必需);python-dotenv(可选,缺失时自带 .env 解析)。
env:SEEDANCE_API_KEY / SEEDANCE_BASE_URL(必需)· SEEDANCE_MODEL(默认 doubao-seedance-2-0)· SEEDANCE_WORKERS(默认 2)。
许可:自有代码,随引擎分发(MIT)。
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
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests
import yaml

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    load_dotenv = None

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
log = logging.getLogger("cap.video.i2v")


def _load_env(env_path: Path | None) -> None:
    """加载 .env(若存在)· dotenv 缺失时用自带解析,不覆盖已存在的环境变量。"""
    if env_path is None or not env_path.exists():
        return
    if load_dotenv:
        load_dotenv(env_path)
        return
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


# ============================================================================
# Config & DTO
# ============================================================================


@dataclass(frozen=True)
class SeedanceConfig:
    base_url: str
    api_key: str
    model: str
    workers: int = 2

    @classmethod
    def from_env(
        cls, env_path: Path | None = None, workers_override: int | None = None
    ) -> "SeedanceConfig":
        _load_env(env_path)
        try:
            base_url = os.environ["SEEDANCE_BASE_URL"]
            api_key = os.environ["SEEDANCE_API_KEY"]
        except KeyError as exc:
            raise SystemExit(
                f"缺 env: {exc}. 需要 SEEDANCE_API_KEY / SEEDANCE_BASE_URL "
                "(可选 SEEDANCE_MODEL / SEEDANCE_WORKERS)"
            ) from exc
        model = os.environ.get("SEEDANCE_MODEL", "doubao-seedance-2-0")
        w = workers_override or int(os.environ.get("SEEDANCE_WORKERS", "2"))
        return cls(base_url=base_url, api_key=api_key, model=model, workers=w)


@dataclass(frozen=True)
class VideoScene:
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
    error_class: str | None = None
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
                scene.slug, attempt, max_retries, cfg.model, scene.duration,
                len(json.dumps(payload)) // 1024,
            )
            resp = requests.post(url, headers=headers, json=payload, timeout=120)
            if resp.status_code == 200:
                return resp.json()

            err_class = classify_error(resp.status_code, resp.text)
            log.warning(
                "[%s] HTTP %d (%s) · body_head: %s",
                scene.slug, resp.status_code, err_class, resp.text[:300],
            )
            if err_class in ("auth", "url", "payload", "content-policy"):
                raise RuntimeError(
                    f"[{scene.slug}] HTTP {resp.status_code} ({err_class}): {resp.text[:300]}"
                )
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

    raise RuntimeError(f"[{scene.slug}] submit 失败 {max_retries} 次 · 最后: {last_exc}")


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


def poll_task(cfg: SeedanceConfig, task_id: str, max_wait: int = 600) -> str | None:
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
            log.info("轮询 %ds · status=%s", int(time.time() - start), data.get("status", "?"))
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
# QA hook (可选注入)
# ============================================================================


def run_post_qa(video_path: Path, qa_script: Path | None) -> dict[str, Any]:
    """跑 --qa-script 指定的媒体体检脚本(若给);不阻断,只报告。"""
    if qa_script is None:
        return {"skipped": True}
    if not qa_script.exists():
        log.info("[QA] qa-script 未找到,跳过: %s", qa_script)
        return {"skipped": True}
    try:
        result = subprocess.run(
            ["python3", str(qa_script), str(video_path)],
            capture_output=True, text=True, timeout=60, check=False,
        )
        ok = result.returncode == 0
        log.info("[QA] %s → %s (rc=%d)", qa_script.name, "PASS" if ok else "FAIL", result.returncode)
        if not ok:
            log.warning("[QA] stderr: %s", result.stderr[:500])
        return {"ok": ok, "returncode": result.returncode, "stdout_head": result.stdout[:300]}
    except subprocess.TimeoutExpired:
        log.warning("[QA] qa-script 超时")
        return {"ok": False, "error": "timeout"}


# ============================================================================
# Scene execution
# ============================================================================


def run_scene(
    cfg: SeedanceConfig, scene: VideoScene, out_dir: Path, qa_script: Path | None = None
) -> SceneResult:
    start = time.time()
    out_path = out_dir / f"{scene.slug}.mp4"
    log.info("========= [%s] START =========", scene.slug)
    try:
        resp = submit_with_retry(cfg, scene)
    except (RuntimeError, FileNotFoundError) as exc:
        return SceneResult(scene.slug, False, error=str(exc),
                           error_class="submit-failed", elapsed_s=time.time() - start)

    video_url = extract_video_url(resp)
    task_id: str | None = None
    if video_url is None:
        task_id = extract_task_id(resp)
        if task_id is None:
            return SceneResult(scene.slug, False, error=f"响应无 video URL 也无 task_id: {resp}",
                               error_class="protocol", elapsed_s=time.time() - start)
        log.info("[%s] 异步任务 id=%s · 开始轮询", scene.slug, task_id)
        video_url = poll_task(cfg, task_id)
        if video_url is None:
            return SceneResult(scene.slug, False, error="轮询未拿到 video URL",
                               error_class="poll-timeout", elapsed_s=time.time() - start, task_id=task_id)

    if not download_video(video_url, out_path):
        return SceneResult(scene.slug, False, error="下载失败",
                           error_class="download", elapsed_s=time.time() - start, task_id=task_id)

    qa = run_post_qa(out_path, qa_script)
    elapsed = time.time() - start
    log.info("========= [%s] DONE %.1fs · QA=%s =========", scene.slug, elapsed, qa.get("ok", "skipped"))
    return SceneResult(scene.slug, True, video_path=out_path, elapsed_s=elapsed, task_id=task_id)


# ============================================================================
# YAML / status
# ============================================================================


def load_scenes_from_yaml(path: Path, asset_root: Path) -> tuple[list[VideoScene], dict[str, Any]]:
    """返回 (scenes, defaults)。图片相对 asset_root 解析。"""
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    defaults = {
        "workers": data.get("workers"),
        "aspect_ratio": data.get("aspect_ratio", "9:16"),
        "resolution": data.get("resolution", "720p"),
    }
    scenes: list[VideoScene] = []
    for item in data.get("scenes", []):
        first_frame = item.get("first_frame")
        first_frame_path = (asset_root / first_frame).resolve() if first_frame else None
        ref_frames = tuple(
            (asset_root / r).resolve() for r in item.get("ref_frames", []) or []
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
    qa_script: Path | None = None,
) -> list[SceneResult]:
    out_dir.mkdir(parents=True, exist_ok=True)
    status = load_status(out_dir) if resume else {}
    completed_slugs = {slug for slug, meta in status.items() if meta.get("ok")}

    todo = [s for s in scenes if s.slug not in completed_slugs]
    if len(todo) < len(scenes):
        log.info("resume: 跳过已完成 %d 个 (%s)", len(scenes) - len(todo), sorted(completed_slugs))
    if not todo:
        log.info("所有 scene 已完成,退出")
        return []

    log.info("batch: %d 段 · workers=%d · out=%s", len(todo), cfg.workers, out_dir)

    results: list[SceneResult] = []
    with ThreadPoolExecutor(max_workers=cfg.workers) as ex:
        futures = {ex.submit(run_scene, cfg, s, out_dir, qa_script): s for s in todo}
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
    p = argparse.ArgumentParser(description="Seedance 2.0 i2v/t2v · 生产工具(能力封装版)")
    p.add_argument("--config", type=Path, help="yaml storyboard 批量模式")
    p.add_argument("--out-dir", type=Path, help="批量输出目录(与 --config 配对)")
    p.add_argument("--asset-root", type=Path, help="图片相对路径根(默认 yaml 所在目录)")
    p.add_argument("--resume", action="store_true", help="跳过 .status.json 里已完成的 slug")
    p.add_argument("--only", help="批量模式下只跑指定 slug(逗号分隔)")
    p.add_argument("--workers", type=int, help="并发数覆盖(默认 SEEDANCE_WORKERS 或 2)")
    p.add_argument("--env", type=Path, help="可选 .env 文件路径")
    p.add_argument("--qa-script", type=Path, help="可选:成品后置 QA 脚本(接收 mp4 路径,rc=0 为 PASS)")

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
        cfg = SeedanceConfig.from_env(env_path=args.env, workers_override=args.workers)
        asset_root = (args.asset_root or args.config.resolve().parent).resolve()
        scenes, _defaults = load_scenes_from_yaml(args.config, asset_root)
        if args.only:
            wanted = set(args.only.split(","))
            scenes = [s for s in scenes if s.slug in wanted]
            if not scenes:
                log.error("--only 未匹配任何 slug")
                return 3
        results = run_batch(cfg, scenes, args.out_dir, resume=args.resume, qa_script=args.qa_script)
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
        cfg = SeedanceConfig.from_env(env_path=args.env, workers_override=args.workers)
        scene = VideoScene(
            slug=args.out.stem,
            prompt=args.prompt,
            duration=args.duration,
            first_frame=args.first_frame,
            negatives=args.negatives,
        )
        result = run_scene(cfg, scene, args.out.parent, qa_script=args.qa_script)
        if result.ok and result.video_path:
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
