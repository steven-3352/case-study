"""把 mingyue_render 渲到临时目录 —— 不碰 ground truth 的 _frames。

用途:改造前后各跑一次,逐帧 sha256 + motion.json 比对。渲染进 scratch 目录,
`publish/` 下的原始产物保持只读。

**同时吐 motion.json**:`publish/` 里那份是 2026-07-26 13:14/13:32 渲的,而
`mingyue_render.py` 13:37 又改过 —— 那份 track 已经对不上当前代码,拿它当
Phase 0 的 ground truth 会验错东西。基线必须由当前代码现渲。

并行用 spawn 不用 fork(理由同 mingyue_render._init_worker:macOS 的 Accelerate
在 fork 后的子进程里调 BLAS 会挂)。子进程什么都没继承,所以 out_dir 走 initargs
重设 —— 直接依赖模块级 OUT 的话,子进程会写回 publish/。
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
sys.path.insert(0, str(ROOT / "pipeline" / "voice_room"))

import mingyue_render as mr  # noqa: E402
import paperdoll_engine as pe  # noqa: E402

_W: dict = {}


def _init(out: str, version: str) -> None:
    o = Path(out)
    mr.OUT = o
    pe._PATHS = pe.PVPaths(assets_dir=mr.ASSETS, wav=mr.WAV, out_dir=o, slug="mingyue")
    _W["version"] = version
    _W["shots"] = mr._load_shots(version)
    _W["dir"] = o / version / "_frames"


def _one(i: int) -> tuple:
    t = mr.SEG_T0 + i / mr.FPS
    im, bb = mr.render_frame(t, _W["shots"], _W["version"])
    # 先写临时名再 os.replace —— PNG 有三兆多,直接写目标名的话,任何并发的
    # 读者(比如 frame_digest)都可能读到写了一半的文件,拿到一个假 sha256。
    # 实测踩过:快照比渲染早 70 秒完成,里面混进了一帧撕裂读。
    dst = _W["dir"] / f"f{i:05d}.png"
    tmp = dst.with_name(f"{dst.name}.tmp.{os.getpid()}")
    im.save(tmp, format="PNG")   # 临时名没有 .png 后缀,格式必须显式给
    os.replace(tmp, dst)
    return i, round(t, 4), mr.active(_W["shots"], t).sid, bb


def render_to(out: Path, versions: list[str], limit: int | None, jobs: int) -> None:
    out.mkdir(parents=True, exist_ok=True)
    for v in versions:
        frames = out / v / "_frames"
        frames.mkdir(parents=True, exist_ok=True)
        n = round((mr.SEG_T1 - mr.SEG_T0) * mr.FPS)
        if limit:
            n = min(n, limit)
        t0 = time.time()
        rows: list[tuple] = []

        if jobs > 1:
            ctx = mp.get_context("spawn")
            with ctx.Pool(jobs, initializer=_init, initargs=(str(out), v)) as pool:
                for done, row in enumerate(
                        pool.imap_unordered(_one, range(n), chunksize=4), 1):
                    rows.append(row)
                    if done % 20 == 0:
                        el = time.time() - t0
                        print(f"[{v}] {done}/{n}  {el:.0f}s", flush=True)
            # imap_unordered 的返回顺序不是帧序;track 是时间序列,乱序会让
            # gate_check_motion 把相邻帧当跳变。
            rows.sort()
        else:
            _init(str(out), v)
            for i in range(n):
                rows.append(_one(i))
                if i % 20 == 0:
                    print(f"[{v}] {i}/{n}  {time.time() - t0:.0f}s", flush=True)

        track = [{"t": t, "shot": sid,
                  "bbox": [(bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2,
                           bb[2] - bb[0], bb[3] - bb[1]]}
                 for _i, t, sid, bb in rows if bb]
        (out / v / "motion.json").write_text(json.dumps(
            {"fps": mr.FPS, "w": mr.W, "h": mr.H,
             "start": mr.SEG_T0, "end": mr.SEG_T1, "track": track},
            ensure_ascii=False))
        print(f"[{v}] {n} 帧 · track {len(track)} 条 · {time.time() - t0:.0f}s",
              flush=True)


def main() -> int:
    ap = argparse.ArgumentParser(description="渲到 scratch 目录(帧 + motion.json)")
    ap.add_argument("--out", type=Path, default=ROOT / ".cache" / "mv_engine" / "scratch")
    ap.add_argument("--version", nargs="*", default=["a", "b"])
    ap.add_argument("--limit", type=int, help="只渲前 N 帧(计时用)")
    ap.add_argument("--jobs", type=int, default=4)
    args = ap.parse_args()
    render_to(args.out.resolve(), args.version, args.limit, args.jobs)
    return 0


if __name__ == "__main__":
    sys.exit(main())
