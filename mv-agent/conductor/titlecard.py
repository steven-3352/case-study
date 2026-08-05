"""标题卡桥接层：title_card.yaml（数据契约）→ paperdoll 引擎的大标题艺术字 Shot。

职责单一：只做「数据契约 → 引擎 Shot 参数」的翻译，不碰渲染、不碰 ffmpeg。
compose() 调它把 01_analysis 产的 title_card.yaml 翻成引擎能吃的 title-card spec。

契约（title_card.yaml）：
    version: 1
    art_style: 金墨朱砂
    opening: {title, subtitle}
    ending:  {title, subtitle, seal}

产物（title_cards.json）：引擎侧可直接构造 Shot 的最小字段集合。
留空字段一律不塞（引擎自带默认，行为不变）。
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional


def _load_yaml(path: Path) -> dict:
    """读 title_card.yaml。缺 pyyaml 时退化为极简解析（够读本契约的扁平结构）。"""
    text = Path(path).read_text(encoding="utf-8")
    try:
        import yaml
        data = yaml.safe_load(text) or {}
        return data if isinstance(data, dict) else {}
    except ImportError:
        return _mini_parse(text)


def _mini_parse(text: str) -> dict:
    """无 pyyaml 的兜底：解析两层缩进的 key: value（够本契约用）。"""
    root: dict = {}
    cur: dict = root
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip())
        key, _, val = line.strip().partition(":")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if indent == 0:
            if val == "":
                cur = {}
                root[key] = cur
            else:
                root[key] = val
                cur = root
        else:
            cur[key] = val
    return root


def _card(section: dict, mode: str, art_style: str) -> Optional[dict]:
    """把一节（opening/ending）翻成引擎 Shot 的 title-card 字段。
    无 title → 该卡不渲染（返回 None）。留空字段不塞（引擎用默认）。"""
    if not isinstance(section, dict):
        return None
    title = (section.get("title") or "").strip()
    if not title:
        return None
    spec: dict = {"title_mode": mode, "text": title, "art_style": art_style}
    subtitle = (section.get("subtitle") or "").strip()
    if subtitle:
        spec["subtitle"] = subtitle
    if mode == "ending":
        seal = (section.get("seal") or "").strip()
        if seal:
            spec["seal"] = seal
    return spec


def build_title_cards(title_card_yaml: Path) -> list[dict]:
    """读 title_card.yaml → 返回 title-card spec 列表（喂给 paperdoll 引擎构造 Shot）。

    每个 spec 是 Shot 的字段子集：{title_mode, text, art_style, [subtitle], [seal]}。
    opening/ending 无 title 的自动跳过。
    """
    data = _load_yaml(title_card_yaml)
    art_style = (data.get("art_style") or "金墨朱砂").strip() or "金墨朱砂"
    cards: list[dict] = []
    opening = _card(data.get("opening", {}), "opening", art_style)
    if opening:
        cards.append(opening)
    ending = _card(data.get("ending", {}), "ending", art_style)
    if ending:
        cards.append(ending)
    return cards
