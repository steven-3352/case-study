---
name: gen-ui-avoid-blue-purple-gradient
description: gen_ui_wNNdNN.py 里禁用 linear-gradient 深蓝紫端；单色
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 3f745456-49f1-429e-9665-8b9c342c2ce6
---

# gen_ui HTML 禁蓝紫渐变（2026-07-05 D05 教训）

**规则：** `gen_ui_wNNdNN.py` 里 CSS `background` 禁用 `linear-gradient` 含蓝紫端色（`#0a0e1a` `#1a1a2e` `#0a0e14→#1a1a2e` 一类）· 用单色 `#0a0e14` 或 `#1a1611` 代替。

**Why:** 用户 D05 M3 `.left { background: linear-gradient(180deg, #0a0e1a 0%, #1a1a2e 100%); }` 触发 `gate_check_palette.py` 蓝紫占比 5.48% > 5% 阈值 FAIL。原因：`#1a1a2e` 落 HSL H≈240 蓝紫域。渐变从深黑过渡到蓝紫，中间过渡带全是蓝紫像素，占比不断累积。单色则无累积。违反 memory `feedback_no-neon-palette` "禁暖红→冷蓝渐变" 条。

**How to apply:**
- gen_ui 里所有 `linear-gradient` 出现时 · 检查两端色 · 若含 `#*[8-e][0-f]` 蓝端或 `#*[0-2][0-3]` 深紫端 · 换单色
- 首选单色：`#0a0e14`（近黑）· `#1a1611`（暖褐）· `#000000`（纯黑）
- `text-shadow` 也避开蓝色 rgba(100,150,255,*) · 换 rgba(200,180,150,*) 暖米
- 文案禁"屏幕蓝光"一类 · 改"改方案 / 疲惫"（视觉暗示会引导设计蓝色渐变）
- gen_ui 跑完立即 palette gate check 全 PNG · 不要等 render 后才发现（多花 render 一次）

**触发关键词：** 出现 `linear-gradient` in gen_ui · 出现 `#[0-2][0-9a-f][0-2][0-9a-f][2-9a-f][0-9a-f]` 蓝端 hex · 文案含 "蓝光/冷蓝/深夜屏幕"

**反例：**
- ❌ `linear-gradient(180deg, #0a0e1a 0%, #1a1a2e 100%)` (D05 M3 v1)
- ✅ `background: #0a0e14` (D05 M3 v2)
- ❌ `text-shadow: 0 0 30px rgba(100,150,255,0.35)` (蓝光晕)
- ✅ `text-shadow: 0 0 20px rgba(200,180,150,0.25)` (暖米晕)

**验证：** `python3 pipeline/gate_check_palette.py <PNG>` · 蓝紫占比 < 5% PASS · rendered mp4 也需 8+ 帧采样验证
