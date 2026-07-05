#!/usr/bin/env python3
"""中文形容词/场景描述 → Freesound 英文检索词建议 (#70 · fetch_sfx.py 配套).

用途:
  audio_plan.yaml 写 sfx event 时, 声音设计师脑里是中文形容词("深夜安静的卧室"
  "关键数字落地重击")。本工具把中文描述映射成 Freesound 可直接检索的英文词组,
  并给出该音效应归入的 catalog 家族 (ambient/tick/whoosh/hit/riser)。

用法:
  python3 pipeline/sfx/search_keywords.py 深夜 卧室 安静
  python3 pipeline/sfx/search_keywords.py "大字落地重击"
  python3 pipeline/sfx/search_keywords.py --list          # 打印全部词表
  python3 pipeline/sfx/search_keywords.py --family hit    # 只看某家族词表

输出:
  每条匹配 → 英文 query (可直接喂 fetch_sfx.py 手动模式或 Freesound 网页搜索)

词典来源:
  assets/sfx/catalog.yaml freesound_search_hints + W28D05 gap report 关键词归纳。
  新家族/新形容词直接往 VOCAB 里加。
"""
from __future__ import annotations

import argparse
import sys

# (中文触发词元组, 家族, 英文 query)
VOCAB: list[tuple[tuple[str, ...], str, str]] = [
    # ═══ ambient · 环境铺底 ═══
    (("办公室", "白天", "上班"), "ambient", "office room tone daylight ambience"),
    (("深夜", "卧室", "安静", "静谧", "台灯"), "ambient", "quiet bedroom night late ambience"),
    (("清晨", "早晨", "鸟叫", "起床"), "ambient", "morning bedroom ambient birds distant"),
    (("咖啡厅", "咖啡馆", "人声"), "ambient", "coffee shop cafe ambience daytime"),
    (("户外", "街道", "城市"), "ambient", "city street ambience distant traffic"),
    (("雨", "下雨", "雨声"), "ambient", "rain on window interior ambience"),
    # ═══ tick · 拍点/打字/UI ═══
    (("轻拍", "轻点", "UI", "点击"), "tick", "subtle ui tap soft click"),
    (("键盘", "打字", "机械键盘"), "tick", "mechanical keyboard typing sequence"),
    (("单击", "按键"), "tick", "mechanical keyboard key single click"),
    (("回车", "确认键"), "tick", "keyboard enter key press"),
    (("节拍", "秒表", "倒计时", "计时"), "tick", "metronome tick soft"),
    (("手机", "推送", "通知", "消息"), "tick", "iphone notification sound soft"),
    (("相机", "快门", "截图"), "tick", "camera shutter click single"),
    # ═══ whoosh · 转场/进出 ═══
    (("转场", "过渡", "段间"), "whoosh", "whoosh transition swish soft"),
    (("快切", "滑入", "扫过"), "whoosh", "whoosh swipe fast transition"),
    (("气流", "掠过", "飞过"), "whoosh", "whoosh air pass transition"),
    (("翻页", "翻动"), "whoosh", "page turn paper flip"),
    # ═══ hit · 撞击/落地/强调 ═══
    (("落地", "重击", "砸", "大字"), "hit", "impact soft boom cinematic"),
    (("硬切", "撞击", "冲击"), "hit", "impact hard cut stinger"),
    (("深长", "低沉", "价值锚", "共鸣"), "hit", "impact deep resonance cinematic"),
    (("打勾", "勾选", "完成", "对号"), "hit", "soft click check mark ui"),
    (("打叉", "错误", "驳回", "叉号"), "hit", "error click ui cross"),
    (("金属", "锤"), "hit", "metal impact hit short"),
    # ═══ riser · 情绪拉升 (情感/带货型) ═══
    (("拉升", "紧张", "揭晓", "翻转", "升调"), "riser", "riser short ascending cinematic tension"),
    (("悬念", "屏息"), "riser", "suspense riser build up short"),
]

FAMILIES = ("ambient", "tick", "whoosh", "hit", "riser")


def match(words: list[str]) -> list[tuple[str, str, str]]:
    """返回 (命中触发词, family, query) 列表 · 按命中触发词数量降序."""
    scored = []
    for triggers, family, query in VOCAB:
        hits = [w for w in words for t in triggers if t in w or w in t]
        if hits:
            scored.append((len(hits), ", ".join(dict.fromkeys(hits)), family, query))
    scored.sort(key=lambda x: -x[0])
    return [(h, f, q) for _, h, f, q in scored]


def print_vocab(family: str | None = None) -> None:
    for triggers, fam, query in VOCAB:
        if family and fam != family:
            continue
        print(f"  [{fam:7s}] {'/'.join(triggers):30s} → {query}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("words", nargs="*", help="中文形容词/场景描述 · 可多个")
    ap.add_argument("--list", action="store_true", help="打印全部词表")
    ap.add_argument("--family", choices=FAMILIES, help="只看某家族词表")
    args = ap.parse_args()

    if args.list or args.family:
        print_vocab(args.family)
        return
    if not args.words:
        ap.print_help()
        sys.exit(1)

    results = match(args.words)
    if not results:
        print(f"无匹配 · 输入: {' '.join(args.words)}")
        print("建议: --list 看词表 · 或直接英译后上 freesound.org 搜 (filter CC0)")
        sys.exit(1)
    print(f"输入: {' '.join(args.words)}\n")
    for hit_words, family, query in results:
        print(f"  [{family:7s}] {query}")
        print(f"           命中: {hit_words}")
    print("\n下一步: 词组填入 catalog.yaml freesound_search_hints → python3 pipeline/sfx/fetch_sfx.py --family <家族>")


if __name__ == "__main__":
    main()
