"""内容寻址缓存渲染 —— 冷跑正常，热跑只做 hardlink,秒级完成。

流程:
    1. 父进程遍历所有 (version, i) 帧,算 cache key
    2. 分 hit / miss:hit 直接 hardlink 到 _frames/;miss 塞给 worker pool
    3. Worker 渲染 miss,写到 cache_root/<key[:2]>/<key>.png(原子写)
    4. worker 完成后,父进程再补 hardlink miss 的那些
    5. motion.json 由父进程的 track.predict_track 直出
       —— 不能靠 worker 收集 bbox:命中率 100% 时 worker 一次都不跑

用法:
    python3 -m mv_engine.tools.render_cached --out .cache/mv_engine/hot \
        --cache .cache/mv_engine/framecache
"""
from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "pipeline"))
sys.path.insert(0, str(ROOT / "pipeline" / "voice_room"))

import paperdoll_engine as pe                                 # noqa: E402
import mv_engine.session as _sess                             # noqa: E402
import mingyue_render as mr                                   # noqa: E402
from mv_engine.cache import (                                 # noqa: E402
    cache_path, code_digest, frame_key, link_or_copy,
)
from mv_engine.track import Session as TrSession, predict_track  # noqa: E402
from mingyue.loader import load as load_shots                 # noqa: E402


_W: dict = {}


def _init(out: str, cache: str, version: str) -> None:
    """spawn worker 入口 —— 只在 miss 存在时才会被调用。"""
    o = Path(out)
    mr.OUT = o
    pe._PATHS = pe.PVPaths(assets_dir=mr.ASSETS, wav=mr.WAV, out_dir=o, slug="mingyue")
    _sess.configure(mr.ASSETS, mr.TEX, mr.GEN)
    _W["cache_root"] = Path(cache)
    _W["version"]    = version
    _W["shots"]      = load_shots(
        Path(__file__).resolve().parents[2] / "voice_room" / "mingyue"
        / f"shots_{version}.yaml"
    )


def _render_miss(job: tuple[int, float, str]) -> tuple[int, str]:
    """job = (frame_index, t, key)。渲一帧并写到内容寻址位置。"""
    i, t, key = job
    im, _bb = mr.render_frame(t, _W["shots"], _W["version"])
    dst = cache_path(_W["cache_root"], key)
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp = dst.with_name(f"{dst.name}.tmp.{os.getpid()}")
    im.save(tmp, format="PNG")
    os.replace(tmp, dst)
    return i, key


def render(out: Path, cache_root: Path, versions: list[str], jobs: int) -> None:
    engine_root = Path(__file__).resolve().parents[1]
    film_root   = ROOT / "pipeline" / "voice_room" / "mingyue"
    code = code_digest(engine_root, film_root)
    render_cfg = {"W": mr.W, "H": mr.H, "FPS": mr.FPS,
                  "PAD_W": mr.PAD_W, "PAD_H": mr.PAD_H,
                  "DARK_FLOOR": mr.DARK_FLOOR}

    pe._PATHS = pe.PVPaths(assets_dir=mr.ASSETS, wav=mr.WAV, out_dir=out, slug="mingyue")
    _sess.configure(mr.ASSETS, mr.TEX, mr.GEN)

    for v in versions:
        t0 = time.time()
        shots_path = (Path(__file__).resolve().parents[2] / "voice_room" / "mingyue"
                      / f"shots_{v}.yaml")
        shots = load_shots(shots_path)

        n = round((mr.SEG_T1 - mr.SEG_T0) * mr.FPS)
        frames_dir = out / v / "_frames"
        frames_dir.mkdir(parents=True, exist_ok=True)

        # 1) 父进程算 keys
        jobs_to_run: list[tuple[int, float, str]] = []
        keys: dict[int, str] = {}
        hits = 0
        for i in range(n):
            t = mr.SEG_T0 + i / mr.FPS
            sh = mr.active(shots, t)
            k_prog = sh.k(t)
            items = sh.items(t, k_prog)
            key = frame_key(v, t, sh, items, code, render_cfg)
            keys[i] = key
            if cache_path(cache_root, key).exists():
                hits += 1
            else:
                jobs_to_run.append((i, t, key))

        elapsed = time.time() - t0
        print(f"[{v}] {n} 帧 · hit {hits} · miss {len(jobs_to_run)} · "
              f"key 计算 {elapsed:.1f}s")

        # 2) miss 交给 worker pool
        if jobs_to_run:
            t0 = time.time()
            if jobs > 1:
                ctx = mp.get_context("spawn")
                with ctx.Pool(jobs, initializer=_init,
                              initargs=(str(out), str(cache_root), v)) as pool:
                    done = 0
                    for _i, _key in pool.imap_unordered(_render_miss,
                                                         jobs_to_run, chunksize=4):
                        done += 1
                        if done % 20 == 0:
                            print(f"[{v}] miss 渲染 {done}/{len(jobs_to_run)} "
                                  f"{time.time() - t0:.0f}s", flush=True)
            else:
                _init(str(out), str(cache_root), v)
                for job in jobs_to_run:
                    _render_miss(job)
            print(f"[{v}] miss 渲染完 · {time.time() - t0:.0f}s")

        # 3) 全部帧 hardlink 到 _frames/
        for i in range(n):
            src = cache_path(cache_root, keys[i])
            dst = frames_dir / f"f{i:05d}.png"
            link_or_copy(src, dst)

        # 4) motion.json 由预测器直出(不靠 worker 收 bbox —— 100% hit 时 worker 不跑)
        tr_sess = TrSession(mr)
        track = predict_track(shots, mr.SEG_T0, mr.SEG_T1, mr.FPS, tr_sess)
        (out / v / "motion.json").write_text(
            json.dumps(track, ensure_ascii=False), encoding="utf-8")

        # 5) index.json 便于诊断
        (out / v / "index.json").write_text(
            json.dumps({"n": n, "hits": hits, "misses": len(jobs_to_run),
                        "keys": {str(i): k for i, k in keys.items()}},
                       ensure_ascii=False, indent=1),
            encoding="utf-8")

        print(f"[{v}] 完成 · frames + motion.json + index.json")


def main() -> int:
    ap = argparse.ArgumentParser(description="内容寻址缓存渲染")
    ap.add_argument("--out", type=Path,
                    default=ROOT / ".cache" / "mv_engine" / "cached_out")
    ap.add_argument("--cache", type=Path,
                    default=ROOT / ".cache" / "mv_engine" / "framecache")
    ap.add_argument("--version", nargs="*", default=["a", "b"])
    ap.add_argument("--jobs", type=int, default=4)
    args = ap.parse_args()
    render(args.out.resolve(), args.cache.resolve(), args.version, args.jobs)
    return 0


if __name__ == "__main__":
    sys.exit(main())
