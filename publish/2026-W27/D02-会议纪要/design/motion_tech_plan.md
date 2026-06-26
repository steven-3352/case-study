# 动效技术审查 · motion_tech_plan · W27D02

> 选题: 开完会就走，纪要待办AI已发群 · 内容 ID: W27D02 · 工种: 动效技术导演
> 触发: GPT-image 真素材 + HTML/GSAP 叠动效卡 → render 前审查
> 结论: **可行**，GPT-image 出场景/角色（已实测 56s/张可用）+ p004(HTML+GSAP→截帧→mp4)叠文字卡。

## 0. 适用性 / 可读性
- **适用性：** 职场会议题材，真实场景插画 > 卡通圆脸，提升代入；文字卡(纪要/待办)用 HTML 保证中文清晰（GPT-image 中文渲染差，故文字一律 HTML 叠层）。
- **可读性：** 纪要/待办卡用 HTML 大字、卡片停留≥1s、与底图对比足；render 后抽帧验。

## 1. 实现路线
| 环节 | 用什么 |
|------|--------|
| 场景/角色素材 | **GPT-image-2**（urllib 直调 OPENAI_*，1024×1536，存 assets/characters/w27d02/） |
| 场景合成 | 每镜 HTML：GPT-image 图作全幅底图 + HTML/GSAP 叠纪要卡/待办@/提醒铃/大字 |
| 截帧/拼接/音画 | p004 capture_frames + build（VO=MiniMax · 字幕=_subtitles 帧 overlay） |

→ 不引新框架；**文字全走 HTML 层**，GPT-image 只出无文字插画。

## 2. 素材清单（GPT-image 真出图 · 必须入片）
| 文件 | 用途 |
|------|------|
| meeting_room.png | s1 散会场景底图 |
| tired.png / relaxed.png | s4 分屏对比 |
| me_phone.png | s5 自证 |
| test_worker.png / female_worker.png | s3 待办责任人头像 |
- 一致性：统一风格词「扁平矢量插画/明亮/无文字」；出图后人工筛。

## 3. 量化时序（30fps · GSAP 叠层）
| 镜 | 元素 | 时序 | ease |
|----|------|------|------|
| s1 | 群"叮"纪要卡 drop | 1.5–2.0s | back.out(1.7) |
| s1 | hook 大字 | 1.8–3.0s | back.out |
| s2 | 纪要卡逐行展开 | 3.5–10s | power2.out stagger .6 |
| s3 | 待办卡逐条@亮+铃 | 12–21s | back.out stagger 1.2，每条停留≥1s |
| s4 | 分屏 clip 滑入 | 22.5–24s | power2.out |
| s5 | 自证+CTA pop | 31/37s | back.out |

## 4. 风险/对策
| 风险 | 对策 |
|------|------|
| GPT-image 角色不一致 | 固定风格词；s3 头像小、影响低 |
| 中文渲染差 | 文字全 HTML 层，GPT-image 不出文字 |
| 卡片遮挡底图人物 | 卡片置屏侧/底，留人物可见；抽帧验 |
| 外网/中转超时 | 已实测可用；失败重试4次 |

## 5. 门禁
- [x] 适用性/可读性/资产/导出/风险齐 · GPT-image 实测可用 · 文字 HTML 层 · render 后抽 6 帧复验
