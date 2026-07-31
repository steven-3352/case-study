"""内容寻址帧缓存 —— 改一镜的 fx 只渲那一镜。

**key 算法**:blake2b 消化规范化 JSON,payload 包含:

- `version`   —— a / b
- `t`         —— round(t, 6),1μs 精度就够(帧步长 1/30s)
- `shot`      —— 当前帧所属 shot 的序列化(cam / items(t,k) / subject / bg / fx / hold)
                 **不包含 `note`** —— 散文更改不应让帧失效
- `code`      —— mv_engine/*.py + 本片包 *.py 的 sha256 合并摘要
- `render_cfg`—— W / H / FPS / PAD_W / PAD_H(几何几乎不变,但显式列进 key)

**为什么 items(t,k) 序列化不含 layer 的位图**:layer 由 `(kind, name, crop, ...)` 索引,
key 已经完全刻画;真素材本身在磁盘不变时结果就不变。**素材换了要自行清缓存** ——
这是 MVP 简化:完整版应把每个触碰素材的 `(path, size, mtime_ns)` 一并计入。

**存储布局**:

    <cache_root>/<key[:2]>/<key>.png     — 内容寻址,跨版本/跨渲染共享
    <out>/<version>/_frames/f00042.png   — 到缓存的 hardlink
    <out>/<version>/index.json           — 帧号 → key 映射,便于诊断

**帧输出用 hardlink 不用 symlink**:ffmpeg 拿 `f%05d.png` 通配串,symlink 会跨盘
点破;hardlink 保持真文件,而且节约 inode。同分区约束:cache_root 必须与 out
同盘(不同盘只能 fallback 到 copy)。
"""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict, is_dataclass
from pathlib import Path


def _hash_files(paths: list[Path]) -> str:
    """把多个源文件 sha 起来。文件不存在的 skip(不 raise)。"""
    h = hashlib.blake2b(digest_size=16)
    for p in sorted(paths):
        if not p.exists():
            continue
        h.update(p.name.encode())
        h.update(hashlib.sha256(p.read_bytes()).digest())
    return h.hexdigest()


def code_digest(engine_root: Path, film_root: Path) -> str:
    """mv_engine/*.py + film/*.py 的合并摘要 —— 代码一变缓存整体失效。"""
    files = list(engine_root.rglob("*.py")) + list(film_root.rglob("*.py"))
    return _hash_files(files)


def _norm(o):
    """把 shot / item 递归转成 JSON 可 dump 的 dict/list/scalar。"""
    if is_dataclass(o) and not isinstance(o, type):
        # frozen dataclass (Item) → dict; **不含**任何模块级引用
        return {k: _norm(v) for k, v in asdict(o).items()}
    if isinstance(o, (tuple, list)):
        return [_norm(x) for x in o]
    if isinstance(o, dict):
        return {k: _norm(v) for k, v in o.items()}
    if isinstance(o, (int, float, str, bool)) or o is None:
        return o
    # 其它对象(比如 Cam)→ 走 __dict__;若也没有,退成 repr(不推荐但兜底)
    if hasattr(o, "__dict__"):
        return {k: _norm(v) for k, v in vars(o).items() if not k.startswith("_")}
    return repr(o)


def frame_key(version: str, t: float, shot, items_tuple: tuple,
              code: str, render_cfg: dict) -> str:
    """→ 十六进制 blake2b(32) 帧 key。

    `shot` 传 MShot 对象(Cam 属性会被 _norm 拆开),`items_tuple` 传该帧的 items(t,k)
    结果 —— 加载器已保证 items 是 frozen dataclass,可稳定序列化。
    """
    payload = {
        "version": version,
        "t":       round(t, 6),
        "sid":     shot.sid,
        "cam":     _norm(shot.cam),
        "items":   _norm(items_tuple),
        "subject": list(shot.subject),
        "bg":      _norm(shot.bg),
        "fx":      _norm(shot.fx),
        "code":    code,
        "render":  render_cfg,
    }
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()
    return hashlib.blake2b(blob, digest_size=16).hexdigest()


def cache_path(cache_root: Path, key: str) -> Path:
    return cache_root / key[:2] / f"{key}.png"


def link_or_copy(src: Path, dst: Path) -> None:
    """优先 hardlink;跨盘或 hardlink 失败退回 copy(不 raise,让流程继续)。"""
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        dst.unlink()
    try:
        os.link(src, dst)
    except OSError:
        # 跨设备 / 权限 / 文件系统不支持 hardlink → 兜底 copy
        import shutil                                          # noqa: PLC0415
        shutil.copyfile(src, dst)
