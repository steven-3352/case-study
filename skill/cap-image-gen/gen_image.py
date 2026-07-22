#!/usr/bin/env python3
"""通用出图能力 · GPT-image-2(能力封装版).

两种模式:
  1. 文生图(t2i):只给 prompt → images.generate
  2. 参考图驱动(edit):prompt + 参考图 → images.edit
     用途:角色一致性——先出一张角色设定图(character sheet),
     后续每镜以它为 ref 改姿态/场景,而不是每镜独立盲生成。

单张 + yaml 批量双模;重试(4 次 · 5s 退避)+ 并发 + 已存在跳过。

这是从零新写的参数化封装(原项目 p002 等脚本把 prompt/文案内联写死,
无通用入口;本脚本以 gen_d07_bg.py 直连 + gen_scene_frames.py 的 edit 形态为骨架)。

用法:
  # 文生图单张
  python3 gen_image.py --prompt "..." --out out.png --env ./.env

  # 参考图驱动单张(角色一致性)
  python3 gen_image.py --prompt "same character, now sitting at a desk" \
      --ref char_sheet.png --out S01.png

  # yaml 批量
  python3 gen_image.py --config scenes.yaml --out-dir ./imgs --asset-root ./refs

依赖:openai(SDK)· pyyaml(仅批量)。
env:GPT_IMAGE_API_KEY / GPT_IMAGE_BASE_URL(必需,回落 OPENAI_*)· GPT_IMAGE_MODEL(默认 gpt-image-2)· GPT_IMAGE_WORKERS(默认 2)。
许可:自有代码,随引擎分发(MIT)。
"""
from __future__ import annotations

import argparse
import base64
import logging
import os
import pathlib
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("cap.image")

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore


def load_env_file(path: pathlib.Path | None) -> None:
    """加载 .env(若给且存在)· dotenv 缺失时自带解析,不覆盖已存在环境变量。"""
    if path is None or not path.exists():
        return
    try:
        from dotenv import load_dotenv
        load_dotenv(path)
        return
    except ModuleNotFoundError:
        pass
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


@dataclass(frozen=True)
class ImageJob:
    slug: str
    prompt: str
    refs: tuple[pathlib.Path, ...] = field(default_factory=tuple)


def _write_result(first, out: pathlib.Path) -> bool:
    """把 API 返回的第一张图落盘(b64_json 或 url)。"""
    b64 = getattr(first, "b64_json", None)
    if b64:
        out.write_bytes(base64.b64decode(b64))
        return True
    url = getattr(first, "url", None)
    if url:
        import urllib.request
        with urllib.request.urlopen(url) as r:  # noqa: S310
            out.write_bytes(r.read())
        return True
    return False


def generate_one(client, model: str, job: ImageJob, out_dir: pathlib.Path,
                 size: str, max_retries: int = 4) -> pathlib.Path | None:
    out = out_dir / f"{job.slug}.png"
    if out.exists():
        log.info("skip 已存在: %s", out.name)
        return out

    mode = "edit(参考图驱动)" if job.refs else "t2i(文生图)"
    log.info("生图 [%s]: %s → %s (refs=%d)", mode, job.slug, out.name, len(job.refs))

    for attempt in range(1, max_retries + 1):
        handles = [p.open("rb") for p in job.refs if p.exists()]
        try:
            if handles:
                image_arg = handles if len(handles) > 1 else handles[0]
                resp = client.images.edit(
                    model=model, image=image_arg, prompt=job.prompt, size=size, n=1,
                )
            else:
                resp = client.images.generate(
                    model=model, prompt=job.prompt, size=size, n=1,
                )
        except Exception as exc:  # noqa: BLE001 — 重试
            log.warning("尝试 %d/%d 失败 %s: %s", attempt, max_retries, job.slug, exc)
            for h in handles:
                h.close()
            if attempt < max_retries:
                time.sleep(5)
                continue
            log.error("放弃 %s(%d 次全败)", job.slug, max_retries)
            return None
        finally:
            for h in handles:
                if not h.closed:
                    h.close()

        if not resp.data:
            log.error("返回 data 为空: %s", job.slug)
            return None
        out.parent.mkdir(parents=True, exist_ok=True)
        if not _write_result(resp.data[0], out):
            log.error("无 b64_json 也无 url: %s", job.slug)
            return None
        log.info("✓ %s (%s bytes)", out, out.stat().st_size)
        return out
    return None


def load_jobs_from_yaml(path: pathlib.Path, asset_root: pathlib.Path) -> tuple[list[ImageJob], dict]:
    if yaml is None:
        sys.exit("批量模式需要 PyYAML: pip install pyyaml")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    defaults = {"size": data.get("size", "1024x1536"), "model": data.get("model")}
    jobs: list[ImageJob] = []
    for item in data.get("scenes", []):
        refs = tuple((asset_root / r).resolve() for r in item.get("refs", []) or [])
        jobs.append(ImageJob(slug=item["slug"], prompt=item["prompt"], refs=refs))
    return jobs, defaults


def _make_client(base_url: str, api_key: str):
    try:
        from openai import OpenAI
    except ModuleNotFoundError:
        sys.exit("需要 openai SDK: pip install openai")
    return OpenAI(api_key=api_key, base_url=base_url)


def main() -> int:
    ap = argparse.ArgumentParser(description="通用出图 · GPT-image-2(t2i + 参考图驱动)")
    ap.add_argument("--prompt", help="单张模式:出图 prompt")
    ap.add_argument("--ref", nargs="*", type=pathlib.Path, default=[],
                    help="单张模式:参考图(给了走 edit 模式,角色一致性)")
    ap.add_argument("--out", type=pathlib.Path, help="单张模式:输出 png 路径")
    ap.add_argument("--config", type=pathlib.Path, help="批量模式:yaml")
    ap.add_argument("--out-dir", type=pathlib.Path, help="批量模式:输出目录")
    ap.add_argument("--asset-root", type=pathlib.Path, help="批量:参考图相对根(默认 yaml 所在目录)")
    ap.add_argument("--size", default="1024x1536", help="出图尺寸(默认 1024x1536)")
    ap.add_argument("--model", help="覆盖 GPT_IMAGE_MODEL")
    ap.add_argument("--workers", type=int, help="并发(默认 GPT_IMAGE_WORKERS 或 2)")
    ap.add_argument("--env", type=pathlib.Path, help="可选 .env 路径")
    args = ap.parse_args()

    load_env_file(args.env)
    api_key = os.environ.get("GPT_IMAGE_API_KEY") or os.environ.get("OPENAI_API_KEY")
    base_url = os.environ.get("GPT_IMAGE_BASE_URL") or os.environ.get("OPENAI_BASE_URL")
    if not api_key or not base_url:
        log.error("缺 GPT_IMAGE_API_KEY 或 GPT_IMAGE_BASE_URL(环境变量或 --env)")
        return 1
    model = args.model or os.environ.get("GPT_IMAGE_MODEL", "gpt-image-2")
    workers = args.workers or int(os.environ.get("GPT_IMAGE_WORKERS", "2"))
    client = _make_client(base_url, api_key)

    if args.config:
        if not args.out_dir:
            log.error("--config 需要配对 --out-dir")
            return 2
        asset_root = (args.asset_root or args.config.resolve().parent).resolve()
        jobs, defaults = load_jobs_from_yaml(args.config, asset_root)
        size = defaults["size"] or args.size
        model = defaults["model"] or model
        args.out_dir.mkdir(parents=True, exist_ok=True)
        log.info("批量 %d 张 · model=%s · size=%s · workers=%d", len(jobs), model, size, workers)
        done = 0
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(generate_one, client, model, j, args.out_dir, size): j for j in jobs}
            for fut in as_completed(futures):
                if fut.result():
                    done += 1
        log.info("完成 %d/%d 张", done, len(jobs))
        return 0 if done == len(jobs) else 4

    if args.prompt:
        if not args.out:
            log.error("单张模式需要 --out")
            return 2
        job = ImageJob(slug=args.out.stem, prompt=args.prompt, refs=tuple(args.ref or ()))
        result = generate_one(client, model, job, args.out.parent, args.size)
        if result and result != args.out:
            result.rename(args.out)
        return 0 if result else 1

    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
