"""文件夹脚手架层：建/校验骨架、_input/ 交接、_meta/ 落盘。

每步文件夹固定结构：
  step_id/
    _input/          上游产物拷贝
    _meta/
      log.md         执行日志
      prompt_used/   本次用到的提示词副本（可复盘）
    <产物文件>
"""
from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path


def project_root(base: Path, name: str) -> Path:
    return Path(base) / name


def ensure_step_dirs(root: Path, step_id: str) -> dict[str, Path]:
    """建单步文件夹骨架，返回关键子路径。"""
    step_dir = Path(root) / step_id
    sub = {
        "step":        step_dir,
        "input":       step_dir / "_input",
        "meta":        step_dir / "_meta",
        "prompt_used": step_dir / "_meta" / "prompt_used",
    }
    for p in sub.values():
        p.mkdir(parents=True, exist_ok=True)
    return sub


def stage_inputs(root: Path, step_id: str, input_from: list[str]) -> list[Path]:
    """把上游步骤产物拷进本步 _input/（拷贝而非软链，Windows 友好）。"""
    sub = ensure_step_dirs(root, step_id)
    staged = []
    for upstream in input_from:
        up_dir = Path(root) / upstream
        if not up_dir.is_dir():
            continue
        dst = sub["input"] / upstream
        if dst.exists():
            shutil.rmtree(dst)
        # 只拷产物，跳过上游的 _input/_meta
        shutil.copytree(
            up_dir, dst,
            ignore=shutil.ignore_patterns("_input", "_meta"),
        )
        staged.append(dst)
    return staged


def append_log(root: Path, step_id: str, line: str) -> None:
    sub = ensure_step_dirs(root, step_id)
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    log_file = sub["meta"] / "log.md"
    with log_file.open("a", encoding="utf-8") as f:
        f.write(f"- `{ts}` {line}\n")


def copy_prompt_used(root: Path, step_id: str, prompts_dir: Path, names: list[str]) -> None:
    """把本步用到的提示词副本留档（可复盘用哪版提示词）。"""
    sub = ensure_step_dirs(root, step_id)
    for name in names:
        src = Path(prompts_dir) / name
        if src.is_file():
            shutil.copy2(src, sub["prompt_used"] / name)
