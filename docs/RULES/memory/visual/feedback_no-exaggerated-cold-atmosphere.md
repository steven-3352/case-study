---
name: feedback_no-exaggerated-cold-atmosphere
description: "温馨居家片段禁止刻意戏剧化\"冷\"（白呼气雾/怕冷缩脚/冷蓝阴影） · 冬季感够即可 · 主基调是暖"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 9b1fed5d-f0e8-44bb-92c5-cf637a4f1774
---

# 温馨片段禁刻意冷渲染

**用户 2026-07-12 原话**：不用刻意表现房间很冷。

## 规则

温馨居家/回忆类片段的 prompt 里禁止堆砌以下"冷戏剧化"元素：

- ❌ visible white breath puff（白呼气雾）· **静图 + 视频 motion 双禁**
- ❌ 广义"从嘴里出来的东西"：puff / vapor / steam / mist / smoke / exhale mist / white fog 全禁（2026-07-12 S01 视频踩坑：静图里 Grok 没渲染呼气雾，视频里却渲染出来了 — 用户看到"嘴里冒烟"直接退回重做）
- ❌ shivering / cold reflex（怕冷缩脚/搓手/发抖）
- ❌ THE ROOM IS COLD 类断言式描述
- ❌ pale silver-blue cold light dominating（冷蓝色调主导画面）
- ❌ "cold-room vs warm-quilt duality is the emotional key"（用冷暖反差作为核心情绪锚）

**视频层增补铁律**：所有 motion prompt 末尾必须加负面词 block：
```
IMPORTANT NEGATIVES: NO visible breath puff from mouth, NO white vapor,
NO steam or fog around lips, NO cigarette smoke, NO exhale mist,
NO cold blue tint on skin.
```
理由：Grok/AI 视频对"breath / cold air"关键词高度敏感，会自动加烟雾特效。静图 prompt 里删还不够，视频层要独立加负面词兜底。

## 允许保留

- ✓ 白空调挂机（作为道具存在，不写"OFF"红灯戏剧化）
- ✓ 冬季服装（棉睡衣/毛衣/被子）自然暗示季节
- ✓ 主暖色 + 少量冷色平衡（不是刻意反差）
- ✓ soft tungsten glow（暖床头灯）

## Why

用户对温馨/亲密类片段的期待是"quiet cozy indoor ambiance"，不是"冷得瑟瑟发抖里两人取暖"。前者是日常爱意，后者是求生剧。刻意冷戏（呼气冒雾+缩脚+冷蓝调）让镜头变戏剧化、不真实、破坏了温馨基调。

2026-07-12 S01/S02 静图里女主呼气冒雾、男主呼气冒雾、女主"cold reflex 抬脚"，全部踩了这条。用户看视频后立刻反馈。

## How to apply

- 温馨/亲密类片段 SCENE_ANCHOR 默认 "quiet cozy" 基调，不做 hot/cold duality
- 冬季片段只写季节感（服装/被子），不额外堆砌"how cold it is"
- 只有**情节明确需要冷**（如流浪、迷路、痛失挚爱在雪地）才允许刻意冷渲染
- 关联：短片《回忆·思念》 → [[project_shortfilm-memory-piece]]（本条 feedback 由该项目触发）
