---
name: feedback_sfx-layer-required
description: sfx 是独立于 BGM 的必需音效层（whoosh/tick/hit/ambient 4 类）· 密 VO 型 BGM 可 off 但 sfx 不可 off · 万能公式 ambient+riser+hit
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 3f745456-49f1-429e-9665-8b9c342c2ce6
---

# sfx 音效层 · 独立必需（2026-07-05 · 寒林教剪辑吸收）

**规则：** audio_plan.yaml 里 sfx 是独立层，**与 BGM 分开决策**：
- BGM: 密 VO 演示/知识型默认 off，情感/出镜/带货型默认 on
- **SFX: 视频形态全都 on**（密 VO 型 BGM off 时更需要 sfx 撑节奏）

**Why:**
- 寒林教剪辑金句："画面是骨架，声音是灵魂" · "人脑对情绪的感知超过一半来自声音"
- 观众"感觉自然"vs"注意到音效本身"：sfx 音量必须比 VO 低 10-15 dB，让节奏被感知但不抢戏
- 密 VO 视频没有 BGM 铺氛围，全靠 VO 节奏；如果切场景/关键金句/CTA 也无 sfx，就是"干念"，完播必崩

**How to apply（每条视频形态选题）：**

1. **4 类 sfx 事件必须覆盖：**
   - `whoosh` · 每次场景切换（M1→M2 等）· 检索: whoosh / swoosh / swish / transition
   - `tick` · 文字/字幕/UI 出现 · 检索: UI tick / typewriter click / message tap
   - `hit` · 关键金句 / CTA / 反转打点 · 检索: impact / boom / stinger / hit
   - `ambient` · 全片/段落氛围铺底 · 检索: room tone / night city / office ambience

2. **万能公式**（寒林招 3）：`ambient 铺 + riser 推 + hit 落`
   - 找画面/节奏断点 → ambient 铺底 → riser 推起 → hit 打点
   - audio_plan.yaml 的 `sfx.formula_check` 三项必须 ≥2 项为 true

3. **音量分级**：
   - hit 最响：gain_db 不超过 VO -8dB
   - whoosh/tick: -12dB
   - ambient: -22dB
   - 全部走 `assets/sfx/*` 真素材（Freesound CC0 / Epidemic Sound）· 禁 ffmpeg aevalsrc/sine 合成

4. **检索技巧**（寒林招 4）：形容词 → 英文 → 搜库
   - 悬疑紧张 → tension riser / suspense build
   - 反转揭示 → impact hit / boom stinger
   - 界面进入 → UI whoosh in / pop in

5. **情感型/出镜型选题的 BGM 分支**（寒林招 1 · "先定情绪再选音乐"）：
   - `bgm.mood` → `bgm.genre_hint` 映射：
     - 高级冷静 → piano_ambient（钢琴+弦乐）
     - 活力动感 → electronic_upbeat（电子鼓）
     - 悬疑紧张 → tension_drone（弦乐持续+低频）
     - 温暖释放 → acoustic_warm（木吉他+钢琴）
   - 关注：节奏速度 · 乐器质感 · 氛围层次（不是"好听"）

**反例：**
- 密 VO 视频 BGM=off 但 sfx 也不做 → 完全干念，切场景无过渡 = fail
- ffmpeg aevalsrc 合成 whoosh → 假的，同 no-synth-bgm 铁律
- hit gain_db 设 -3dB（比 VO 更响）→ 观众"注意到音效本身"了

**相关 memory：** [[feedback_dense-vo-no-bgm-default]] [[feedback_no-synth-bgm]] [[feedback_dense-vo-no-dead-air]]
