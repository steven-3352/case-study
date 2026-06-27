# 动效技术可行性 · motion_tech_plan · W27D04

> 工种: 动效技术导演 · 触发原因: form_strategy 8 镜含 GSAP 动效 + 真实终端录屏 + countUp + stagger 弹幕墙
> 依赖: form_strategy ✓ · retention_beat_sheet ✓ · capture_frames.py 今日优化 ✓

## 适用性(逐镜数据杠杆已审)
见 form_strategy.md,本表只审"可不可行 + 资产是否就位"。

## 资产清单

### 真实素材(无需现做,已存在)
- `ops/metrics.csv` — 4 周弱播数据真实(可截图作镜 1 背景)
- `pipeline/p004_video/capture_frames.py` — 今天优化后并行截帧脚本(可录屏作镜 4 主信息)
- `git log` 含 `8e13d3c perf: P004 截帧并行 + 字幕去重,制作时间 ~3.4×` — 真实提交,作镜 4 证据

### 仿真但可控
- 镜 2 私信截图 × 3 张 — HTML+CSS 仿小红书/微信样式,**右上角常驻"示意"水印**(fact_check 红线)

### 字体 / GSAP
- 项目统一中文黑体 + 等宽数字字体(已就绪)
- GSAP timeline / countUp / stagger 已用于 D01/D03(可复用)

## 导出路径(稳定路线 · 截帧合成)
1. 每镜独立 HTML+GSAP 场景(`pipeline/p004_video/templates/d04_*.html`)
2. `capture_frames.py --all --workers 8`(今日已优化,3.4× 提速)
3. ffmpeg scene→mp4 → concat → compose(overlay 字幕 PNG 序列 + VO + BGM)
4. 字幕走 `d04_subtitles.html` overlay(透明帧,**复用今日 `__contentKey` 去重**,~6× 提速)

## 性能预估(用今日优化新管线)
- 总片长 ≈ 42s × 30fps = 1260 帧
- 主层 8 镜 1260 帧,并行 8 worker:**预计 60–80s**(对照 D03 86.6s)
- 字幕层 dedup 后实截 ~80 帧:**预计 10–15s**
- ffmpeg 编译 + concat + compose:~30s
- **截帧 + 合成总计预计 < 2.5 min**(全量 5 min 等级)

## 风险与控制

- **真实终端录屏(镜 4)的画面密度** — 控制:录屏前先精确演练每帧出现的命中信息(进度条 / git log / 时间数字),录屏速率 1× 不快放
- **私信仿真合规** — 控制:三张截图都不写真实店名/真名,只用泛化职业(餐饮老板/美容店主/教培负责人)
- **数据截图可读性** — 控制:9:16 小屏要清,把 metrics.csv 红色一片做成 zoom-in 强对比,核心数字(11/30/32)可读
- **报价表叠层** — 控制:99/299/599 大字横排,行业对比小字下排,逐张目视检查无遮挡
- **未使用 Three / Web3D** — 候选无,本条数据导向不需要 3D

## 门禁自检(content_form_split_gates §13.2)
- [x] 适用性:每镜声明数据杠杆,含数据杠杆词
- [x] 可读性:9:16 小屏文字/数字/动效路径清楚,单焦点不打散
- [x] 资产:真实素材 + 仿真素材 + GSAP 均就位
- [x] 导出:HTML+GSAP → capture_frames(并行)→ ffmpeg 稳定路径
- [x] 风险:复杂度 / 抢主信息 / 移动端观感 / 真实性逐项有控制
- [x] 无非法技术理由,每镜选型以数据指标为依据
