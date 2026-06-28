# PUBLISH_LOG · W27D05

- **选题:** 「老板让我帮他招人回客户消息,我让他先看 3 个月群记录 — 数完那天他说不用招了」
- **形态:** 双平台同选题 · 抖音视频 + 小红书 8 张轮播(平台分轨)
- **状态:** ready_to_publish · 两道门 fail-closed 全过(forecast 内容 92 / 形式 90)
- **发布:** 抖音 2026-07-03 · 19:30 ｜ 小红书 2026-07-03 · 12:30

## 成片

### 抖音
- `douyin/video_with_bgm.mp4` · 41.8s · 1080×1920 · stereo 44.1k · VO MiniMax `Chinese (Mandarin)_Sincere_Adult` + BGM `assets/audio/hook_pack_01/我爱的女孩叫丫头-最终版本.mp3`(volume 0.22 · afade in 1.5s / out 2.0s,起始 0s 取 41.83s)+ HTML 字幕 overlay 烧录 · 实测峰差 VO -14dB / BGM -16.7dB
- `douyin/cover.png` @ 1.5s · "招人这件事 / 我建议你先别招" 反差大字 + 仿真群消息背景
- `douyin/publish.md` · 标题 / 正文 / CTA / 标签 / 合规自检全套

### 小红书
- `xhs/page_01..page_08.png` · 1080×1620 · P003 hybrid 模式(P01 GPT-image-2 报纸风 + P02-P08 Pillow 本地)
- `xhs/SCRIPT.md` · 8 张 caption + 留存节拍
- `xhs/publish.md` · 标题 / 正文 / 评论 CTA / 标签 / 测水统计板

## 反转架构(全片核心)
**老板第一反应"招人 ¥4500-6000"** → 90 天群记录 1247 条 → **真不一样的就 10 来类 · 头部 5 类占 7 成多** → **老板自醒"招人推迟 · 先做个表"** → 落点"你不是缺人 · 你是缺数据" + 测水"也想数"

## 与 D04 差异(防同质 · 核 SCRIPT_REJECT_LOG)
- **D04** = 自燃人设(资格质疑)→ 测水报价(¥99/¥299/¥599)
- **D05** = 数据让老板自醒(老板视角)→ 测水 Excel 模板
- 视觉锚:**真截屏 ≥ 60% 镜头**(s1 微信群瀑布 / s2 BOSS 直聘 / s3 微信 PC 端导出 / s5 微信群对话 / s7 Excel 模板)
- 颜色:全程黑底 / 纸色 · 强调红 #e53935 · 无 Dracula 紫/粉/青 · 通过 `gate_check_palette` 0.00%

## 门禁记录
- **pre_render:** PASS · 内容 92 / 形式 90(`design/pre_publish_forecast.md`)
- **palette gate:** PASS · 抖音 cover.png + 小红书 page_01..08.png 共 9 张全部 0.00% 蓝紫(阈值 5%)
- **approve:** PASS · 双平台素材逐张目视检查 → P06 修复 "人" 字加横线视错(变"大") · 改用红 ✗ 双对角线 · P05 修复 "迟" 字 PingFang bold 缺字 · 加 PingFang idx=2 自动回退
- **合规复检:** PASS · 数字区间 / 群截图打码 + 示意水印 / BOSS 直聘卡仿真 / 不卖 SaaS

## 已知取舍(如实登记)
1. **VO 41.8s 略超 35-45s 目标 · 略低于 D04 48.5s** — 实测 VO 41.82s + 0.3s 尾静音,按 D03/D04 策略"按实测 VO 拉伸"。s4 数据柱图 11.10s 是最长场,服务 7 成多反转情绪沉淀。
2. **"1247 / 10 来类 / 7 成多" 为某母婴店 90 天群消息归类示意 · 已脱敏** — 不出具体店名/老板名/手机号;`insights/fact_check.md` 红线全过。
3. **BOSS 直聘卡片 ¥4500-6000 为仿真区间** — 取自 BOSS 直聘母婴店客服公开行情,P02 标"招聘 APP 示意 · 不指代真实门店 · 已脱敏"。
4. **不卖 SaaS · 不卖 AI 客服 · 只发 Excel 模板** — 合规零风险路径;CTA "也想数 · 凑 10 个发模板" 是测水信号 + 私域承接物。
5. **微信群截屏 · 老板回复"招人推迟 · 先做个表"** — 仿真 · 标"示意 · 已脱敏" + 头像用 emoji。
6. **MiniMax 走 yunwu.ai `/minimax` 中转** — 抄自 D03/D04 sibling config(memory: `feedback_read-env-example-first`)· 声线 Sincere Adult 与"老板自醒"叙事契合。
7. **BGM 用项目自有素材 `assets/audio/hook_pack_01/我爱的女孩叫丫头-最终版本.mp3`** — 此前合成 BGM 经用户判定为"噪音不是 BGM"(见 `feedback_no-synth-bgm`),改用用户指定的真音乐文件。volume 0.22 让 VO 在前,起始 0s 取头 41.83s,1.5s fade-in / 2.0s fade-out。原 audio_plan 里的"我曾经的丫头.mp3"是失效引用 · 实际文件不在仓库,本条以新路径覆盖。

## 制作时间真实数据(对照 D04)
- 抖音 7 镜并行截帧 + 字幕层 dedup: ~35s(D04 commit 8e13d3c 优化效果延续)
- ffmpeg 合成 ~18s
- **抖音总制作时间 ≈ 55-65s**(D04 ~80-90s · 进一步压缩,因镜头 7 < D04 的 8)
- 小红书 carousel:封面 GPT-image-2 606s(本次较慢 · 平均 60-130s 区间偶发长尾)+ Pillow 7 张 ~2s + P06/P05 二次修缮各 ~0.3s = ~10 min(等 API)
- 文档总耗时: ~15 min(meta + 2 publish.md + SCRIPT + PUBLISH_LOG)

## P004 流水线复用(顺手)
- `--subtitle-template` 参数已在 D04 commit 8e13d3c 加入,D05 直接用 `d05_subtitles.html` 不踩"D04 烧成 D03 字幕"老坑。
- `gen_xhs_d05.py` 新增 `_draw_safe(...)` 缺字回退函数 · 抽到下条(D06+)可共享:Pillow + PingFang bold 缺 迟/远 等扩展汉字时自动用 idx=2 兜底。

## 投后待跑(L3)
- 48h/7d 回填 actual → `post_publish_retro` + 下条 `evolution_overlay`
- 重点验证(`pre_publish_forecast` 假设):
  1. **"招人这件事 / 我建议你先别招" 反常识钩 > D04 "涨粉为 0" 自燃钩** → completion_3s 应 ≥ 28%
  2. **"也想数" 3 字门槛 < D04 "档位号 + 行业" 8 字门槛** → 评论数应 ≥ D04
  3. **真截屏 ≥ 60% 镜头** → completion_rate 应 ≥ 30%
  4. 私域承接 "凑 10 发模板" 转化率 ≥ D04 "凑 10 做 demo"
- 失败容忍:若评论 < 5 → 数法测水赛道证伪,D06 切其他角度(选品 / 复购 / 库存 etc.)

## 系统进化(D05 新增固化)
- **Pillow 缺字自动回退 `_draw_safe`** — 列入 `pipeline/` 共享工具候选(D06+ 抽到 `pipeline/p004_video/gen_xhs_common.py`)
- **红 ✗ 双对角线 替代 横划线** — 「字符上画删除标」防视错教训(横线穿"人"变"大")· 写入 `templates/design/REJECT_LOG`(待补)
