"""工具层 — ad2-agent 当前执行骨架，复用 src/mvstudio provider。

调用链：conductor → tools.py → mvstudio.providers.*（semantic / image / seedance）

每个工具签名统一：
    run(inputs, out_dir, params, prompt_file=None) -> ToolResult
失败一律结构化返回 ok=False + error（控制器路由到 reject，不炸状态机）。

本地/免费步：00_intake（读图/校验）、05_delivery（ffmpeg 合成）
付费步：01_analysis（LLM）、02_storyboard（LLM）、03_keyframes（图像）、04_shots（Seedance,仅生成镜/i2v展示镜）
小样验证：环境变量 AD_MAX_SHOTS=2 限制镜头数（省钱）。

保真铁律：display 镜的产品素材不进入生成模型 —— gen_keyframe 用 PIL 做确定性缩放与
alpha paste，并记录 source_digest/composite_digest；不宣称编码后字节等于原文件。
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

import yaml

from . import media
from .contracts import ToolResult


def _write(out_dir: Path, name: str, body: str) -> str:
    p = Path(out_dir) / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")
    return name


def _load_yaml(path: Path) -> dict:
    try:
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        return data if isinstance(data, dict) else {}
    except Exception:  # noqa: BLE001
        return {}


def _find(inputs, filename: str) -> Optional[Path]:
    """在 _input 暂存树里找某个产物文件（返回第一个）。"""
    for base in (inputs or []):
        for p in Path(base).rglob(filename):
            return p
    return None


def _read_prompt(prompt_file: Optional[Path]) -> str:
    """读提示词文件正文（去掉首行 # 标题占位无所谓，整体交给 LLM 当 instruction）。"""
    if prompt_file and Path(prompt_file).is_file():
        try:
            return Path(prompt_file).read_text(encoding="utf-8").strip()
        except OSError:
            return ""
    return ""


def _select_targets(items: list, only) -> tuple[list, list]:
    """按 only（镜号集合）筛选 items；only 为空 → 全部。返回 (targets, not_found)。"""
    if not only:
        return list(items), []
    want = {str(x).upper() for x in only}
    by_id = {str(i.get("id")).upper(): i for i in items if isinstance(i, dict)}
    targets = [by_id[w] for w in want if w in by_id]
    not_found = [w for w in want if w not in by_id]
    # 保持原顺序
    order = {str(i.get("id")).upper(): n for n, i in enumerate(items)}
    targets.sort(key=lambda i: order.get(str(i.get("id")).upper(), 10**9))
    return targets, not_found


def _rebuild_index(all_items: list, by_id: dict, key: str) -> list:
    """按分镜原顺序重排索引（只保留已生成的镜）。"""
    out = []
    for it in all_items:
        sid = it.get("id")
        if sid in by_id:
            out.append(by_id[sid])
    return out


def _compose_storyboard_grid(out_dir: Path, index: list[dict]) -> Optional[str]:
    """从 keyframes_index 生成 N 宫格拼图。<2 镜返回 None(caller 不加入 outputs)。"""
    if len(index) < 2:
        return None
    from mvstudio.media import compose_storyboard, resolve_cjk_font
    entries = [
        {"id": e["id"],
         "keyframe_path": Path(out_dir) / e["keyframe"],
         "duration": e.get("duration", 0)}
        for e in index if isinstance(e, dict) and e.get("keyframe")
    ]
    if len(entries) < 2:
        return None
    result = compose_storyboard(
        entries,
        Path(out_dir) / "storyboard_grid.png",
        font_path=resolve_cjk_font(),
    )
    return "storyboard_grid.png" if result else None


def prepare_pose_reference(source: Path, out_path: Path, *,
                           model: Optional[Path] = None,
                           label: bool = True) -> ToolResult:
    """把人物参考片转成无脸骨架，并把覆盖率门失败归一成 ToolResult。

    公网托管不属于本地媒体层；成功结果的 ``meta.output`` 是后续上传到受控
    HTTPS 目录的集成点，托管后把 URL 写入镜头的 ``reference_video_url``。
    """
    from mvstudio.media import PoseReferenceError

    source, out_path = Path(source), Path(out_path)
    try:
        pose = media.pose_reference_from_video(
            source, out_path, model=model, label=label)
        coverage = float(pose.get("coverage", 0.0))
        if coverage < media.POSE_REFERENCE_MIN_COVERAGE:
            raise PoseReferenceError(
                f"Pose detection coverage too low: {coverage:.1%} "
                f"(< {media.POSE_REFERENCE_MIN_COVERAGE:.0%})"
            )
    except Exception as exc:  # CV 依赖和门禁错误均由公共库归一为 PoseReferenceError
        if isinstance(exc, PoseReferenceError):
            low_coverage = "coverage too low" in str(exc).lower()
            if low_coverage and source.resolve() != out_path.resolve():
                try:
                    out_path.unlink(missing_ok=True)
                except OSError:
                    pass
            code = "pose_reference_low_coverage" if low_coverage else "pose_reference_failed"
            message = ("参考视频的清晰全身主体覆盖率不足，未生成可用骨架参考。"
                       if low_coverage else f"参考视频去身份化失败：{exc}")
            return ToolResult(
                ok=False,
                error=media.err(
                    code,
                    message,
                    "换一段主体清晰且全身入镜的参考片；或改镜头设计；或放弃复制该运镜。",
                ),
                meta={
                    "step": "pose_reference",
                    "min_coverage": media.POSE_REFERENCE_MIN_COVERAGE,
                    "suggestions": [
                        "replace_reference_clip",
                        "redesign_shot",
                        "drop_reference_motion",
                    ],
                },
            )
        return ToolResult(
            ok=False,
            error=media.err(
                "pose_reference_failed",
                f"参考视频去身份化失败：{exc}",
                "检查源视频、姿态模型和 CV 依赖后重试。",
            ),
            meta={"step": "pose_reference",
                  "min_coverage": media.POSE_REFERENCE_MIN_COVERAGE},
        )

    return ToolResult(
        ok=True,
        outputs=[pose["output"]],
        meta={
            "step": "pose_reference",
            **pose,
            "min_coverage": media.POSE_REFERENCE_MIN_COVERAGE,
            "hosting": "external_https_required",
        },
    )


def _llm_model() -> str:
    return os.environ.get("LLM_MODEL", "").strip() or "gpt-4-turbo"


def _semantic_call(instruction: str, payload: dict, output_schema: dict,
                   event_type: str, reason: str, max_tokens: int = 4000) -> dict:
    """直接调 semantic port（绕开音乐专用 run_bounded_task/_SCHEMAS），返回解析后的 dict。

    抛异常给上层工具包成结构化 error。
    """
    import hashlib
    from mvstudio.director.drafting import ModelBudget, ModelTask
    from mvstudio.providers.semantic_openai import OpenAICompatibleSemanticPort

    def _h(obj) -> str:
        return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=True)
                              .encode("utf-8")).hexdigest()

    port = OpenAICompatibleSemanticPort.from_env()
    task = ModelTask(
        event_type=event_type,
        model=_llm_model(),
        budget=ModelBudget(max_tokens=max_tokens),
        reason=reason,
        input_contract_hash=_h(payload),
        output_schema_hash=_h(output_schema),
        output_schema=output_schema,
        payload=payload,
        instruction=instruction,
    )
    result = port.run(task)
    return dict(result.output)


_REQUEST_TEMPLATE = """\
# 物料清单 — 填好后重跑：run <片名>
# 路径可用绝对路径；含空格请加引号。
aspect_ratio: "9:16"            # 成片画幅：9:16(竖) / 16:9(横) / 1:1(方)
reference_video:                 # 留空时自动扫描项目根 reference/
  path: ""
brief: ""                       # 广告/视频文本文件路径（.txt/.md）：写明用途+核心诉求
                                #   留空则用下面 brief_text 内联文本
brief_text: ""                  # 或直接内联一段文本（brief 留空时用这个）
images:                         # 图片素材（至少 1 张：产品图/人物图，100% 展示不改）
  - path: ""
    name: ""                    # 素材名（留空则用文件名）
    role: ""                    # 可选：product(产品) / person(人物) / logo / scene
    view: ""                    # 商品视角：front / back / side
    sku: ""                     # 可选；多图填写时必须一致
rights:
  source: ""                    # 来源/权利依据，如 user_owned / licensed
  declared_by: ""               # 声明人
  usage: ""                     # 允许用途
"""


_VIDEO_EXT = {".mp4", ".mov", ".m4v", ".webm", ".avi", ".mkv"}


def _resolve_material_path(raw, root: Path) -> Path:
    path = Path(str(raw or "").strip()).expanduser()
    return path if path.is_absolute() else root / path


def _scan_files(folder: Path, extensions: set[str]) -> list[Path]:
    if not folder.is_dir():
        return []
    return sorted(p for p in folder.rglob("*")
                  if p.is_file() and p.suffix.lower() in extensions)


def _video_resolution(path: Path) -> tuple[int, int]:
    """用 ffprobe 的 JSON 输出读取首条视频流尺寸；失败返回 (0, 0)。"""
    import subprocess

    try:
        result = subprocess.run(
            [media.ffprobe_bin(), "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=width,height", "-of", "json", str(path)],
            capture_output=True, timeout=60, check=False,
        )
        payload = json.loads(result.stdout.decode("utf-8", "replace") or "{}")
        stream = (payload.get("streams") or [{}])[0]
        return int(stream.get("width") or 0), int(stream.get("height") or 0)
    except (OSError, ValueError, subprocess.SubprocessError):
        return 0, 0


def _material_recommendations(blocking: list[dict]) -> dict:
    from .recommendations import build_recommendation

    return build_recommendation(
        node="N01_material_preflight",
        reason_code="MATERIAL_PREFLIGHT_BLOCKED",
        plain_reason="；".join(x["issue"] for x in blocking),
        evidence=["00_intake/preflight-report.yaml"],
        options=[
            {
                "id": "O1",
                "action": "补齐或更换缺失、不可读、权利不清的原始物料后重跑预检",
                "expected_visual_quality": "high",
                "product_fidelity": "high",
                "cost_delta": "low",
                "time_delta": "medium",
                "invalidates": ["N00", "N01"],
            },
            {
                "id": "O2",
                "action": "缩小镜头方案，移除无权或冲突素材；若关键要求无法保留则终止本次制作",
                "expected_visual_quality": "medium",
                "product_fidelity": "medium",
                "cost_delta": "low",
                "time_delta": "low",
                "invalidates": ["N01", "N02", "N06"],
            },
        ],
        recommended_option="O1",
        recommendation_reason="先修复输入能保留商品准确性与后续创作空间。",
        resume_from="N01_material_preflight",
    )


def intake_validate(inputs, out_dir, params, prompt_file=None) -> ToolResult:
    """00_intake — 登记参考片/商品图/文本，哈希并做三级物料预检。"""
    out_dir = Path(out_dir)
    root = out_dir.parent
    req_path = out_dir / "request.yaml"
    req = _load_yaml(req_path)
    if not req_path.is_file():
        _write(out_dir, "request.yaml", _REQUEST_TEMPLATE)
    aspect = media.normalize_aspect(str(req.get("aspect_ratio", "")).strip())
    blocking: list[dict] = []
    fixable: list[dict] = []
    advisory: list[dict] = []

    raw_images = [c for c in (req.get("images") or [])
                  if isinstance(c, dict) and str(c.get("path", "")).strip()]
    explicit_paths = {str(_resolve_material_path(c.get("path"), root))
                      for c in raw_images if str(c.get("path", "")).strip()}
    for path in _scan_files(root / "product", media.IMAGE_EXT):
        if str(path) not in explicit_paths:
            raw_images.append({"path": str(path), "name": path.stem, "role": "product"})

    images = []
    for n, c in enumerate(raw_images, 1):
        ip = _resolve_material_path(c.get("path"), root)
        if not ip.is_file() or ip.suffix.lower() not in media.IMAGE_EXT:
            blocking.append({
                "id": f"MAT-IMG-{n:03d}",
                "issue": f"商品图片找不到或格式不支持：{ip}",
                "impact": "无法确认商品外观与 SKU 一致性",
            })
            continue
        try:
            w, h = media.image_size(ip)
            digest = media.sha256_file(ip)
        except (OSError, RuntimeError) as exc:
            blocking.append({
                "id": f"MAT-IMG-{n:03d}", "issue": f"商品图片不可读：{ip}",
                "impact": str(exc),
            })
            continue
        images.append({"path": str(ip), "name": str((c or {}).get("name") or ip.stem),
                       "role": str((c or {}).get("role") or "").strip(),
                       "view": str((c or {}).get("view") or "").strip().lower(),
                       "sku": str((c or {}).get("sku") or "").strip(),
                       "width": w, "height": h,
                       "digest": digest, "sha256": digest})
    product_images = [im for im in images if im.get("role", "").lower() in ("", "product")]
    if not product_images:
        blocking.append({"id": "MAT-002", "issue": "缺少可读商品图片",
                         "impact": "无法建立商品保真展示路径"})

    reference_raw = req.get("reference_video") or ""
    if isinstance(reference_raw, dict):
        reference_raw = reference_raw.get("path", "")
    reference_candidates = []
    if str(reference_raw).strip():
        reference_candidates.append(_resolve_material_path(reference_raw, root))
    for path in _scan_files(root / "reference", _VIDEO_EXT):
        if path not in reference_candidates:
            reference_candidates.append(path)
    reference = None
    if reference_candidates:
        rp = reference_candidates[0]
        try:
            duration = media.video_duration_seconds(rp)
            width, height = _video_resolution(rp)
            digest = media.sha256_file(rp)
            if not rp.is_file() or duration <= 0 or width <= 0 or height <= 0:
                raise OSError("无法读取有效时长或视频分辨率")
            reference = {"path": str(rp), "duration_seconds": round(duration, 3),
                         "width": width, "height": height,
                         "digest": digest, "sha256": digest}
        except OSError as exc:
            blocking.append({"id": "MAT-001", "issue": f"参考视频不可读：{rp}",
                             "impact": str(exc)})
        if len(reference_candidates) > 1:
            advisory.append({"id": "MAT-009", "issue": "发现多个参考视频，仅登记第一段",
                             "impact": "其余参考片不会进入本次分析"})
    else:
        blocking.append({"id": "MAT-001", "issue": "缺少参考视频",
                         "impact": "无法分析原片节奏、结构与运镜"})

    brief_files = []
    raw_brief = str(req.get("brief", "")).strip()
    if raw_brief:
        brief_files.append(_resolve_material_path(raw_brief, root))
    for path in _scan_files(root / "brief", media.TEXT_EXT):
        if path not in brief_files:
            brief_files.append(path)
    brief_parts, brief_meta = [], []
    for n, path in enumerate(brief_files, 1):
        try:
            body = path.read_text(encoding="utf-8").strip()
            if not body:
                raise OSError("文本为空")
            digest = media.sha256_file(path)
            brief_parts.append(f"## {path.name}\n\n{body}")
            brief_meta.append({"path": str(path), "chars": len(body),
                               "digest": digest, "sha256": digest})
        except (OSError, UnicodeError) as exc:
            blocking.append({"id": f"MAT-BRIEF-{n:03d}",
                             "issue": f"文本文件不可读：{path}", "impact": str(exc)})
    inline = str(req.get("brief_text", "")).strip()
    if inline:
        brief_parts.append(f"## inline brief_text\n\n{inline}")
        inline_digest = media.sha256_bytes(inline.encode("utf-8"))
        brief_meta.append({"path": "(inline brief_text)", "chars": len(inline),
                           "digest": inline_digest, "sha256": inline_digest})
    brief_text = "\n\n".join(brief_parts)
    if not brief_text:
        blocking.append({"id": "MAT-003", "issue": "缺少商品文本或新视频要求",
                         "impact": "无法确定卖点、受众与成片目标"})

    rights_raw = req.get("rights") if isinstance(req.get("rights"), dict) else {}
    rights = {key: str(rights_raw.get(key) or "").strip()
              for key in ("source", "declared_by", "usage")}
    missing_rights = [key for key, value in rights.items() if not value]
    if missing_rights:
        blocking.append({"id": "MAT-006", "issue": "缺少完整权利声明",
                         "impact": "未声明 " + ", ".join(missing_rights) + "，不得进入制作"})

    skus = {im["sku"] for im in images if im.get("sku")}
    if len(skus) > 1:
        blocking.append({"id": "MAT-007", "issue": "商品图片存在 SKU 冲突",
                         "impact": "检测到多个 SKU：" + ", ".join(sorted(skus))})

    view_text = [(im.get("view", "") + " " + im.get("name", "")).lower()
                 .replace("-", " ").replace("_", " ")
                 for im in product_images]
    has_back = any(any(k in v for k in ("back", "rear", "背面", "后视"))
                   for v in view_text)
    has_side = any(any(k in v for k in ("side", "profile", "侧面", "侧视"))
                   for v in view_text)
    if product_images and not has_back:
        fixable.append({"id": "MAT-004", "issue": "缺少商品背面图",
                        "impact": "无法可信展示超过正面 60 度旋转"})
    if product_images and not has_side:
        fixable.append({"id": "MAT-005", "issue": "缺少商品侧面图",
                        "impact": "侧向运镜只能限制为近正面角度"})

    _write(out_dir, "brief.md", f"# 广告/视频文本\n\n{brief_text}\n")

    manifest = {
        "version": 2, "status": "intake_blocked" if blocking else "intake_validated",
        "aspect_ratio": aspect,
        "reference_video": reference,
        "brief": {"source": brief_meta[0]["path"] if brief_meta else "",
                  "chars": len(brief_text), "files": brief_meta},
        "images": images,
        "rights": rights,
    }
    _write(out_dir, "manifest.yaml", yaml.safe_dump(manifest, allow_unicode=True, sort_keys=False))

    result = "blocked" if blocking else ("conditional_pass" if fixable else "pass")
    preflight = {
        "result": result,
        "blocking_issues": blocking,
        "fixable_issues": fixable,
        "advisory_issues": advisory,
        "recommended_option": ("补齐阻塞物料与权利声明" if blocking else
                               ("补充背面与侧面商品图" if fixable else "继续进入需求分析")),
        "resume_from": "N01_material_preflight",
    }
    _write(out_dir, "preflight-report.yaml",
           yaml.safe_dump(preflight, allow_unicode=True, sort_keys=False))

    canvas = media.aspect_spec(aspect)["canvas"]
    _write(out_dir, "validation_report.md",
           "# 物料校验报告\n\n"
           f"- 预检结果：{result}\n"
           f"- 画幅：{aspect}（成片画布 {canvas[0]}x{canvas[1]}）\n"
           f"- 参考视频：{'已登记' if reference else '未登记'}\n"
           f"- 图片：{len(images)} 张\n"
           + "".join(f"  - `{im['name']}`（{im['width']}x{im['height']}"
                     + (f" · {im['role']}" if im['role'] else "") + "）\n" for im in images)
           + f"- 文本：{len(brief_text)} 字\n"
           + f"- blocking/fixable/advisory：{len(blocking)}/{len(fixable)}/{len(advisory)}\n")

    outputs = ["manifest.yaml", "validation_report.md", "brief.md", "preflight-report.yaml"]
    meta = {"step": "00_intake", "images": len(images), "aspect": aspect,
            "brief_chars": len(brief_text), "preflight_result": result}
    if blocking:
        meta["recommendations"] = _material_recommendations(blocking)
        return ToolResult(ok=False, outputs=outputs, error=media.err(
            "material_preflight_blocked",
            f"物料预检有 {len(blocking)} 个阻塞问题，已写入 preflight-report.yaml。",
            "按 recommendations 的推荐项补齐物料后，从 N01_material_preflight 重跑。",
        ), meta=meta)
    return ToolResult(ok=True, outputs=outputs, meta=meta)


_REQ_SCHEMA = {
    "purpose": "text",              # 广告 / 普通视频 + 一句话用途
    "video_type": "text",           # ad | general
    "selling_points": ["text"],     # 核心卖点（3~6 条）
    "audience": "text",             # 目标人群
    "tone": "text",                 # 基调/风格
    "cta": "text",                  # 行动号召文案（普通视频可留空）
    "duration_seconds": "number",   # 建议成片时长
    "key_message": "text",          # 一句话核心信息
}


def llm_analyze(inputs, out_dir, params, prompt_file=None) -> ToolResult:
    """01_analysis — LLM 读广告文本 + 图片清单，提炼需求，产需求理解书（等用户确认）。"""
    out_dir = Path(out_dir)
    manifest = _load_yaml(_find(inputs, "manifest.yaml") or Path("/nonexistent"))
    brief_path = _find(inputs, "brief.md")
    if not manifest or not brief_path:
        return ToolResult(ok=False, error=media.err(
            "missing_intake", "找不到上游 00_intake 的产物。", "先跑通 00_intake 并批准"))

    brief_text = Path(brief_path).read_text(encoding="utf-8")
    payload = {
        "brief": brief_text,
        "aspect_ratio": manifest.get("aspect_ratio"),
        "images": [{"name": im.get("name"), "role": im.get("role"),
                    "size": f"{im.get('width')}x{im.get('height')}"}
                   for im in manifest.get("images", [])],
    }
    instruction = _read_prompt(prompt_file) or (
        "你是资深广告策划。读广告/视频文本与图片清单，提炼创作需求。"
        "判断这是广告(ad)还是普通视频(general)。卖点具体可拍，别空话。"
        "CTA 是结尾行动号召文案；普通视频可留空。duration_seconds 给合理建议（广告常 15~30s）。"
        "只返回一个 JSON 对象，字段严格照 output_schema。")

    try:
        result = _semantic_call(instruction, payload, _REQ_SCHEMA,
                                "ad.requirements_analysis_requested",
                                "Analyze ad brief into structured requirements")
    except Exception as exc:  # noqa: BLE001
        return ToolResult(ok=False, error=media.err(
            "llm_config" if "config" in str(exc).lower() or "incomplete" in str(exc).lower()
            else "analysis_failed",
            f"需求分析失败：{exc}",
            "检查项目根 .env 的 LLM_BASE_URL / LLM_API_KEY / LLM_MODEL，或额度"))

    points = result.get("selling_points") or []
    if isinstance(points, str):
        points = [points]
    req = {
        "version": 1,
        "video_type": str(result.get("video_type", "ad")).strip() or "ad",
        "purpose": str(result.get("purpose", "")).strip(),
        "key_message": str(result.get("key_message", "")).strip(),
        "selling_points": [str(p).strip() for p in points if str(p).strip()],
        "audience": str(result.get("audience", "")).strip(),
        "tone": str(result.get("tone", "")).strip(),
        "cta": str(result.get("cta", "")).strip(),
        "duration_seconds": float(result.get("duration_seconds") or 20),
        "aspect_ratio": manifest.get("aspect_ratio"),
    }
    _write(out_dir, "requirements.yaml", yaml.safe_dump(req, allow_unicode=True, sort_keys=False))

    md = ["# 需求理解书\n",
          f"\n> 请确认方向对不对。不对告诉我哪里改。\n",
          f"\n**类型**：{'广告' if req['video_type']=='ad' else '普通视频'}",
          f"\n**用途**：{req['purpose'] or '（未提炼）'}",
          f"\n**核心信息**：{req['key_message'] or '—'}",
          f"\n**目标人群**：{req['audience'] or '—'}",
          f"\n**基调风格**：{req['tone'] or '—'}",
          f"\n**建议时长**：约 {int(req['duration_seconds'])} 秒 · 画幅 {req['aspect_ratio']}",
          f"\n**CTA**：{req['cta'] or '（无）'}\n",
          "\n## 核心卖点\n\n"]
    md += [f"{i}. {p}\n" for i, p in enumerate(req["selling_points"], 1)] or ["（未提炼卖点）\n"]
    _write(out_dir, "requirements.md", "".join(md))

    return ToolResult(ok=True, outputs=["requirements.md", "requirements.yaml"],
                      meta={"step": "01_analysis", "video_type": req["video_type"],
                            "points": len(req["selling_points"]),
                            "duration": int(req["duration_seconds"])})


_SB_SCHEMA = {
    "story": "text",                     # 视频故事线（2~4 句）
    "shots": [{
        "id": "text",                    # SH001 递增
        "type": "text",                  # generated | display
        "motion": "text",                # static | ken_burns | i2v（唯一视频路由权威）
        "duration": "number",            # 单镜秒数（4~15）
        "role": "text",                  # hook|feature|scene|cta|logo
        "product_ref": "text",           # display/i2v 用哪张图（图片 name；generated 可空）
        "beat": "text",                  # 这镜讲什么（对应哪个卖点/信息）
        "scene": "text",                 # 画面一句话
        "image_prompt": "text",          # 生成镜首帧 / 展示帧背景 的画面提示词
        "video_prompt": "text",          # 运动提示词（i2v 用）
        "overlay_text": "text",          # 叠加文字（卖点/CTA；无则空）
        "delivery_mode": "text",         # standard | single_take
        "product_overlays": [{            # single_take: 原图按时间贴入，不送生成模型
            "product_ref": "text",
            "start": "number",
            "end": "number",
        }],
        "text_overlays": [{               # single_take: 一条视频内的分段字幕
            "text": "text",
            "start": "number",
            "end": "number",
        }],
        "reference_video_url": "text",
        "reference_audio_url": "text",
        "reference_image_urls": ["text"],
    }],
}

_MOTIONS = {"static", "ken_burns", "i2v"}
_CLIP_MIN, _CLIP_MAX = 4, 15


def _clamp_dur(v) -> int:
    try:
        n = int(round(float(v)))
    except (TypeError, ValueError):
        n = 5
    return max(_CLIP_MIN, min(_CLIP_MAX, n))


def _timeline_seconds(value, default: float, duration: float) -> float:
    try:
        seconds = float(value)
    except (TypeError, ValueError):
        seconds = default
    return max(0.0, min(duration, seconds))


def _normalize_timeline(items: object, duration: float, *, product: bool) -> list[dict]:
    normalized = []
    if not isinstance(items, list):
        return normalized
    for item in items:
        if not isinstance(item, dict):
            continue
        start = _timeline_seconds(item.get("start"), 0.0, duration)
        end = _timeline_seconds(item.get("end"), duration, duration)
        if end <= start:
            continue
        if product:
            ref = str(item.get("product_ref", "")).strip()
            if ref:
                normalized.append({"product_ref": ref, "start": start, "end": end})
        else:
            text = str(item.get("text", "")).strip()
            if text:
                normalized.append({"text": text, "start": start, "end": end})
    return normalized


def _normalize_shots(raw_shots: list, image_names: set) -> list:
    """规整 LLM 出的镜头：补 id、校验 type/motion、clamp 时长、校验 product_ref。"""
    shots = []
    for n, s in enumerate(raw_shots, 1):
        if not isinstance(s, dict):
            continue
        sid = str(s.get("id") or "").upper().strip() or f"SH{n:03d}"
        if not sid.startswith("SH"):
            sid = f"SH{n:03d}"
        stype = str(s.get("type", "generated")).strip().lower()
        stype = "display" if stype == "display" else "generated"
        motion = str(s.get("motion", "")).strip().lower()
        if motion not in _MOTIONS:
            motion = "ken_burns" if stype == "display" else "i2v"
        ref = str(s.get("product_ref", "")).strip()
        if ref and ref not in image_names:
            ref = ""  # 引用了不存在的素材名 → 清空，gen 时兜底取第一张
        delivery_mode = str(s.get("delivery_mode", "standard")).strip().lower()
        delivery_mode = "single_take" if delivery_mode == "single_take" else "standard"
        duration = _clamp_dur(s.get("duration", 5))
        raw_reference_images = s.get("reference_image_urls")
        if not isinstance(raw_reference_images, (list, tuple)):
            raw_reference_images = []
        product_overlays = _normalize_timeline(
            s.get("product_overlays"), duration, product=True)
        product_overlays = [x for x in product_overlays if x["product_ref"] in image_names]
        text_overlays = _normalize_timeline(s.get("text_overlays"), duration, product=False)
        shots.append({
            "id": sid, "type": stype, "motion": motion,
            "duration": duration,
            "role": str(s.get("role", "")).strip(),
            "product_ref": ref,
            "beat": str(s.get("beat", "")).strip(),
            "scene": str(s.get("scene", "")).strip(),
            "image_prompt": str(s.get("image_prompt", "")).strip(),
            "video_prompt": str(s.get("video_prompt", "")).strip() or "cinematic subtle motion",
            "overlay_text": str(s.get("overlay_text", "")).strip(),
            "delivery_mode": delivery_mode,
            "product_overlays": product_overlays,
            "text_overlays": text_overlays,
            "reference_video_url": str(s.get("reference_video_url", "")).strip(),
            "reference_audio_url": str(s.get("reference_audio_url", "")).strip(),
            "reference_image_urls": [
                str(url).strip() for url in raw_reference_images
                if str(url).strip()
            ],
        })
    return shots


def llm_storyboard(inputs, out_dir, params, prompt_file=None) -> ToolResult:
    """02_storyboard — 按需求写故事 + 逐镜分镜，每镜标 generated/display + motion。"""
    out_dir = Path(out_dir)
    req = _load_yaml(_find(inputs, "requirements.yaml") or Path("/nonexistent"))
    manifest = _load_yaml(_find(inputs, "manifest.yaml") or Path("/nonexistent"))
    if not req:
        return ToolResult(ok=False, error=media.err(
            "no_requirements", "上游没有 requirements.yaml。", "先跑通 01_analysis 并批准"))

    images = manifest.get("images", [])
    image_names = {im.get("name") for im in images}
    payload = {
        "requirements": req,
        "aspect_ratio": manifest.get("aspect_ratio"),
        "images": [{"name": im.get("name"), "role": im.get("role"),
                    "size": f"{im.get('width')}x{im.get('height')}"} for im in images],
        "duration_seconds": req.get("duration_seconds", 20),
    }
    instruction = _read_prompt(prompt_file) or (
        "你是广告导演。按需求写一条视频故事线，并拆成逐镜分镜。"
        "每镜标 type：generated(AI 生成氛围/场景镜) 或 display(产品展示帧)。"
        "display 镜必须给 product_ref（图片 name），motion 用 static 或 ken_burns。"
        "motion 是视频路由的唯一权威；generated 默认 i2v，但明确需要定帧时可用 static。"
        "产品展示帧负责精确展示，生成镜负责动感/情绪。"
        "关键卖点和 CTA 优先用 display 镜保真展示，overlay_text 放卖点/CTA 文案。"
        "镜头总时长≈建议时长，单镜 4~15 秒。只返回一个 JSON 对象，字段照 output_schema。")

    try:
        result = _semantic_call(instruction, payload, _SB_SCHEMA,
                                "ad.storyboard_requested",
                                "Draft ad storyboard with shot types", max_tokens=6000)
    except Exception as exc:  # noqa: BLE001
        return ToolResult(ok=False, error=media.err(
            "storyboard_failed", f"分镜生成失败：{exc}",
            "检查 LLM 服务/额度；或改 prompts 后重跑"))

    shots = _normalize_shots(result.get("shots", []), image_names)
    if not shots:
        return ToolResult(ok=False, error=media.err(
            "no_shots_drafted", "LLM 没产出有效镜头。", "改 prompts 或重跑"))

    cap = media.max_shots()
    if cap:
        shots = shots[:cap]

    _write(out_dir, "shots.yaml", yaml.safe_dump({"shots": shots}, allow_unicode=True, sort_keys=False))
    story = str(result.get("story", "")).strip() or "（未产出故事线）"
    _write(out_dir, "story.md", f"# 视频故事\n\n{story}\n")

    total = sum(s["duration"] for s in shots)
    md = ["# 分镜脚本\n",
          f"\n故事：{story}\n",
          f"\n共 {len(shots)} 镜 · 总时长约 {total}s"
          + (f"（小样上限 AD_MAX_SHOTS={cap}）" if cap else "") + "\n\n",
          "| # | 类型 | 动作 | 时长 | 讲什么 | 画面 | 叠字 |\n|---|---|---|---|---|---|---|\n"]
    for s in shots:
        tag = "🖼展示" if s["type"] == "display" else "🎬生成"
        md.append(f"| {s['id']} | {tag} | {s['motion']} | {s['duration']}s | "
                  f"{s['beat']} | {s['scene']} | {s['overlay_text']} |\n")
    _write(out_dir, "storyboard.md", "".join(md))

    n_disp = sum(1 for s in shots if s["type"] == "display")
    return ToolResult(ok=True, outputs=["shots.yaml", "storyboard.md", "story.md"],
                      meta={"step": "02_storyboard", "shots": len(shots),
                            "display": n_disp, "generated": len(shots) - n_disp,
                            "total_seconds": total, "capped": bool(cap)})


def _image_provider():
    from mvstudio.providers.image_openai import OpenAICompatibleImageProvider
    return OpenAICompatibleImageProvider.from_env(os.environ)


def _product_path_for(shot: dict, images: list) -> Optional[Path]:
    """按 product_ref 找图；找不到就取第一张 role=product 的，再兜底第一张。"""
    ref = shot.get("product_ref")
    by_name = {im.get("name"): im for im in images}
    if ref and ref in by_name:
        return Path(by_name[ref]["path"])
    prods = [im for im in images if (im.get("role") or "").lower() == "product"]
    pick = prods[0] if prods else (images[0] if images else None)
    return Path(pick["path"]) if pick else None


def gen_keyframe(inputs, out_dir, params, prompt_file=None) -> ToolResult:
    """03_keyframes — generated 镜→AI 首帧；display 镜→产品原图贴 AI 背景（像素不动）。

    支持单镜/子集：params["only"] 给镜号集合时只出那几张，增量合并进 keyframes_index.yaml。
    """
    out_dir = Path(out_dir)
    only = (params or {}).get("only")
    shots = _load_yaml(_find(inputs, "shots.yaml") or Path("/nonexistent")).get("shots", [])
    if not shots:
        return ToolResult(ok=False, error=media.err(
            "no_shots", "上游没有 shots.yaml。", "先跑通 02_storyboard 并批准"))

    targets, not_found = _select_targets(shots, only)
    if only and not targets:
        return ToolResult(ok=False, error=media.err(
            "shot_not_found", f"点名的镜号在分镜里不存在：{', '.join(not_found)}",
            f"有效镜号：{shots[0]['id']}~{shots[-1]['id']}(共 {len(shots)} 镜)"))

    existing_index = _load_yaml(out_dir / "keyframes_index.yaml").get("keyframes", [])
    grid_path = out_dir / "storyboard_grid.png"
    if (not only and existing_index and len(existing_index) >= 2
            and not grid_path.exists()):
        grid_name = _compose_storyboard_grid(out_dir, existing_index)
        outputs_list = ["keyframes_index.yaml"]
        if grid_name:
            outputs_list.append(grid_name)
        return ToolResult(ok=True, outputs=outputs_list, meta={
            "step": "03_keyframes", "backfilled": True,
            "storyboard_grid": grid_name, "indexed": len(existing_index),
        })

    manifest = _load_yaml(_find(inputs, "manifest.yaml") or Path("/nonexistent"))
    images = manifest.get("images", [])
    aspect = manifest.get("aspect_ratio", media.DEFAULT_ASPECT)
    spec = media.aspect_spec(aspect)
    img_size, canvas = spec["image_size"], tuple(spec["canvas"])

    try:
        provider = _image_provider()
    except Exception as exc:  # noqa: BLE001
        return ToolResult(ok=False, error=media.err(
            "image_config", f"画面生成服务未配置：{exc}",
            "在项目根 .env 填 GPT_IMAGE_BASE_URL / GPT_IMAGE_API_KEY / GPT_IMAGE_MODEL"))

    quality = os.environ.get("GPT_IMAGE_QUALITY", "high").strip() or None
    bg_instruction = _read_prompt(prompt_file)  # image.background.md（背景生成基调）
    keyframe_prompt = (Path(prompt_file).parent / "image.keyframe.md") if prompt_file else None
    keyframe_instruction = _read_prompt(keyframe_prompt)

    by_id = {e["id"]: e for e in _load_yaml(out_dir / "keyframes_index.yaml").get("keyframes", [])
             if isinstance(e, dict) and e.get("id")}
    made, done, first_err = [], 0, None
    for s in targets:
        name = f"{s['id']}_keyframe.png"
        try:
            if s["type"] == "display":
                # 受控合成：AI 只画背景；产品素材不进生成模型，只做确定性缩放与 paste。
                product = _product_path_for(s, images)
                if not product or not product.is_file():
                    first_err = first_err or f"{s['id']}: 找不到产品图"
                    continue
                bg_prompt = (bg_instruction + "\n" if bg_instruction else "") + \
                    f"广告背景场景（不含任何产品/主体，纯背景）：{s.get('image_prompt') or s.get('scene')}"
                bg_bytes = provider.generate(bg_prompt, size=img_size, quality=quality)
                source_digest = media.sha256_file(product)
                data = media.compose_product_on_background(bg_bytes, product, canvas)
            else:
                # 生成镜：AI 画首帧（可选产品参考，允许漂移）
                ref = _product_path_for(s, images)
                refs = [str(ref)] if (ref and ref.is_file() and s.get("product_ref")) else []
                prompt = ((keyframe_instruction + "\n") if keyframe_instruction else "") + \
                    (s.get("image_prompt") or s.get("scene") or "cinematic scene")
                raw = provider.generate(prompt, references=refs, size=img_size, quality=quality)
                data = media.fit_image_to_canvas(raw, canvas)
            (out_dir / name).write_bytes(data)
            composite_digest = media.sha256_bytes(data)
            entry = {"id": s["id"], "keyframe": name, "type": s["type"],
                     "motion": s["motion"], "duration": s["duration"],
                     "video_prompt": s.get("video_prompt", ""),
                     "overlay_text": s.get("overlay_text", ""),
                     "delivery_mode": s.get("delivery_mode", "standard"),
                     "product_overlays": s.get("product_overlays", []),
                     "text_overlays": s.get("text_overlays", []),
                     "reference_video_url": s.get("reference_video_url", ""),
                     "reference_audio_url": s.get("reference_audio_url", ""),
                     "reference_image_urls": s.get("reference_image_urls", []),
                     "digest": composite_digest}
            if s["type"] == "display":
                entry["source_digest"] = source_digest
                entry["composite_digest"] = composite_digest
            by_id[s["id"]] = entry
            made.append(name)
            done += 1
        except Exception as exc:  # noqa: BLE001
            first_err = first_err or f"{s['id']}: {exc}"

    if done == 0 and not by_id:
        return ToolResult(ok=False, error=media.err(
            "keyframe_failed", f"首帧图全部失败：{first_err}", "检查图像服务地址/额度"))

    index = _rebuild_index(shots, by_id, "keyframe")
    _write(out_dir, "keyframes_index.yaml", yaml.safe_dump(
        {"keyframes": index}, allow_unicode=True, sort_keys=False))
    grid_name = _compose_storyboard_grid(out_dir, index)
    missing = [s["id"] for s in shots if s["id"] not in by_id]
    meta = {"step": "03_keyframes", "generated": done, "requested": len(targets),
            "indexed": len(index), "total": len(shots), "missing": missing,
            "storyboard_grid": grid_name}
    if first_err:
        meta["partial_error"] = first_err
    if not_found:
        meta["not_found"] = not_found
    outputs_list = ["keyframes_index.yaml", *made]
    if grid_name:
        outputs_list.append(grid_name)
    return ToolResult(ok=True, outputs=outputs_list, meta=meta)


def gen_video(inputs, out_dir, params, prompt_file=None) -> ToolResult:
    """04_shots — motion=i2v 走 Seedance；static/ken_burns 走本地 ffmpeg。

    支持单镜/子集：params["only"] 给镜号集合时只跑那几段，增量合并进 shots_index.yaml。
    Seedance 只按需初始化——纯本地镜（static/ken_burns）不碰付费服务。
    """
    out_dir = Path(out_dir)
    only = (params or {}).get("only")
    idx_path = _find(inputs, "keyframes_index.yaml")
    keyframes = _load_yaml(idx_path or Path("/nonexistent")).get("keyframes", [])
    if not keyframes or not idx_path:
        return ToolResult(ok=False, error=media.err(
            "no_keyframes", "上游没有关键帧。", "先跑通 03_keyframes 并批准"))
    kf_dir = idx_path.parent

    manifest = _load_yaml(_find(inputs, "manifest.yaml") or Path("/nonexistent"))
    aspect = manifest.get("aspect_ratio", media.DEFAULT_ASPECT)
    spec = media.aspect_spec(aspect)
    canvas, video_ratio = tuple(spec["canvas"]), spec["video_ratio"]

    targets, not_found = _select_targets(keyframes, only)
    if only and not targets:
        return ToolResult(ok=False, error=media.err(
            "shot_not_found", f"点名的镜号在关键帧里不存在：{', '.join(not_found)}",
            f"有效镜号：{keyframes[0]['id']}~{keyframes[-1]['id']}(共 {len(keyframes)} 镜)"))

    video_instruction = _read_prompt(prompt_file)  # video.motion.md（运动基调）
    needs_seedance = any(kf.get("motion", "i2v") == "i2v" for kf in targets)
    provider = model = None
    if needs_seedance:
        try:
            from mvstudio.providers.seedance import SeedancePort
            provider = SeedancePort.from_env()
            model = os.environ.get("SEEDANCE_MODEL", "").strip() or "doubao-seedance-2-0"
        except Exception as exc:  # noqa: BLE001
            return ToolResult(ok=False, error=media.err(
                "video_config", f"视频生成服务未配置：{exc}",
                "在项目根 .env 填 SEEDANCE_BASE_URL / SEEDANCE_API_KEY / SEEDANCE_MODEL"
                "（或把生成镜改成 display+static/ken_burns 走本地免费路径）"))

    by_id = {e["id"]: e for e in _load_yaml(out_dir / "shots_index.yaml").get("shots", [])
             if isinstance(e, dict) and e.get("id")}
    job_store = None
    jobs_by_shot: dict[str, dict] = {}
    if needs_seedance and (out_dir.parent / "state.json").is_file():
        from .jobs import JobStore
        from .recommendations import build_recommendation

        job_store = JobStore(out_dir.parent)
        estimate_raw = os.environ.get("SEEDANCE_ESTIMATED_COST", "").strip()
        try:
            estimated_cost = float(estimate_raw) if estimate_raw else None
        except ValueError:
            return ToolResult(ok=False, error=media.err(
                "bad_cost_estimate", "SEEDANCE_ESTIMATED_COST 不是有效数字。",
                "修正或删除该环境变量后，从 04_shots 重试。"))

        for kf in targets:
            if kf.get("motion", "i2v") != "i2v":
                continue
            edit_duration = _clamp_dur(kf.get("edit_duration", kf.get("duration", 5)))
            generation_duration = _clamp_dur(kf.get("generation_duration", edit_duration))
            request_contract = {
                "model": model,
                "prompt": ((video_instruction + " ") if video_instruction else "")
                + (kf.get("video_prompt") or "cinematic subtle motion"),
                "duration": generation_duration,
                "aspect_ratio": video_ratio,
                "first_frame_digest": kf.get("digest", ""),
                "reference_video_url": kf.get("reference_video_url", ""),
                "reference_audio_url": kf.get("reference_audio_url", ""),
                "reference_image_urls": kf.get("reference_image_urls", []),
            }
            job = job_store.prepare(
                node="N11", shot_id=kf["id"], provider_id=str(model),
                request=request_contract, estimated_cost=estimated_cost,
            )
            decision = job_store.authorize_submission(job["job_id"])
            if not decision.get("ok"):
                reason = (decision.get("error") or {}).get(
                    "message", "付费任务提交前被预算门禁暂停。")
                package = build_recommendation(
                    node=f"N11_{kf['id']}",
                    reason_code=str((decision.get("error") or {}).get(
                        "code", "BUDGET_BLOCKED")).upper(),
                    plain_reason=reason,
                    evidence=[f".adfilm/jobs/{job['job_id']}.yaml"],
                    options=[
                        {
                            "id": "O1", "action": "确认未知费用或提高 hard_limit 后继续提交",
                            "expected_visual_quality": "high", "product_fidelity": "high",
                            "cost_delta": "unknown", "time_delta": "low",
                            "invalidates": [f"N11_{kf['id']}", "N13", "N14"],
                        },
                        {
                            "id": "O2", "action": "保留已有镜头，把剩余镜改为本地 static 或 ken_burns",
                            "expected_visual_quality": "medium", "product_fidelity": "high",
                            "cost_delta": "none", "time_delta": "medium",
                            "invalidates": [f"N11_{kf['id']}", "N13", "N14"],
                        },
                        {
                            "id": "O3", "action": "停止后续生成并保留现有产物和任务记录",
                            "expected_visual_quality": "incomplete", "product_fidelity": "unchanged",
                            "cost_delta": "none", "time_delta": "none",
                            "invalidates": ["N13", "N14"],
                        },
                    ],
                    recommended_option="O1",
                    recommendation_reason="优先保留已确认画面路线和商品保真策略。",
                    resume_from=f"N11_{kf['id']}",
                )
                return ToolResult(
                    ok=False,
                    error=decision.get("error") or media.err(
                        "budget_blocked", reason, "处理建议后重试 04_shots。"),
                    meta={"step": "04_shots", "job": job,
                          "recommendations": package,
                          "exit_code": decision.get("exit_code", 2)},
                )
            jobs_by_shot[kf["id"]] = decision["job"]
    made, done, first_err = [], 0, None
    for kf in targets:
        kf_path = kf_dir / kf["keyframe"]
        out_name = f"{kf['id']}.mp4"
        edit_duration = _clamp_dur(kf.get("edit_duration", kf.get("duration", 5)))
        generation_duration = _clamp_dur(
            kf.get("generation_duration", edit_duration))
        if not kf_path.is_file():
            first_err = first_err or f"{kf['id']}: 首帧图缺失"
            continue
        motion = kf.get("motion", "i2v")
        try:
            if motion == "static":
                src = "static"
                if not media.still_to_mp4(kf_path, out_dir / out_name, edit_duration, canvas):
                    raise RuntimeError("静态定格 ffmpeg 失败")
            elif motion == "ken_burns":
                src = "ken_burns"
                if not media.ken_burns_to_mp4(
                        kf_path, out_dir / out_name, edit_duration, canvas):
                    raise RuntimeError("Ken Burns ffmpeg 失败")
            elif motion == "i2v":
                src = "seedance"
                from mvstudio.providers.seedance import SeedanceTask, SeedanceFrame
                data = kf_path.read_bytes()
                prompt = ((video_instruction + " ") if video_instruction else "") + \
                    (kf.get("video_prompt") or "cinematic subtle motion")
                task = SeedanceTask(
                    shot_id=kf["id"], model=model, prompt=prompt,
                    duration_seconds=generation_duration,
                    first_frame=SeedanceFrame(content=data, sha256=media.sha256_bytes(data)),
                    aspect_ratio=video_ratio, resolution="720p",
                    reference_video_url=kf.get("reference_video_url", ""),
                    reference_audio_url=kf.get("reference_audio_url", ""),
                    reference_image_urls=tuple(kf.get("reference_image_urls") or ()))
                job = jobs_by_shot.get(kf["id"])
                if job_store is not None and job is not None:
                    if not job_store.authorize_submission(job["job_id"]).get("submit"):
                        if (out_dir / out_name).is_file():
                            result = None
                        else:
                            raise RuntimeError(
                                "任务已提交或完成，但本地视频缺失；保留 job 后等待远程恢复能力")
                    else:
                        job_store.mark_running(job["job_id"])
                        result = provider.generate(task)
                else:
                    result = provider.generate(task)
                if result is not None:
                    (out_dir / out_name).write_bytes(result.video_bytes)
                    if job_store is not None and job is not None:
                        job_store.complete(
                            job["job_id"], actual_cost=getattr(result, "actual_cost", None))
            else:
                raise RuntimeError(f"不支持的 motion：{motion}")
            entry = {"id": kf["id"], "video": out_name,
                     "duration": edit_duration, "edit_duration": edit_duration,
                     "type": kf.get("type"), "source": src,
                     "overlay_text": kf.get("overlay_text", ""),
                     "delivery_mode": kf.get("delivery_mode", "standard"),
                     "product_overlays": kf.get("product_overlays", []),
                     "text_overlays": kf.get("text_overlays", [])}
            if motion == "i2v":
                entry["generation_duration"] = generation_duration
            by_id[kf["id"]] = entry
            made.append(out_name)
            done += 1
        except Exception as exc:  # noqa: BLE001
            if motion == "i2v" and job_store is not None:
                job = jobs_by_shot.get(kf["id"])
                if job is not None:
                    job_store.fail(job["job_id"], error={
                        "code": "video_generation_failed", "message": str(exc)})
            first_err = first_err or f"{kf['id']}: {exc}"

    if done == 0 and not by_id:
        return ToolResult(ok=False, error=media.err(
            "video_failed", f"视频全部失败：{first_err}",
            "本地镜查 ffmpeg；i2v 镜查 Seedance 地址/额度/模型名"))

    index = _rebuild_index(keyframes, by_id, "video")
    _write(out_dir, "shots_index.yaml", yaml.safe_dump(
        {"shots": index}, allow_unicode=True, sort_keys=False))
    missing = [kf["id"] for kf in keyframes if kf["id"] not in by_id]
    meta = {"step": "04_shots", "generated": done, "requested": len(targets),
            "indexed": len(index), "total": len(keyframes), "missing": missing}
    if first_err:
        meta["partial_error"] = first_err
    if not_found:
        meta["not_found"] = not_found
    return ToolResult(ok=True, outputs=["shots_index.yaml", *made], meta=meta)


_ASS_HEAD = """[Script Info]
ScriptType: v4.00+
PlayResX: {w}
PlayResY: {h}
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, Outline, Shadow, Alignment, MarginL, MarginR, MarginV
Style: Default,Noto Sans CJK SC,{fs},&H00FFFFFF,&H00202020,&H64000000,1,3,1,2,60,60,{mv}

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def _ass_ts(seconds: float) -> str:
    seconds = max(0.0, seconds)
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def _build_overlay_ass(windows: list, canvas: tuple) -> str:
    """windows: [(start, end, text)]。每镜 overlay_text 在该镜时间窗内显示。"""
    cw, ch = canvas
    fs = max(28, int(ch * 0.055))
    mv = int(ch * 0.10)
    lines = [_ASS_HEAD.format(w=cw, h=ch, fs=fs, mv=mv)]
    for start, end, text in windows:
        text = str(text).replace("\n", " ").strip()
        if text and end > start:
            lines.append(f"Dialogue: 0,{_ass_ts(start)},{_ass_ts(end)},Default,,0,0,0,,{text}")
    return "\n".join(lines) + "\n"


def _normalize_seg(src: Path, dst: Path, canvas: tuple, ff: str) -> bool:
    """把一段 mp4 归一成 canvas 尺寸/30fps/h264/无音轨，便于 concat。"""
    cw, ch = canvas
    scale = (f"scale={cw}:{ch}:force_original_aspect_ratio=increase,"
             f"crop={cw}:{ch},setsar=1,fps=30")
    ok, _ = media.run_ff([ff, "-y", "-i", str(src), "-vf", scale,
                          "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p", "-an", str(dst)])
    return ok and dst.is_file()


def compose(inputs, out_dir, params, prompt_file=None) -> ToolResult:
    """05_delivery — 按分镜顺序拼接片段，叠卖点/CTA 文字，出成片（用户画幅）。无音频。"""
    import tempfile
    out_dir = Path(out_dir)
    ff = media.ffmpeg_bin()

    si_path = _find(inputs, "shots_index.yaml")
    shots_idx = _load_yaml(si_path or Path("/nonexistent")).get("shots", [])
    if not shots_idx or not si_path:
        return ToolResult(ok=False, error=media.err(
            "no_videos", "上游没有视频片段。", "先跑通 04_shots 并批准"))
    shot_dir = si_path.parent

    manifest = _load_yaml(_find(inputs, "manifest.yaml") or Path("/nonexistent"))
    aspect = manifest.get("aspect_ratio", media.DEFAULT_ASPECT)
    canvas = tuple(media.aspect_spec(aspect)["canvas"])

    work = Path(tempfile.mkdtemp(prefix="compose-", dir=str(out_dir)))
    segments, windows, product_windows, t_cursor = [], [], [], 0.0
    images_by_name = {im.get("name"): Path(im["path"]) for im in manifest.get("images", [])}
    for s in shots_idx:
        src = shot_dir / s["video"]
        seg = work / f"seg_{s['id']}.mp4"
        if src.is_file() and _normalize_seg(src, seg, canvas, ff):
            segments.append(seg)
            seg_dur = media.video_duration_seconds(seg) or float(s.get("duration", 5))
            if s.get("delivery_mode") == "single_take" and s.get("text_overlays"):
                for overlay in s["text_overlays"]:
                    windows.append((t_cursor + float(overlay["start"]),
                                    t_cursor + float(overlay["end"]), overlay["text"]))
            elif s.get("overlay_text"):
                windows.append((t_cursor + 0.2, t_cursor + seg_dur - 0.2, s["overlay_text"]))
            for overlay in s.get("product_overlays", []):
                product = images_by_name.get(overlay.get("product_ref"))
                if product and product.is_file():
                    product_windows.append((product,
                                            t_cursor + float(overlay["start"]),
                                            t_cursor + float(overlay["end"])))
            t_cursor += seg_dur

    if not segments:
        import shutil as _sh
        _sh.rmtree(work, ignore_errors=True)
        return ToolResult(ok=False, error=media.err(
            "normalize_failed", "所有片段归一化失败。", "确认 ffmpeg 可用、镜头 mp4 有效"))

    body = work / "body.mp4"
    single_take = len(segments) == 1 and shots_idx[0].get("delivery_mode") == "single_take"
    if single_take:
        import shutil as _sh
        _sh.copy2(segments[0], body)
        ok, msg = body.is_file(), ""
    else:
        listf = work / "concat.txt"
        listf.write_text("".join(f"file '{p.name}'\n" for p in segments), encoding="utf-8")
        ok, msg = media.run_ff([ff, "-y", "-f", "concat", "-safe", "0", "-i", "concat.txt",
                                "-c", "copy", str(body)], cwd=str(work))
    if not ok or not body.is_file():
        import shutil as _sh
        _sh.rmtree(work, ignore_errors=True)
        return ToolResult(ok=False, error=media.err("concat_failed", f"拼接失败：{msg}", "检查 ffmpeg"))

    _write(out_dir, "overlay.ass", _build_overlay_ass(windows, canvas))
    final = out_dir / "final.mp4"
    vf = "subtitles=overlay.ass" if windows else None
    cmd = [ff, "-y", "-i", str(body)]
    if product_windows:
        for product, _, _ in product_windows:
            cmd += ["-loop", "1", "-i", str(product)]
        filters = []
        if single_take:
            clean_start = min(start for _, start, _ in product_windows)
            filters.append(
                f"[0:v]drawbox=x=0:y=0:w=iw:h=ih:color=0xF7F3EA:t=fill:"
                f"enable='between(t,{clean_start:.3f},{t_cursor:.3f})'[base0]")
        else:
            filters.append("[0:v]null[base0]")
        base_label = "base0"
        max_w, max_h = int(canvas[0] * 0.82), int(canvas[1] * 0.68)
        for index, (_, start, end) in enumerate(product_windows, 1):
            product_label = f"product{index}"
            next_base = f"base{index}"
            filters.append(
                f"[{index}:v]scale={max_w}:{max_h}:force_original_aspect_ratio=decrease,"
                f"setsar=1[{product_label}]")
            filters.append(
                f"[{base_label}][{product_label}]overlay=(W-w)/2:(H-h)/2:"
                f"enable='between(t,{start:.3f},{end:.3f})'[{next_base}]")
            base_label = next_base
        if vf:
            filters.append(f"[{base_label}]{vf}[captioned]")
            base_label = "captioned"
        cmd += ["-filter_complex", ";".join(filters), "-map", f"[{base_label}]",
                "-t", f"{t_cursor:.3f}"]
    elif vf:
        cmd += ["-vf", vf]
    cmd += ["-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p", "-an", str(final.name)]
    ok, msg = media.run_ff(cmd, cwd=str(out_dir))
    import shutil as _sh
    _sh.rmtree(work, ignore_errors=True)
    if not ok or not final.is_file():
        return ToolResult(ok=False, error=media.err("mux_failed", f"终混失败：{msg}", "检查 ffmpeg/字幕字体"))

    total = round(t_cursor, 1)
    n = len(shots_idx)
    n_disp = sum(1 for s in shots_idx if s.get("type") == "display")
    _write(out_dir, "delivery_report.md",
           "# 交付报告\n\n"
           f"- 成片：`final.mp4`（{aspect} / {canvas[0]}x{canvas[1]}）\n"
           f"- 时长：约 {total}s\n"
           f"- 生成方式：{'单次生成，不拼接' if single_take else '多镜拼接'}\n"
           f"- 镜头：{n} 段（展示帧 {n_disp} · 生成镜 {n - n_disp}）\n"
           f"- 产品原图贴入：{len(product_windows)} 处（原图未送入视频生成）\n"
           f"- 文字叠加：{len(windows)} 处（卖点/CTA，已烧入）\n"
           f"- 音频：无（当前版本纯画面+文字）\n")

    return ToolResult(ok=True, outputs=["final.mp4", "overlay.ass", "delivery_report.md"],
                      meta={"step": "05_delivery", "shots": n, "display": n_disp,
                            "overlays": len(windows), "product_overlays": len(product_windows),
                            "single_take": single_take, "seconds": total})
