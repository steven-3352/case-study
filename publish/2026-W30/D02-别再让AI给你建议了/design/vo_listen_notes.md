# 成片口播与音频验收 · W30D02

content_version: v3

> 对象：`douyin/video.mp4`，实测 52.48s。正式引擎 MiniMax `speech-2.8-turbo`，声线 `Chinese (Mandarin)_Sincere_Adult`，fallback: none。

## MP4 时间轴核验

| 时间戳 | 内容与音画检查 | 结论 |
|---|---|---|
| 0.0–6.30s | 首句从“半年后计划失败”起；逆向红线和具体事实逐步出现 | pass |
| 6.30–12.56s | 虚构计划三条输入事实进入，披露常驻 | pass |
| 12.56–19.29s | 普通问法已够严格，三项风险逐条出现 | pass |
| 19.29–27.39s | Round 1 原文短摘把失败原因接到事实或信息缺口 | pass |
| 27.39–34.88s | 双轮短哈希、原因/排序不同与窄结论同屏 | pass |
| 34.88–46.95s | 修订版 Prompt 完整展开，未单独 A/B 披露常驻 | pass |
| 46.95–52.48s | “小事别用”边界和四选一 CTA 完整说完 | pass |

## 声学检查

- [x] AAC 48kHz mono；整片综合响度 -17.35 LUFS，true peak -1.04 dBTP，无削波
- [x] 12 个本地 CC0 音效均按真实分段起点重排，0 个未解析事件
- [x] 无首尾死音；所有检测静音均 <0.75s，无 >=3s 静音死区
- [x] SRT 由真实 MiniMax timing 生成；Prompt 镜正文为主视觉，不叠烧录字幕

结论：机器声学与逐句时间轴验收 pass；主观听感由 Phase B 独立编剧/编导 reviewer 复验。
