# 形式策略 · form_strategy · T040 让AI说真话·致命漏洞法

> 工种:形式策略官
> 依赖:`design/motion_storyboard.md`(已完成,逐秒9字段)· `design/form_competition.md`(推荐路线 A+局部GSAP)· `assets/formats/catalog.yaml`(形式词汇)
> 目的:逐镜比较表达方案,声明**数据杠杆 / 理解成本 / 制作成本 / 技术风险**,铁律7(无 data_lever 的镜头不进成片)逐条自查

## 0. 入口必读打勾

- [x] `design/motion_storyboard.md` 已完成(风格判定=Vibe Motion改良 + 逐秒9字段)
- [x] `assets/formats/catalog.yaml` 已通读,catalog 内既有 id 优先引用,无匹配 id 时声明"自建场景"(非默认套用某历史 HTML 文件)
- [x] 铁律7自查:本文件每一镜必须能填出 data_lever,填不出的镜头标记退回 motion_storyboard 重设计
- [x] 按用户 2026-07-16 要求,本条不参照任何历史选题的 form_strategy 实例做借鉴

## 1. 逐镜形式声明

| 镜/秒段 | 选用形式(catalog id 或自建) | family | 数据杠杆(data_lever) | 理解成本 | 制作成本 | 技术风险 |
|---|---|---|---|---|---|---|
| ①钩子 0:00-0:02(夸夸截图快闪) | 自建:真实对话气泡快闪合成(非 catalog 既有 id,声明为新场景) | screen(改良,非品牌UI) | completion_3s(反差直给) | 低(截图内容一看即懂) | 低(静态图层+ffmpeg硬切) | 低(P001已验证) |
| ①钩子 0:02-0:04(大字砸入) | `punch_black`(catalog既有) | text_motion | completion_3s·收束 | 低 | 低 | 低 |
| ②揭矛盾 0:04-0:09(长文滚动) | 自建:HTML+GSAP timeline控速滚动真实文档(`capture_frames.py`确定性截帧机制,catalog无现成id,声明新场景;气质近 `broll_demo` 但机制不同——broll是真实项目画面,这里是真实API输出文档) | screen | 理解(信息量压迫感→坑很多的直觉)·信任(真实文本) | 中(需读一定信息量才get"多") | 中(需搭HTML渲染真实长文+GSAP timeline) | 中(滚动速度/时长精确对齐9s切点,需调校) |
| ③痛点 0:09-0:14(急停+红框+虚化) | 自建:帧锁接缝+红框定位虚化(与②同一场景延续,非独立新场景) | screen | 理解(致命点被淹没的可视化证明)·共鸣("我也没看到") | 低(红框直接指向,零学习成本) | 中(需精确帧锁+ CSS blur 蒙版调校) | 中(帧锁接缝拼接需像素级对齐,`[[feedback_frame-locked-seam]]`) |
| ④解法 0:14-0:16(真实打字闪回) | 自建:真实屏幕录制片段(raw,窄范围混用,非catalog screen family标准用法) | raw→screen | 信任("真操作过"的证明,静态合成无法替代) | 低 | 中(需真实录制+隐私裁切审核) | 中(隐私裁切合规是硬约束,需人工过目验收) |
| ④解法 0:16-0:21(GSAP指令卡) | `kinetic_typography`(catalog既有,气质吻合"文字随时间轴逐句弹出") | text_motion | 收藏(可抄指令,本条最强收藏杠杆) | 低(逐行清晰,截图友好) | 中(需逐句时间轴对齐+GSAP timeline调校,catalog原生标注) | 中(GSAP/Remotion时间轴,catalog原生标注tech_risk中——**触发motion_tech_plan门禁**) |
| ⑤实测打脸 0:21-0:23(分屏初现) | `before_after`(catalog既有,"反转、信任建立"与本镜意图完全吻合) | grid_compare | 信任·completion_rate(catalog原生标注) | 低(左右对切,直觉理解"对比") | 中(分屏合成+时间轴对齐) | 低 |
| ⑤实测打脸 0:23-0:26(左侧回顾) | `before_after`延伸(左栏内嵌②③素材的加速/灰度处理) | grid_compare | 理解(信息经济学,不重复占用完播时长)·防止"看起来像循环"的risk已在retention_beat_sheet §反同质硬规约束 | 低 | 低(素材复用,仅加变速+灰度滤镜) | 低 |
| ⑤实测打脸 0:26-0:29(右侧金句放大) | `before_after`延伸(右栏静态金句+`punch_black`式放大手法) | grid_compare + text_motion | completion_rate(完播顶点)·传播(可截图金句) | 低 | 低(文本卡+描边框) | 低 |
| ⑥分寸 0:29-0:31(标题转场) | `punch_black`(复用) | text_motion | 信任(反高潮,防止被判定"卖万能药") | 低 | 低 | 低 |
| ⑥分寸 0:31-0:34(两图标对照) | 近似 `agent_grid`("展示分工"→改为"展示两种使用场景对照",气质相通但非"分工/系统能力") | grid_compare(改良) | 理解(大赌/小赌两分寸一眼分清)·信任(接住88赞反对声,防翻车) | 低 | 低(线性图标+文字,无复杂动效) | 低 |
| ⑦CTA 0:34-0:36(指令卡再现) | `kinetic_typography`延伸(缩略复用④素材) | text_motion | 收藏(第二次收藏机会) | 低 | 低(素材复用) | 低 |
| ⑦CTA 0:36-0:38(评论区焦点框+问句) | 自建:评论区UI mock+`punch_black`式问句大字 | screen(改良)+text_motion | 评论(低门槛开放问句,互动杠杆) | 低 | 低 | 低 |

## 2. 铁律7自查(每镜必须有 data_lever)

全部 13 个子镜头段均已在上表填出明确 data_lever(completion_3s / 理解 / 信任 / 共鸣 / 收藏 / completion_rate / 评论),**无一处空白**——无 data_lever 的镜头不进成片,本条无需退回。

## 3. 制作成本/技术风险汇总(供动效技术导演接手)

- **低成本低风险(可直接执行,占大多数):** ①②局部/⑤大部分/⑥/⑦——沿用已验证的 P001 + ffmpeg 静态合成能力,无新依赖
- **中成本中风险(需专项技术方案,交 motion_tech_plan):**
  1. **②③帧锁接缝滚动**:HTML+GSAP timeline 控速滚动真实文档 + 9s 处像素级帧锁定格,与④走同一套`capture_frames.py`确定性截帧机制(2026-07-16 由 Playwright录制方案简化而来,见 motion_tech_plan §动效2 修正记录)
  2. **④GSAP 指令卡逐行打字机**:catalog 原生标注 `kinetic_typography` tech_risk=中,**本条使用 GSAP,已触发 CLAUDE.md 门禁"使用GSAP/复杂HTML动效但无motion_tech_plan→禁止render"**,下一步必须产出 `design/motion_tech_plan.md`
  3. **④真实打字闪回隐私裁切**:非技术难度,是**合规审核难度**——需人工逐帧过目确认无账号信息泄露,建议列入验收清单硬项(design_language §6 已列)

## 4. 与 form_competition 的一致性自查

- [x] 本文件的逐镜选型与 form_competition §7"分镜五维要点"结论一致(均落在方案A为骨架,④局部混C+GSAP,②③帧锁接缝技法)
- [x] 未出现与推荐路线矛盾的形式选择
- [x] catalog 既有 id 优先使用(`punch_black`/`kinetic_typography`/`before_after`/`agent_grid`改良),仅在 catalog 无对应机制时声明自建(②③④真实录制部分),未滥用"自建"逃避复用已验证能力

## 5. 交接下游

- **下一节点:** `design/motion_tech_plan.md`(④指令卡 + ②③长文滚动 均为 GSAP timeline 技术可行性审查,**必跑,已触发门禁**)
- 之后:`storyboard.yaml`(导演+摄像最终合成)
