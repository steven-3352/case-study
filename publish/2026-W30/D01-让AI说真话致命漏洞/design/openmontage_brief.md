# OpenMontage 制作 brief · T040 让AI说真话·致命漏洞法

> 工种:OpenMontage 制作导演
> 状态:draft · 本条**必跑判断**(content v3/form v4 已重新评估，待独立复核)
> 依赖: `insights/` 已完成 · `design/retention_beat_sheet.md` · `script/脚本锦标赛_口播定稿v1.md`(v2 人话版采用)

## 0. 入口必读打勾

- [x] `docs/SYSTEM.md` §2.4b 生产 whitelist(含 OpenMontage)· §4.2 候选清单
- [x] `integrations/openmontage/README.md` 已实读(sibling repo 架构,不 vendor 进本仓)
- [x] **基础设施现状核实(2026-07-16 实测,不沿用任何历史条目结论)**:
  - sibling repo 已 checkout 于文档指定路径 `/Users/bubu/Documents/projects/OpenMontage` ✓
  - 当前系统用户 `bubu`,与文档路径一致 ✓
  - 已有 pipeline_defs 12 种(含 `screen-demo.yaml` real_capture/synthetic_terminal 双模式)
  - **本条独立评估结论不预设"过去阻塞过就还阻塞"或"基础设施好了就该用"——两种偷懒都不做,只看内容是否需要它**

## 1. 启用判断

```yaml
enabled: false
content_id: T040
platform: douyin + xhs
target_duration_s: 40
recommended_pipeline: native_p001_screenshot_compositing + p004_gsap_typewriter(局部)
render_runtime: ffmpeg + gsap_frame_render
budget_usd: 0
budget_mode: cap
target_metric: completion_3s + completion_rate + 收藏率(指令卡可读性是本条收藏物本体)
decision: disabled_by_choice
decision_review_trigger:
  - content_requires_ai_generated_cinematic_footage: true   # 若未来某镜需要"运镜/场景"而非"证据截图",重新评估
  - screen_demo_realcapture_proven_for_chat_ui: true         # 若 screen-demo real_capture 模式被验证适配聊天/API输出类静态截图(非活体app会话),可重估
```

### 判断结论

- **是否启用 OpenMontage:** 否
- **一句话理由:** 本条的核心资产**已经是真实的**(2026-07-16 用 claude-opus-4-8 + gpt-5.5 真实 API 跑出的输出文本),视觉命题是"把这份真实证据完整、清楚地给观众看",不是"生成一段有电影感的运镜"——OpenMontage 的核心增益(AI 生成运镜/形象/场景)在这条上没有用武之地。
- **服务的北极星指标:** completion_3s(0-3s匿名A/B选择)+ completion_rate(24-35s双轮结果与诚实边界)+ 收藏率(16-24s完整Prompt可读)
- **为什么当前项目原生路线够用:**
  1. 全片 8 段的核心画面是原文短摘、控制变量、虚构计划事实、完整 Prompt 和双轮短哈希，不需要生成场景；专属 HTML/GSAP 可以直接兑现这些证据关系。
  2. 唯一有"动效"诉求的一段(④指令卡逐行打字机)是纯排版动画,不涉及素材生成——HTML+GSAP(P004)的 TextPlugin/timeline 就能做,项目已装 GSAP skills,无新增依赖。
  3. Q9 铁律"真实画面是否更强"在本条几乎是压倒性的:观众要看的就是"AI 真的说了这句话",任何 AI 二次生成的运镜/画面都会稀释"这是真实验证过的方法"这个 core_message P0 主张,反而伤真实性。
- **为什么 OpenMontage 会更强(诚实评估,非回避):**
  - `screen-demo.yaml` 的 real_capture 模式擅长给"真实活体 app 会话"加专业 callout/zoom-crop——但本条没有活体会话要录,只有已产出的静态真实截图/文本,场景不匹配。
  - synthetic_terminal 模式做的是**终端窗口皮肤**的确定性打字动画——本条留存节拍表明确要求指令卡是"暖白高对比卡片",不是终端窗口皮肤;若强行套用会让本条平白多一层不必要的视觉语言,且指令卡内容(自然语言指令,非 CLI 命令)与"终端"这个意象本身就不搭。
  - 结论:内容本身不需要,不是"基础设施不够"、也不是"图省事不想学新工具"。

### 禁止理由自检(任一项为真则不得启用 · 本条自查)

- [x] 只是因为"更酷/更电影感/更高级"——不是,本条明确否定这个理由
- [x] 没有明确提升 completion_3s/completion_rate/理解/收藏/评论——是,评估后无提升点(见上)
- [ ] 会改写当前项目已通过的核心脚本或价值锚——不涉及(未启用)
- [ ] 只是简单图文轮播或大字卡片视频——不是唯一原因(本条有实测分屏这类信息密集镜,但仍判断原生路线更贴)
- [x] 当前 P001+P004 组合已能稳定完成且表现力足够——是

## 2. 本条独立结论(与基础设施状态无关)

基础设施解除阻塞不等于"该用"。本条经独立评估:**内容驱动的判断是 disabled_by_choice**,不是 blocked_infrastructure。若未来某条选题的视觉命题真的需要"生成一段场景/运镜"(比如需要一个不存在的虚拟空间),再重新评估启用。
