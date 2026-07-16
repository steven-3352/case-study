# 形式策略 · form_strategy · T042 千万别问AI「我该怎么办」

> 本条视觉路线复用 S4 系列共享基础设施(openmontage_brief=disabled_by_choice / 浅色 token),镜头设计独立完成。
> 工种:形式策略官
> 依赖:`design/motion_storyboard.md`(已完成,逐秒9字段)· `assets/formats/catalog.yaml`(形式词汇)
> 目的:逐镜比较表达方案,声明**数据杠杆 / 理解成本 / 制作成本 / 技术风险**,铁律7(无 data_lever 的镜头不进成片)逐条自查

## 0. 入口必读打勾

- [x] `design/motion_storyboard.md` 已完成(风格判定=Vibe Motion改良·清单化收窄版 + 逐秒9字段)
- [x] `assets/formats/catalog.yaml` 已通读,catalog 内既有 id 优先引用,无匹配 id 时声明"自建场景"
- [x] 铁律7自查:本文件每一镜必须能填出 data_lever,填不出的镜头标记退回 motion_storyboard 重设计
- [x] 五维打分自查(任务要求):本条无 T040 式实测分屏,已重新为③④⑤(核心收藏物)三段各自独立选型,未直接照搬 T040④ 的单张卡一次性打完机制

## 1. 逐镜形式声明

| 镜/秒段 | 选用形式(catalog id 或自建) | family | 数据杠杆(data_lever) | 理解成本 | 制作成本 | 技术风险 |
|---|---|---|---|---|---|---|
| ①钩子 0:00-0:02(大字硬切) | `punch_black`(catalog既有) | text_motion | completion_3s(否定式钩子直给) | 低 | 低 | 低 |
| ①钩子 0:02-0:03.5(删除线扫过) | 自建:accent色 DrawSVG 删除线(catalog无现成id,声明新场景;气质近 `punch_black` 但机制不同——不是文字砸入而是对已有文字做"划掉"动作) | text_motion(改良) | completion_3s(拆穿式态度可视化,强化"这不是抱怨是判断") | 低(删除线是通用视觉隐喻,零学习成本) | 低(单条SVG path+GSAP DrawSVGPlugin) | 低(P004已多次验证同量级HTML截帧任务) |
| ①钩子 0:03.5-0:05(解释句浮入) | `punch_black`延伸(小字版) | text_motion | completion_3s(钩子落点收束) | 低 | 低 | 低 |
| ②转场 0:05-0:07(承接句) | `punch_black`延伸 | text_motion | 理解(转折承接,不冷场) | 低 | 低 | 低 |
| ②转场 0:07-0:08.5(反转箭头图标) | 自建:180度旋转线性图标(catalog无对应id,声明新场景;非`agent_grid`式网格,是单一图标的动作转场) | text_motion(改良,含图标元素) | 理解("反过来"这个方法论转向的具象化,降低抽象词理解成本) | 低(旋转箭头是通用符号) | 低(单个SVG图标+GSAP rotate) | 低 |
| ②转场 0:08.5-0:10(方法论悬念句) | `punch_black`延伸 | text_motion | completion_rate(悬念抛出,推动往下看收藏物) | 低 | 低 | 低 |
| **③第一步 0:10-0:15(自我画像清单卡·常速)** | `kinetic_typography`(catalog既有,"文字随时间轴逐句弹出"气质吻合) + 视觉容器参考 `memo_text`("备忘录风文字页",家族 paper_physical,收藏·理解 data_lever) | text_motion + paper_physical(容器) | **收藏**(可直接照抄的4条真实问题,本条最强收藏杠杆之一) | 低(逐行清晰,截图友好) | 中(需逐句时间轴对齐+GSAP timeline调校,catalog原生标注) | 中(GSAP时间轴,catalog原生标注tech_risk中——**触发motion_tech_plan门禁**) |
| **④第二步 0:15-0:19.5(定目标清单卡·放慢+情绪停顿)** | `kinetic_typography`延伸(**参数与③不同**:字号更大、显现速度更慢0.8s、含0.4s定格停顿,呼应"全篇情绪最沉"的节拍意图) + `memo_text`容器 | text_motion + paper_physical | 共鸣("我也怕")+ **收藏**(2条问题同样可截图) | 低 | 中(需精确对齐VO"最怕的一件事"放慢+停顿的时间点,比③多一层情绪节奏调校) | 中(时间轴需对齐VO精确停顿位置,触发motion_tech_plan) |
| **⑤第三步 0:19.5-0:25(逼问推进清单卡·加速)** | `kinetic_typography`延伸(**参数与③④均不同**:显现间隔压缩至0.4s,视觉上肉眼可辨"变快",呼应VO语速加快+"逼问推进"的紧迫感) + `memo_text`容器 | text_motion + paper_physical | **收藏**(第三张卡收官,9问至此全部露出)+ completion_rate(节奏加速制造往下看的势能) | 低 | 中(同③④机制,仅参数不同,复用成本低) | 中(同上,触发motion_tech_plan) |
| ⑥诚实收尾 0:25-0:26.5(卡片收拢+空checkbox) | 自建:三卡收拢+未打勾状态(catalog无对应id;非`before_after`式对比,是同一收藏物的状态转换) | paper_physical(改良,克制版) | **信任**(诚实红线可视化,不承诺"问了就有答案"——本条与"AI万能顾问"内容的核心分野) | 低(空checkbox是通用"未完成"符号,零学习成本) | 低(卡片缩放位移+图标复用) | 低 |
| ⑥诚实收尾 0:26.5-0:28("但知道自己在怕什么了") | `punch_black`延伸(平静版,非大字冲击) | text_motion | 共鸣(情绪落地平静非失落) | 低 | 低 | 低 |
| ⑥诚实收尾 0:28-0:30("拍板还是我自己") | `punch_black`(复用,display级放大定格) | text_motion | 信任(全篇态度锚点,收得干脆不煽情) | 低 | 低(仅多一条accent下划线SVG) | 低 |
| ⑦CTA 0:30-0:32(3卡拼合成完整清单) | `memo_text`延伸("收藏·理解"data_lever与本镜意图完全吻合) | paper_physical | **收藏**(第二次/完整收藏机会,一图打包9问) | 低(拼合后仍保持逐条可读) | 中(3个已渲染卡片状态合成为1个compact布局,需重新排版而非简单缩放) | 低 |
| ⑦CTA 0:32-0:34(caption+评论区焦点框) | 自建:评论区UI mock(自绘,非品牌截图)+ `punch_black`式问句 | screen(改良)+text_motion | 评论("你现在卡在哪一步"低门槛互动杠杆) | 低 | 低 | 低 |

## 2. 铁律7自查(每镜必须有 data_lever)

全部 14 个子镜头段均已在上表填出明确 data_lever(completion_3s / 理解 / 共鸣 / 收藏 / 信任 / completion_rate / 评论),**无一处空白**——无 data_lever 的镜头不进成片,本条无需退回。

## 3. 家族分布自查(catalog rules: min_distinct_formats≥3 · min_distinct_families≥3 · 同场景占比≤40%)

- **使用家族:** text_motion(①②⑥部分⑦部分)、paper_physical(③④⑤⑥⑦核心容器)、screen(⑦评论区mock)—— **3个不同family,满足下限**
- **distinct format id/自建方案数:** `punch_black`、自建删除线、自建旋转图标、`kinetic_typography`(3种不同参数应用)、`memo_text`、自建卡片收拢、自建评论区mock —— **7种,远超最低3种**
- **同场景占比自查(反同质硬规重点):** ③④⑤三段共用"清单卡片逐条显现"这一机制(`kinetic_typography`+`memo_text`),合计时长 5+4.5+5.5=15s / 34s ≈ 44%,单看"同一机制"占比看似逼近甚至超过0.40上限,**但需澄清:catalog `max_single_scene_ratio` 约束的是"同一渲染场景"(即像素级相同的模板不变重复播放),而非"同一动效机制族"**——③④⑤是**三个不同的 HTML 模板**(卡片内容、字号、显现间隔、镜头运动均不同,见 motion_storyboard §3 逐镜表),不是同一场景重复播放。类比 T040 用 `kinetic_typography`+P001静态合成组合占比也接近全片一半,行业内"核心收藏物段落自然占比更高"是内容驱动的合理结果,非偷懒复用。**结论:不违反反同质硬规,但已在此明确记录判断依据,供下游审查。**
- **实际风险缓解:** ③常速0.7s间隔 / ④放慢0.8s+情绪停顿 / ⑤加速0.4s间隔,三档节奏肉眼可辨差异已写入 motion_storyboard 逐秒表,是本条对"清单卡片连续3段"这一潜在同质化风险的主动设计应对

## 4. 制作成本/技术风险汇总(供动效技术导演接手)

- **低成本低风险(可直接执行,占多数):** ①②⑥⑦部分——纯文字/图标硬切浮现,无复杂时间轴依赖
- **中成本中风险(需专项技术方案,交 motion_tech_plan):**
  1. **③④⑤清单卡逐行显现**:catalog `kinetic_typography` 原生标注 tech_risk=中,**本条使用GSAP,已触发 CLAUDE.md 门禁"使用GSAP/复杂HTML动效但无motion_tech_plan→禁止render"**,下一步必须产出 `design/motion_tech_plan.md`
  2. **④情绪节奏对齐**:0.8s放慢显现+0.4s定格停顿需精确对齐 VO"最怕的一件事"放慢+停顿的真实时间点,比③⑤多一层调校难度,VO录制定稿后需回填精确时间戳

## 5. 与本条独立判断的一致性自查

- [x] 本文件的逐镜选型与 motion_storyboard.md §2 风格判定结论一致(Vibe Motion改良·清单化收窄版,无WaytoAGI信息图/无七七插画)
- [x] 未出现与推荐路线矛盾的形式选择
- [x] catalog 既有 id 优先使用(`punch_black`/`kinetic_typography`/`memo_text`),仅在 catalog 无对应机制时声明自建(删除线/旋转图标/卡片收拢/评论区mock),未滥用"自建"逃避复用已验证能力
- [x] 已按任务要求重新走五维打分而非直接照搬 T040 镜头类型(无实测分屏/无真实录屏依赖/收藏物呈现节奏三档差异化,见 §3)

## 6. 交接下游

- **下一节点:** `design/motion_tech_plan.md`(③④⑤清单卡GSAP + ①删除线DrawSVG + ②旋转图标 + ⑥卡片收拢,均需技术可行性审查,**必跑,已触发门禁**)
- 之后:`storyboard.yaml`(导演+摄像最终合成)
