"""工具层 — 六步真实实现，复用 src/mvstudio 的 provider（只读，不改引擎）。

调用链：conductor → tools.py → mvstudio.providers.* / director.drafting

每个工具签名统一：
    run(inputs, out_dir, params, prompt_file=None) -> ToolResult
失败一律结构化返回 ok=False + error（控制器路由到 reject，不炸状态机）。

本地/免费步：00_intake（ffprobe+whisper）、05_delivery（ffmpeg+PIL）
付费步：01_analysis（LLM）、02_storyboard（LLM）、03_keyframes（图像）、04_shots（Seedance）
小样验证：环境变量 MV_MAX_SHOTS=2 限制镜头数（省钱）。
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Optional

import yaml

from . import media
from .contracts import ToolResult

_MV_OK = media._MV_PLATFORM_OK


def _write(out_dir: Path, name: str, body: str) -> str:
    p = Path(out_dir) / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")
    return name


def _load_yaml(path: Path) -> dict:
    try:
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _find(inputs, filename: str) -> Optional[Path]:
    """在 _input 暂存树里找某个产物文件（返回第一个）。"""
    for base in (inputs or []):
        for p in Path(base).rglob(filename):
            return p
    return None


_REQUEST_TEMPLATE = """\
# 物料清单 — 填好路径后重跑：run <片名>
# 路径可用绝对路径；含空格请加引号。
audio: ""                       # 音乐文件 wav/mp3/aac/m4a/flac
lyrics: ""                      # 歌词文件：
                                #   .lrc  — 自带时间轴，直接用（最准）
                                #   .txt  — 一行一句，whisper 出时间轴（容错对齐）
                                #   .xlsx — 表格，whisper 出时间轴（容错对齐）
                                #   留空  — 纯 whisper 听音频猜词+时间（唱歌易错字）
lyrics_column: ""               # 仅 .xlsx：歌词在哪列（列字母如 "B" 或表头名）；留空自动挑
intent: ""                      # 一句话创作意图：这首歌想表达什么
characters:                     # 人物图（至少 1 个）
  - path: ""
    name: ""                    # 角色名（留空则用文件名）
"""


def intake_validate(inputs, out_dir, params, prompt_file=None) -> ToolResult:
    """00_intake — 收物料 + 校验 + 产歌词时间码。

    读 00_intake/request.yaml（首跑自动生成模板并要求用户填）。
    校验音频/人物图存在，ffprobe 取时长，whisper/.lrc 产 lyrics_timed.json。
    """
    out_dir = Path(out_dir)
    req_path = out_dir / "request.yaml"
    if not req_path.is_file() or not (_load_yaml(req_path).get("audio") or "").strip():
        _write(out_dir, "request.yaml", _REQUEST_TEMPLATE)
        return ToolResult(ok=False, error=media.err(
            "need_materials",
            "请先填物料清单。已在 00_intake/request.yaml 生成模板。",
            "填好 audio / lyrics / intent / characters 后重跑：run <片名>",
        ))

    req = _load_yaml(req_path)
    audio = Path(str(req.get("audio", "")).strip()).expanduser()
    if not audio.is_file() or audio.suffix.lower() not in media.AUDIO_EXT:
        return ToolResult(ok=False, error=media.err(
            "bad_audio", f"音乐文件找不到或格式不支持：{audio}",
            f"支持 {', '.join(sorted(media.AUDIO_EXT))}"))

    chars = []
    for i, c in enumerate(req.get("characters") or [], 1):
        cp = Path(str((c or {}).get("path", "")).strip()).expanduser()
        if not cp.is_file() or cp.suffix.lower() not in media.IMAGE_EXT:
            return ToolResult(ok=False, error=media.err(
                "bad_character", f"人物图找不到或格式不支持：{cp}",
                f"支持 {', '.join(sorted(media.IMAGE_EXT))}"))
        chars.append({"path": str(cp), "name": str((c or {}).get("name") or cp.stem)})
    if not chars:
        return ToolResult(ok=False, error=media.err(
            "no_character", "至少需要 1 个人物图。", "在 request.yaml 的 characters 下补 path"))

    try:
        duration = media.audio_duration_seconds(audio)
    except RuntimeError as exc:
        return ToolResult(ok=False, error=media.err("probe_failed", str(exc), "确认 ffprobe 已安装"))

    # —— 歌词时间码 ——
    #   .lrc            → 自带时间轴，直接解析（最准）
    #   .txt / .xlsx    → 文字权威 + whisper 时间轴（容错对齐）
    #   留空 / 其它失败  → whisper 自由转录兜底（唱歌易错字）
    lyrics_src = str(req.get("lyrics", "")).strip()
    lyrics_col = str(req.get("lyrics_column", "")).strip() or None
    method, entries = "none", []
    try:
        suffix = Path(lyrics_src).expanduser().suffix.lower() if lyrics_src else ""
        if suffix == ".lrc":
            entries = media.parse_lrc(Path(lyrics_src).expanduser().read_text(encoding="utf-8"))
            method = "lrc"
        elif suffix in (".txt", ".xlsx", ".xls"):
            lines = media.read_lyrics_lines(Path(lyrics_src), lyrics_col)
            entries = media.align_lyrics_to_audio(lines, audio, duration)
            method = f"align({suffix.lstrip('.')})"
        if not entries:
            entries = media.whisper_timed_lyrics(audio, duration)
            method = "whisper"
    except Exception as exc:
        return ToolResult(ok=False, error=media.err(
            "lyrics_timing_failed", f"歌词时间码生成失败：{exc}",
            "改用 .lrc/.txt/.xlsx；或确认 faster-whisper 与本地模型已装"))
    if not entries:
        return ToolResult(ok=False, error=media.err(
            "no_lyrics", "没能得到任何歌词时间码。", "提供 .lrc/.txt/.xlsx 或可转录的音频"))

    _write(out_dir, "lyrics_timed.json", json.dumps(
        {"version": 1, "entries": entries}, ensure_ascii=False, indent=2) + "\n")

    manifest = {
        "version": 1, "status": "intake_validated",
        "audio": {"path": str(audio), "digest": media.sha256_file(audio),
                  "duration_seconds": round(duration, 3)},
        "lyrics": {"source": lyrics_src or "(whisper)", "timed": "lyrics_timed.json",
                   "method": method, "lines": len(entries)},
        "intent": str(req.get("intent", "")).strip(),
        "characters": chars,
    }
    _write(out_dir, "manifest.yaml", yaml.safe_dump(manifest, allow_unicode=True, sort_keys=False))
    _write(out_dir, "intent.md", f"# 创作意图\n\n{manifest['intent'] or '（未填写）'}\n")

    mm, ss = divmod(int(duration), 60)
    _write(out_dir, "validation_report.md",
           "# 物料校验报告\n\n"
           f"- 音乐：`{audio.name}`（{mm}分{ss:02d}秒）✅\n"
           f"- 歌词：{len(entries)} 行时间码（来源：{method}）✅\n"
           f"- 人物：{'、'.join(c['name'] for c in chars)}（{len(chars)} 个）✅\n"
           f"- 意图：{manifest['intent'] or '（未填）'}\n")

    return ToolResult(ok=True,
                      outputs=["manifest.yaml", "validation_report.md", "intent.md", "lyrics_timed.json"],
                      meta={"step": "00_intake", "duration": round(duration, 1),
                            "lyric_lines": len(entries), "method": method})


def _semantic_port():
    from mvstudio.providers.semantic_openai import OpenAICompatibleSemanticPort
    return OpenAICompatibleSemanticPort.from_env()


def _llm_model() -> str:
    import os
    return os.environ.get("LLM_MODEL", "").strip() or "gpt-4-turbo"


def llm_analyze(inputs, out_dir, params, prompt_file=None) -> ToolResult:
    """01_analysis — 复用 director.drafting.draft_maps。

    产 beats/lyrics_semantic/music_map/character_map（draft_maps），
    再合成 story.md（人可读）与 title_card.yaml（标题卡契约）。
    """
    import tempfile
    out_dir = Path(out_dir)
    manifest_path = _find(inputs, "manifest.yaml")
    timed_path = _find(inputs, "lyrics_timed.json")
    if not manifest_path or not timed_path:
        return ToolResult(ok=False, error=media.err(
            "missing_intake", "找不到上游 00_intake 的产物。", "先跑通 00_intake 并批准"))

    manifest = _load_yaml(manifest_path)
    audio_info = manifest.get("audio", {})
    src_audio = Path(audio_info.get("path", ""))
    if not src_audio.is_file():
        return ToolResult(ok=False, error=media.err(
            "audio_moved", f"音频文件已不在原路径：{src_audio}", "重跑 00_intake 或恢复文件"))
    timed = json.loads(Path(timed_path).read_text(encoding="utf-8"))

    # draft_maps 要求音频落在 <staging>/inputs/audio/，且 manifest 路径以 inputs/audio/ 开头
    staging = Path(tempfile.mkdtemp(prefix="mvmaps-", dir=str(out_dir)))
    audio_rel = f"inputs/audio/{src_audio.name}"
    dst_audio = staging / audio_rel
    dst_audio.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src_audio, dst_audio)

    intake = {
        "status": "intake_validated",
        "audio": {"path": audio_rel, "digest": media.sha256_file(dst_audio),
                  "duration_seconds": audio_info.get("duration_seconds")},
        "characters": [{"path": c["path"]} for c in manifest.get("characters", [])],
    }
    brief = {"intent": manifest.get("intent", ""),
             "characters": [{"name": c["name"]} for c in manifest.get("characters", [])]}

    try:
        port = _semantic_port()
    except Exception as exc:
        shutil.rmtree(staging, ignore_errors=True)
        return ToolResult(ok=False, error=media.err(
            "llm_config", f"文本分析服务未配置：{exc}",
            "在 mv-agent/.env 填 LLM_BASE_URL / LLM_API_KEY"))

    try:
        from mvstudio.director.drafting import draft_maps
        result = draft_maps(intake, timed, brief, port, str(staging), _llm_model())
    except Exception as exc:
        shutil.rmtree(staging, ignore_errors=True)
        return ToolResult(ok=False, error=media.err(
            "analysis_failed", f"LLM 分析失败：{exc}",
            "检查 LLM 服务地址/额度，或改歌词时间码后重跑"))

    # draft_maps 写到 <staging>/creative/，搬到本步产物目录
    creative = staging / "creative"
    for name in ("beats.json", "lyrics_semantic.json", "music_map.yaml", "character_map.yaml"):
        src = creative / name
        if src.is_file():
            shutil.copy2(src, out_dir / name)
    shutil.rmtree(staging, ignore_errors=True)

    outs = _synthesize_story_and_title(out_dir, manifest, result)

    return ToolResult(ok=True,
                      outputs=["beats.json", "lyrics_semantic.json", "music_map.yaml",
                               "character_map.yaml", "story.md", "title_card.yaml"],
                      meta={"step": "01_analysis", "bpm": result.get("beats", {}).get("bpm_candidate"),
                            "sections": len(result.get("music_map", {}).get("sections", [])),
                            "characters": len(result.get("character_map", {}).get("characters", []))})


def _synthesize_story_and_title(out_dir: Path, manifest: dict, result: dict) -> None:
    """由 music_map / character_map / 意图合成人可读 story.md + title_card.yaml 契约。"""
    mm = result.get("music_map", {})
    cm = result.get("character_map", {})
    sections = mm.get("sections", [])
    chars = cm.get("characters", [])
    intent = manifest.get("intent", "") or "（未填意图）"

    lines = ["# 故事框架\n", f"**创作意图**：{intent}\n",
             f"**音乐**：约 {int(mm.get('duration', 0))} 秒 · BPM {mm.get('bpm', '?')} "
             f"· {len(sections)} 个段落\n", "\n## 段落走向\n"]
    for s in sections:
        t0, t1 = s.get("time", [0, 0])
        lines.append(f"- **{s.get('id')}**（{t0:.0f}–{t1:.0f}s · {s.get('music_role','')}）："
                     f"{s.get('emotion','')}\n")
    lines.append("\n## 人物\n")
    for c in chars:
        lines.append(f"- **{c.get('name', c.get('id'))}**：{c.get('director_function','')}\n")
    _write(out_dir, "story.md", "".join(lines))

    # 标题卡契约：片名/意图 → 开场大标题；结尾用意图收束（用户可后改）
    title = (manifest.get("intent", "") or "").strip()[:8] or "无题"
    tc = {
        "version": 1, "art_style": "金墨朱砂",
        "opening": {"title": title, "subtitle": ""},
        "ending": {"title": "", "subtitle": "", "seal": ""},
    }
    _write(out_dir, "title_card.yaml", yaml.safe_dump(tc, allow_unicode=True, sort_keys=False))


def llm_storyboard(inputs, out_dir, params, prompt_file=None) -> ToolResult:
    """02_storyboard — 按 music_map 段落逐镜出分镜（LLM 创意 + 段落平铺）。

    覆盖铁律：分镜必须铺满整首歌 —— 每个段落按其真实时长切成多镜，镜头总长≈歌曲时长，
    绝不出现「镜头总长 < 歌曲时长」。单镜时长受 Seedance 硬限 4~15s；镜头数由段落能量
    自适应（高能量段落切得更碎、更快切）。LLM 按每段所需镜头数产出对应条数的不同创意，
    同段各镜围绕该段歌词/情绪递进、不同义重复。
    """
    from mvstudio.director.drafting import run_bounded_task, ModelBudget

    out_dir = Path(out_dir)
    mm = _load_yaml(_find(inputs, "music_map.yaml") or Path("/nonexistent"))
    cm = _load_yaml(_find(inputs, "character_map.yaml") or Path("/nonexistent"))
    sections = mm.get("sections", [])
    if not sections:
        return ToolResult(ok=False, error=media.err(
            "no_sections", "上游 music_map 没有段落。", "先跑通 01_analysis 并批准"))

    # 平铺规划：每段 → 一串 4~15s 的子镜时长，铺满该段真实时长（覆盖铁律）。
    plan = _plan_shots(sections)  # [(section, [dur,dur,...]), ...]

    # MV_MAX_SHOTS：小样上限，按「镜头总数」截断规划（而非按段落数），仍保证被保留段落铺满。
    cap = media.max_shots()
    if cap:
        plan = _cap_plan(plan, cap)

    payload = {
        "duration_seconds": mm.get("duration"),
        "characters": [{"id": c.get("id"), "name": c.get("name"),
                        "director_function": c.get("director_function", "")}
                       for c in cm.get("characters", [])],
        "sections": [{"id": s.get("id"),
                      "seconds": round(s.get("time", [0, 0])[1] - s.get("time", [0, 0])[0], 1),
                      "music_role": s.get("music_role", ""), "emotion": s.get("emotion", ""),
                      "energy": s.get("energy", 3), "shots_needed": len(durs)}
                     for s, durs in plan],
    }
    try:
        port = _semantic_port()
        resp, audit = run_bounded_task(
            port, "visual_score.creative_draft_requested", payload,
            _llm_model(), ModelBudget(),
            "Cover the whole song: for each section produce exactly `shots_needed` consecutive "
            "shots that advance its lyric/emotion without repeating. Set each shot id to "
            "\"{section_id}#{n}\" (n starting at 1). Keep every field one drawable sentence.")
    except Exception as exc:
        return ToolResult(ok=False, error=media.err(
            "storyboard_failed", f"分镜生成失败：{exc}",
            "检查 LLM 服务/额度；或改 prompts 后重跑"))

    drafts = resp.get("shots", []) if isinstance(resp, dict) else []
    shots = _assemble_shots(plan, drafts)
    _write(out_dir, "shots.yaml", yaml.safe_dump({"shots": shots}, allow_unicode=True, sort_keys=False))
    # scene_groups：同段的多个子镜归到一个组（下游按段落聚合仍成立）。
    groups: dict = {}
    for sh in shots:
        groups.setdefault(sh["section_id"], []).append(sh["id"])
    _write(out_dir, "scene_groups.yaml", yaml.safe_dump(
        {"groups": [{"id": sid, "shots": ids} for sid, ids in groups.items()]},
        allow_unicode=True, sort_keys=False))

    covered = sum(s["duration"] for s in shots)
    song = round(float(mm.get("duration") or 0), 1)
    md = ["# 分镜脚本\n",
          f"\n共 {len(shots)} 个镜头，覆盖 {covered}s / 歌曲 {song}s"
          + (f"（小样上限 MV_MAX_SHOTS={cap}）" if cap else "") + "：\n\n",
          "| # | 段落 | 时长 | 画面 | 动作 |\n|---|---|---|---|---|\n"]
    for s in shots:
        md.append(f"| {s['id']} | {s['section_id']} | {s['duration']}s | "
                  f"{s['first_frame']} | {s['primary_action']} |\n")
    _write(out_dir, "storyboard.md", "".join(md))

    return ToolResult(ok=True, outputs=["shots.yaml", "storyboard.md", "scene_groups.yaml"],
                      meta={"step": "02_storyboard", "shots": len(shots),
                            "covered_seconds": covered, "song_seconds": song, "capped": bool(cap)})


# 段落能量(1~5) → 目标单镜时长(s)：能量越高切得越碎、切换越快。
_ENERGY_TARGET = {1: 12, 2: 11, 3: 9, 4: 7, 5: 6}
_CLIP_MIN, _CLIP_MAX = 4, 15  # Seedance 硬限：单镜必须落在 [4,15]s


def _split_durations(length: float, target: int) -> list:
    """把一个 length 秒的段落切成若干 4~15s 的整数时长，总和≈length，铺满该段。"""
    total = max(_CLIP_MIN, int(round(length)))
    k = max(1, round(total / target))
    while total / k > _CLIP_MAX:      # 单镜会超 15s → 多切
        k += 1
    while k > 1 and total / k < _CLIP_MIN:  # 单镜会不足 4s → 少切
        k -= 1
    base, rem = divmod(total, k)
    durs = [base + (1 if i < rem else 0) for i in range(k)]
    return [max(_CLIP_MIN, min(_CLIP_MAX, d)) for d in durs]


def _plan_shots(sections: list) -> list:
    """每段 → (section, [子镜时长...])，按能量自适应镜头数，铺满整段。"""
    plan = []
    for s in sections:
        t0, t1 = s.get("time", [0, 0])
        length = (t1 - t0) or 5
        target = _ENERGY_TARGET.get(int(s.get("energy", 3)), 9)
        plan.append((s, _split_durations(length, target)))
    return plan


def _cap_plan(plan: list, cap: int) -> list:
    """按镜头总数上限截断规划（小样用），保留的段落仍整段铺满。"""
    out, used = [], 0
    for s, durs in plan:
        if used >= cap:
            break
        take = durs[: max(1, cap - used)]
        out.append((s, take))
        used += len(take)
    return out


def _assemble_shots(plan: list, drafts: list) -> list:
    """规划 + LLM 创意 → shots。同段多镜用 "{section_id}#n" 归组匹配 draft；
    LLM 少给时复用该段最后一条创意，缺失时回落到段落 emotion —— 覆盖始终由规划保证。"""
    # 按段落前缀归组 LLM 创意（id 形如 "chorus1#2"）；不合规的按顺序兜底。
    by_section: dict = {}
    loose = []
    for d in drafts:
        if not isinstance(d, dict):
            continue
        did = str(d.get("id", ""))
        sid = did.split("#", 1)[0] if "#" in did else ""
        (by_section.setdefault(sid, []) if sid else loose).append(d)

    shots, n = [], 0
    for s, durs in plan:
        sid = s.get("id")
        pool = by_section.get(sid) or loose
        for j, dur in enumerate(durs):
            n += 1
            d = pool[j] if j < len(pool) else (pool[-1] if pool else {})
            first_frame = (d.get("first_frame") or s.get("emotion") or "cinematic still").strip()
            action = (d.get("primary_action") or "subtle motion").strip()
            arrangement = (d.get("arrangement") or "").strip()
            shots.append({
                "id": f"SH{n:03d}",
                "section_id": sid,
                "duration": int(dur),
                "first_frame": first_frame,
                "primary_action": action,
                "image_prompt": (first_frame + ("，" + arrangement if arrangement else "")).strip("，"),
                "video_prompt": action,
            })
    return shots


def gen_keyframe(inputs, out_dir, params, prompt_file=None) -> ToolResult:
    """03_keyframes — 逐镜首帧图（gpt-image，人物图作参考，9:16）。"""
    out_dir = Path(out_dir)
    shots = _load_yaml(_find(inputs, "shots.yaml") or Path("/nonexistent")).get("shots", [])
    if not shots:
        return ToolResult(ok=False, error=media.err(
            "no_shots", "上游没有 shots.yaml。", "先跑通 02_storyboard 并批准"))
    manifest = _load_yaml(_find(inputs, "manifest.yaml") or Path("/nonexistent"))
    refs = [c["path"] for c in manifest.get("characters", []) if Path(c["path"]).is_file()]

    try:
        from mvstudio.providers.image_openai import OpenAICompatibleImageProvider
        provider = OpenAICompatibleImageProvider.from_env(__import__("os").environ)
    except Exception as exc:
        return ToolResult(ok=False, error=media.err(
            "image_config", f"画面生成服务未配置：{exc}",
            "在 mv-agent/.env 填 GPT_IMAGE_BASE_URL / GPT_IMAGE_API_KEY"))

    index, made, done, first_err = [], [], 0, None
    for s in shots:
        name = f"{s['id']}_keyframe.png"
        try:
            data = provider.generate(s["image_prompt"], references=refs, size="1024x1536")
            (out_dir / name).write_bytes(data)
            index.append({"id": s["id"], "keyframe": name, "duration": s["duration"],
                          "video_prompt": s["video_prompt"], "digest": media.sha256_bytes(data)})
            made.append(name)
            done += 1
        except Exception as exc:
            first_err = first_err or f"{s['id']}: {exc}"

    if done == 0:
        return ToolResult(ok=False, error=media.err(
            "keyframe_failed", f"首帧图全部失败：{first_err}", "检查图像服务地址/额度"))

    _write(out_dir, "keyframes_index.yaml", yaml.safe_dump(
        {"keyframes": index}, allow_unicode=True, sort_keys=False))
    meta = {"step": "03_keyframes", "generated": done, "total": len(shots)}
    if first_err:
        meta["partial_error"] = first_err
    return ToolResult(ok=True, outputs=["keyframes_index.yaml", *made], meta=meta)


def gen_video(inputs, out_dir, params, prompt_file=None) -> ToolResult:
    """04_shots — 逐镜 i2v（Seedance，首帧图 → 视频，9:16/720p）。"""
    import os
    out_dir = Path(out_dir)
    idx_path = _find(inputs, "keyframes_index.yaml")
    keyframes = _load_yaml(idx_path or Path("/nonexistent")).get("keyframes", [])
    if not keyframes or not idx_path:
        return ToolResult(ok=False, error=media.err(
            "no_keyframes", "上游没有关键帧。", "先跑通 03_keyframes 并批准"))
    kf_dir = idx_path.parent

    try:
        from mvstudio.providers.seedance import SeedancePort, SeedanceTask, SeedanceFrame
        provider = SeedancePort.from_env()
    except Exception as exc:
        return ToolResult(ok=False, error=media.err(
            "video_config", f"视频生成服务未配置：{exc}",
            "在 mv-agent/.env 填 SEEDANCE_BASE_URL / SEEDANCE_API_KEY / SEEDANCE_MODEL"))
    model = os.environ.get("SEEDANCE_MODEL", "").strip() or "doubao-seedance-2-0"

    index, made, done, first_err = [], [], 0, None
    for kf in keyframes:
        kf_path = kf_dir / kf["keyframe"]
        out_name = f"{kf['id']}.mp4"
        if not kf_path.is_file():
            first_err = first_err or f"{kf['id']}: 首帧图缺失"
            continue
        try:
            data = kf_path.read_bytes()
            task = SeedanceTask(
                shot_id=kf["id"], model=model,
                prompt=kf.get("video_prompt") or "cinematic subtle motion",
                duration_seconds=int(kf.get("duration", 5)),
                first_frame=SeedanceFrame(content=data, sha256=media.sha256_bytes(data)),
                aspect_ratio="9:16", resolution="720p")
            result = provider.generate(task)
            (out_dir / out_name).write_bytes(result.video_bytes)
            index.append({"id": kf["id"], "video": out_name,
                          "duration": int(kf.get("duration", 5)),
                          "video_sha256": result.video_sha256})
            made.append(out_name)
            done += 1
        except Exception as exc:
            first_err = first_err or f"{kf['id']}: {exc}"

    if done == 0:
        return ToolResult(ok=False, error=media.err(
            "video_failed", f"视频全部失败：{first_err}", "检查 Seedance 服务地址/额度/模型名"))

    _write(out_dir, "shots_index.yaml", yaml.safe_dump(
        {"shots": index}, allow_unicode=True, sort_keys=False))
    meta = {"step": "04_shots", "generated": done, "total": len(keyframes)}
    if first_err:
        meta["partial_error"] = first_err
    return ToolResult(ok=True, outputs=["shots_index.yaml", *made], meta=meta)


# ──────────────────────────────────────────────────────────────────────────────
# 05_delivery — 合成（本地 ffmpeg + PIL 标题卡 + .ass 字幕）
# ──────────────────────────────────────────────────────────────────────────────

_OPEN_SEC = 3   # 片头标题卡时长
_END_SEC = 3    # 片尾标题卡时长

_ASS_HEAD = """[Script Info]
ScriptType: v4.00+
PlayResX: 720
PlayResY: 1280
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, Outline, Shadow, Alignment, MarginL, MarginR, MarginV
Style: Default,Noto Serif CJK SC,52,&H00F6E6FF,&H00224AD4,&H64000000,1,3,1,2,40,40,90

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def _ass_ts(seconds: float) -> str:
    seconds = max(0.0, seconds)
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def _build_ass(entries: list, offset: float, total: float) -> str:
    lines = [_ASS_HEAD]
    for i, e in enumerate(entries):
        start = float(e["start_seconds"]) + offset
        end = (float(entries[i + 1]["start_seconds"]) + offset) if i + 1 < len(entries) \
            else min(start + 4.0, total)
        end = max(end, start + 0.5)
        text = str(e.get("text", "")).replace("\n", " ").strip()
        if text:
            lines.append(f"Dialogue: 0,{_ass_ts(start)},{_ass_ts(end)},Default,,0,0,0,,{text}")
    return "\n".join(lines) + "\n"


def _run(cmd: list, cwd=None) -> tuple[bool, str]:
    import subprocess
    try:
        r = subprocess.run(cmd, capture_output=True, cwd=cwd, timeout=1800)
    except (OSError, subprocess.SubprocessError) as exc:
        return False, str(exc)
    if r.returncode != 0:
        return False, r.stderr.decode("utf-8", "replace")[-500:]
    return True, ""


def _normalize(src: Path, dst: Path, ff: str, seconds: Optional[float]) -> bool:
    """把一段（PNG 卡或 mp4 镜头）归一成 720x1280/30fps/h264 无音轨 mp4，便于 concat。"""
    scale = "scale=720:1280:force_original_aspect_ratio=decrease,pad=720:1280:(ow-iw)/2:(oh-ih)/2,setsar=1"
    if src.suffix.lower() == ".png":
        cmd = [ff, "-y", "-loop", "1", "-i", str(src), "-t", str(seconds or _OPEN_SEC),
               "-vf", scale + ",fps=30", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-an", str(dst)]
    else:
        cmd = [ff, "-y", "-i", str(src), "-vf", scale + ",fps=30",
               "-c:v", "libx264", "-pix_fmt", "yuv420p", "-an", str(dst)]
    ok, _ = _run(cmd)
    return ok and dst.is_file()


def compose(inputs, out_dir, params, prompt_file=None) -> ToolResult:
    """05_delivery — 拼接标题卡+镜头，铺音乐，烧 .ass 字幕，出成片。"""
    import tempfile
    from .titlecard import build_title_cards
    from . import cards

    out_dir = Path(out_dir)
    ff = media.ffmpeg_bin()

    shots_idx = _load_yaml(_find(inputs, "shots_index.yaml") or Path("/nonexistent")).get("shots", [])
    si_path = _find(inputs, "shots_index.yaml")
    if not shots_idx or not si_path:
        return ToolResult(ok=False, error=media.err(
            "no_videos", "上游没有视频片段。", "先跑通 04_shots 并批准"))
    shot_dir = si_path.parent

    manifest = _load_yaml(_find(inputs, "manifest.yaml") or Path("/nonexistent"))
    audio = Path(manifest.get("audio", {}).get("path", ""))
    timed_path = _find(inputs, "lyrics_timed.json")
    entries = (json.loads(timed_path.read_text(encoding="utf-8")).get("entries", [])
               if timed_path else [])

    # —— 标题卡 spec → PNG ——
    tc_path = _find(inputs, "title_card.yaml")
    specs = []
    if tc_path:
        try:
            specs = build_title_cards(tc_path)
        except Exception:
            specs = []
    _write(out_dir, "title_cards.json", json.dumps(
        {"cards": specs}, ensure_ascii=False, indent=2) + "\n")
    opening = next((s for s in specs if s.get("title_mode") == "opening"), None)
    ending = next((s for s in specs if s.get("title_mode") == "ending"), None)

    work = Path(tempfile.mkdtemp(prefix="compose-", dir=str(out_dir)))
    segments, open_used = [], 0.0
    if opening:
        png = cards.render_card(opening, work / "open.png")
        seg = work / "seg_open.mp4"
        if _normalize(png, seg, ff, _OPEN_SEC):
            segments.append(seg)
            open_used = _OPEN_SEC
    for s in shots_idx:
        src = shot_dir / s["video"]
        seg = work / f"seg_{s['id']}.mp4"
        if src.is_file() and _normalize(src, seg, ff, None):
            segments.append(seg)
    if ending:
        png = cards.render_card(ending, work / "end.png")
        seg = work / "seg_end.mp4"
        if _normalize(png, seg, ff, _END_SEC):
            segments.append(seg)

    if not segments:
        shutil.rmtree(work, ignore_errors=True)
        return ToolResult(ok=False, error=media.err(
            "normalize_failed", "所有片段归一化失败。", "确认 ffmpeg 可用、镜头 mp4 有效"))

    # —— concat（无音轨视频体）——
    listf = work / "concat.txt"
    listf.write_text("".join(f"file '{p.name}'\n" for p in segments), encoding="utf-8")
    body = work / "body.mp4"
    ok, msg = _run([ff, "-y", "-f", "concat", "-safe", "0", "-i", "concat.txt",
                    "-c", "copy", str(body)], cwd=str(work))
    if not ok or not body.is_file():
        shutil.rmtree(work, ignore_errors=True)
        return ToolResult(ok=False, error=media.err("concat_failed", f"拼接失败：{msg}", "检查 ffmpeg"))

    # —— 字幕 .ass（时间轴整体后移片头卡时长）——
    duration = float(manifest.get("audio", {}).get("duration_seconds", 0) or 0)
    _write(out_dir, "subtitle.ass", _build_ass(entries, open_used, open_used + duration + _END_SEC))

    # —— 终混：视频体 + 音乐（延迟片头卡时长）+ 烧字幕 ——
    # 视频体长度定成片长度：音乐比视频短则留静音尾（片尾卡照显），
    # 比视频长则截到视频尾（不用 -shortest，避免音乐截掉片尾卡）。
    try:
        body_dur = media.audio_duration_seconds(body)
    except RuntimeError:
        body_dur = 0.0
    final = out_dir / "final.mp4"
    have_audio = audio.is_file()
    vf = "subtitles=subtitle.ass" if entries else None
    cmd = [ff, "-y", "-i", str(body)]
    if have_audio:
        cmd += ["-itsoffset", str(open_used), "-i", str(audio)]
    if vf:
        cmd += ["-vf", vf]
    cmd += ["-map", "0:v:0"]
    if have_audio:
        cmd += ["-map", "1:a:0", "-c:a", "aac", "-b:a", "192k"]
    if body_dur > 0:
        cmd += ["-t", f"{body_dur:.3f}"]
    cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", str(final.name)]
    ok, msg = _run(cmd, cwd=str(out_dir))
    shutil.rmtree(work, ignore_errors=True)
    if not ok or not final.is_file():
        return ToolResult(ok=False, error=media.err("mux_failed", f"终混失败：{msg}", "检查 ffmpeg/字幕字体"))

    n_shots = len(shots_idx)
    _write(out_dir, "delivery_report.md",
           "# 交付报告\n\n"
           f"- 成片：`final.mp4`（9:16 / 720p）\n"
           f"- 镜头：{n_shots} 段" + (" + 片头卡" if opening else "")
           + (" + 片尾卡" if ending else "") + "\n"
           f"- 字幕：{len(entries)} 行（subtitle.ass，已烧入）\n"
           f"- 音乐：{'已铺（延迟片头卡时长对齐镜头）' if have_audio else '缺音频'}\n"
           f"- 标题卡：{len(specs)} 张（PIL 渲染，金墨朱砂色板）\n")

    return ToolResult(ok=True,
                      outputs=["final.mp4", "subtitle.ass", "title_cards.json", "delivery_report.md"],
                      meta={"step": "05_delivery", "shots": n_shots, "cards": len(specs),
                            "subtitle_lines": len(entries)})
