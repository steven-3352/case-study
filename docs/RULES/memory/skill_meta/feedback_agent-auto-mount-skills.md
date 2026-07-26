---
name: agent-auto-mount-skills
description: "agent 自主判断 skill 挂载 · 用户不指名 · 场景→skill 组合矩阵由 agent 内化;不问\"要不要挂 X\""
metadata: 
  node_type: memory
  type: feedback
  originSessionId: c911eb58-508b-4841-a096-7f34b2f414ea
---

**规则:** 在 case-study 项目里,agent 面对任何请求时,**skill 挂什么、什么时候挂,由 agent 自主判断**——从用户的自然语言请求推断场景,自动挂载对应 skill 组合,不要让用户说"用 X skill / 挂 X"。用户只描述**内容/意图/问题**,agent 负责翻译成 skill 组合。

**Why:** 2026-07-20 用户明确指出——上轮我给示例时写 "你可以说'挂 higgsfield-soul'"这类,把 skill 挂载责任推回用户,违背了 [[feedback_autonomous-data-driven]] 铁律(用户只出内容/反馈数据,agent 自己拍板)。skill 触发本来就是 Claude Code 按 description 匹配 + agent 主动加载的机制,不该退化为"用户手动点单"。

**How to apply:**

### agent 判断步骤(每次收到 i2v/视频相关请求先跑)

1. **识别场景类别**(从用户自然语言归类):

| 用户自然语言(节选) | 场景 | agent 自动挂 |
|---|---|---|
| "帮我做 XX 主题短片/视频" · "写这个镜头的 prompt" | 新建视频 prompt | `[[i2v-video-prompt]]`(主门必挂)+ 按形态匹配 `video-form-*`(cinematic/food-beverage/comic 等)+ `higgsfield-prompt`(MCSLA 元公式) |
| "这段视频不对/崩了/幻觉/脸变形/塑料感/AI 味重/相机不会动/僵硬" | 生成后诊断 | `[[i2v-video-diagnose]]`(项目版必挂 · 优先)+ 补充 `higgsfield-troubleshoot`(泛用补充) |
| "角色跨镜不一致/换了张脸/服装变/发型变" | 角色一致性 | `higgsfield-soul`(Soul ID)+ `higgsfield-character-design` + 项目铁律 [[project_shortfilm-memory-piece]](若涉本项目短片 IP) |
| "表情僵/情绪不到位/眼神空洞/嘴形对不上" | 表演/微表情 | `higgsfield-facs`(FACS 微表情)+ `[[i2v-video-diagnose]]` |
| "相机不会动/像 PPT/首尾帧几乎一样" | 相机运动缺失 | `higgsfield-camera` + `higgsfield-motion` + [[feedback_zoompan-visible-motion]] + [[feedback_camera-motion-vs-i2v-ceiling]] |
| "情绪化运镜/跟着音乐动/vibe" | 情绪运镜 | `higgsfield-vibe-motion` + `higgsfield-motion` + `higgsfield-audio` |
| "选哪个模型/grok 还是 seedance/kling 好还是 wan 好" | 模型选型 | `higgsfield-models` + [[project_p011-seedance-i2v-candidate]] + SYSTEM §4.2 五维打分 |
| "生成失败/API 报错/为什么 fail" | 系统级失败 | `higgsfield-troubleshoot` + [[feedback_read-env-example-first]] + [[feedback_gpt-image-model-fallback]] |
| "配音/BGM/音效怎么配" | 音画 | `higgsfield-audio` + templates/audio_plan.yaml + [[feedback_dense-vo-no-dead-air]] + [[feedback_dense-vo-no-bgm-default]] + [[feedback_sfx-layer-required.md]] |
| "拆分镜/一条视频拆几个镜头" | 分镜设计 | `higgsfield-shotlist-director` + 项目动画导演角色 + templates/design/motion_storyboard.md |
| "MCSLA 是什么/元公式" | 元公式深度 | `higgsfield-prompt` + `higgsfield` 主门 |
| "Cinema Studio/电影感/大片质感" | 电影视觉 | `higgsfield-cinema` + `video-form-cinematic` + `higgsfield-style` |
| "美食视频/ASMR/餐厅广告" | 美食形态 | `video-form-food-beverage` + `higgsfield-recipes`(不是菜谱是"预设配方")|
| "带货/电商/产品" | 商品形态 | `video-form-ecommerce-ad` + `video-form-product-360` + `higgsfield-marketing-studio` |
| 用户提到"Higgsfield workspace / photodump / credit / recall" | Higgsfield 平台耦合 | **跳过** — 项目不订阅 Higgsfield,`higgsfield-apps/workspaces/recall/stack` 忽略 |

2. **优先级(不改变)**:`i2v-video-prompt`(项目铁律)→ `video-form-{形态}`(形态)→ `higgsfield-{X}`(具体子能力)→ `higgsfield` 主门(元公式)

3. **绝不做**:
- ❌ 问用户"要不要挂 X skill?"
- ❌ 给用户列一堆 skill 让他挑
- ❌ 说"你可以说'用 XX'来触发"(违反自主铁律)
- ❌ 需要 skill 内某公式时不加载 skill,凭记忆写

4. **必须做**:
- ✅ 收到请求先分类场景 → 决定 skill 组合 → 静默挂载/加载后再回答
- ✅ 挂载多个 skill 时,给用户**成品**,不告诉过程("挂了这三个 skill 后…"这话别说,直接给答案)
- ✅ 挂错/漏挂的自我纠正 — 中途发现某场景该挂但没挂,静默补上继续做
- ✅ 场景不确定时倾向**多挂**(信息冗余无害)而不是不挂(容错优先)

**相关**:[[feedback_autonomous-data-driven]] · [[feedback_pre-node-checklist]] · [[project_higgsfield-mcsla-ecosystem-install]] · [[project_video-form-skills-full-install]]
