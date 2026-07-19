# 成片口播与音频验收 · W30D04

content_version: v2

> 对象：最终 `douyin/video.mp4`，45.55s。MiniMax `Chinese (Mandarin)_Reliable_Executive`，fallback: none。

| MP4 时间戳 | 口播/画面同步 | 结论 |
|---|---|---|
| 0.0–5.92s | 同一条记录的两端冲突在前 3s 建立 | pass |
| 5.92–12.24s | journal 文件和 commit 两枚证物与“已落盘”对齐 | pass |
| 12.24–20.36s | SELF/规则/项目索引/当天标题四源按口播节奏扫描 | pass |
| 20.36–31.73s | 目标 journal 缺席与“仅本项目”边界完整 | pass |
| 31.73–45.55s | 共同可读面和入口名 CTA 完整说完 | pass |

- [x] AAC 48kHz mono；前 6s mean volume -17.5dB，全片 max -0.3dB
- [x] 13 个语义 SFX 按真实 timing 混音，0 gap；无 >=3s 静音
- [x] 14 条 SRT 从 0.0s 覆盖到 45.55s，末句未截断
