---
name: feedback_ai-voice-known-gap
description: MiniMax 真诚青年 VO 听感偏 AI — 已识别 4 类破绽，暂不动，后面按触发条件再评估
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 3f745456-49f1-429e-9665-8b9c342c2ce6
---

**状态：** 已识别，**暂不动**（2026-07-04 用户拍板：先不动，记住问题，后面再决定）。

**破绽（4 类 · MiniMax speech-2.8-turbo Chinese_Sincere_Adult）：**
1. **无气口/无换气声** — 真人朗读每 5-8s 有一次可听换气；AI 全程零气口 → 一秒识破
2. **句末韵律固定下坠** — 每句结尾都是同样的降调收音；真人会因情绪、句意调整（疑问句上扬、共情句拖尾）
3. **情感跳变生硬** — s3(sad) → s4(neutral) 之间无过渡；真人靠语速微调 + 半秒停顿完成情绪切换
4. **过清晰连读** — 每个字都咬得很清楚；真人在快段会含糊、吞音、连读（尤其"prompt"这种外来词）

**参考对照：**
- WaytoAGI 主播：真人 + 后期磨音 · 有换气、有情感起伏、有含糊连读
- 七七：真人自录 · 女声偏干净但有明显气口和自然停顿
- 浙大猫学长：真人 + 略混响 · 有情绪、有笑声

**候选路线（暂存 · 触发再评估）：**

| 路线 | 成本 | 真实度 | 可复现 | 备注 |
|---|---|---|---|---|
| A · 用户自录 | 时间高 · 钱 0 | ★★★★★ | ★★☆☆☆ | 每条要重录；出镜/情感型值得 |
| B · MiniMax voice_clone（用户录 5-30 分钟样本） | 一次性中 · 后续 0 | ★★★★☆ | ★★★★★ | **推荐** · 一次克隆全 pipeline 复用 |
| C · ElevenLabs Instant Voice Clone | 订阅费 + 中转 | ★★★★☆ | ★★★★☆ | 英文更强 · 中文一般 |
| D · 只做后期（Adobe Podcast / 剪映去 AI 化滤镜） | 低 | ★★★☆☆ | ★★★★★ | 治标 · 破绽 3/4 仍在 |

**触发再评估条件（满足任一 → 重开决策）：**
- 投后数据显示某条完播/评论显著低，且用户评论出现「机器人/AI 味太重/听着假」等直指声音的反馈
- 用户主动愿意录一次 5-30 分钟样本（B 路线首要门槛）
- 出现声音关键度高的选题（情感叙事、真人自述、共情类）——需临时提级
- 新 TTS 供应商 / MiniMax 发布 speech-3 或类似升级，重新试听

**How to apply（当前）：**
- 继续用 `Chinese (Mandarin)_Sincere_Adult` + emotion/speed 精细化（这是目前能做到的最好）
- 不因"AI 味"单独退稿，除非触发条件已满足
- 若用户在具体一条视频上主动要求换声音，按"路线 B 优先"推进（问用户能否录样本）

**Related:** [[feedback_dense-vo-no-dead-air]] · [[feedback_dense-vo-no-bgm-default]] · [[feedback_read-env-example-first]]
