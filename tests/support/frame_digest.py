"""逐帧 sha256 快照 —— 引擎改造全程的回归基线。

Phase 1(拆分)和 Phase 3(缓存)都是纯代码搬家,画面必须逐帧完全一致。
"1% 以内的差异"在这两个阶段不是可接受误差,是 bug。所以基线取 sha256
而不是像素距离。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[3]


def digest_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def digest_dir(frames: Path, workers: int = 8) -> dict[str, str]:
    """线程池,不是进程池 —— 读文件和 hashlib.update 都会放开 GIL,
    这活是 I/O + 摘要,不是 Python 字节码。进程池在这里只会白付序列化成本。
    """
    paths = sorted(frames.glob("f*.png"))
    with ThreadPoolExecutor(max_workers=workers) as ex:
        return dict(zip((p.name for p in paths), ex.map(digest_file, paths)))


def snapshot(versions: Iterable[str], out_root: Path,
             workers: int = 8) -> dict[str, dict[str, str]]:
    return {v: digest_dir(out_root / v / "_frames", workers) for v in versions}


def compare(before: dict, after: dict) -> list[str]:
    """返回人类可读的差异行;空列表 = 逐帧一致。"""
    diffs: list[str] = []
    for v in sorted(set(before) | set(after)):
        b, a = before.get(v, {}), after.get(v, {})
        if not b or not a:
            diffs.append(f"[{v}] 一侧缺失 (before={len(b)} after={len(a)})")
            continue
        if set(b) != set(a):
            diffs.append(f"[{v}] 帧集合不同: 少 {sorted(set(b) - set(a))[:5]} "
                         f"多 {sorted(set(a) - set(b))[:5]}")
        for name in sorted(set(b) & set(a)):
            if b[name] != a[name]:
                diffs.append(f"[{v}] {name} {b[name][:12]} → {a[name][:12]}")
    return diffs


def main() -> int:
    ap = argparse.ArgumentParser(description="逐帧 sha256 快照 / 比对")
    ap.add_argument("--out-root", type=Path,
                    default=ROOT / "publish" / "语音厅" / "sample_22465_29780")
    ap.add_argument("--version", nargs="*", default=["a", "b"])
    ap.add_argument("--write", type=Path, help="写快照到此 json")
    ap.add_argument("--check", type=Path, help="与此 json 比对,不一致则退出码 1")
    ap.add_argument("--workers", type=int, default=8, help="摘要线程数")
    args = ap.parse_args()

    snap = snapshot(args.version, args.out_root, args.workers)
    total = sum(len(v) for v in snap.values())
    print(f"{total} 帧 · " + " ".join(f"{k}={len(v)}" for k, v in snap.items()))

    if args.write:
        args.write.parent.mkdir(parents=True, exist_ok=True)
        args.write.write_text(json.dumps(snap, indent=1, sort_keys=True))
        print(f"→ {args.write}")

    if args.check:
        diffs = compare(json.loads(args.check.read_text()), snap)
        if diffs:
            print(f"\n✗ {len(diffs)} 处不一致:")
            for d in diffs[:40]:
                print("  " + d)
            if len(diffs) > 40:
                print(f"  … 另有 {len(diffs) - 40} 处")
            return 1
        print("✓ 逐帧 sha256 完全一致")
    return 0


if __name__ == "__main__":
    sys.exit(main())
