# 成片口播与音频验收 · W30D03

content_version: v2

> 对象：最终 `douyin/video.mp4`，48.73s。MiniMax `Chinese (Mandarin)_Sincere_Adult`，fallback: none。

| MP4 时间戳 | 口播/画面同步 | 结论 |
|---|---|---|
| 0.0–2.83s | 双轮实测钩子完整，首音从 0.0s 进入 | pass |
| 2.83–15.53s | 两种首答顺序与“只证明顺序变化”边界分镜对齐 | pass |
| 15.53–34.52s | 四个生存事实、两个目标边界、三个本周验证逐项高亮 | pass |
| 34.52–40.52s | 第十问完整说完，编辑补充标注常驻 | pass |
| 40.52–48.74s | 出口票、数字 CTA 和人类拍板边界未截尾 | pass |

- [x] AAC 48kHz mono；前 6s mean volume -17.5dB，全片 max -0.3dB，无削波门命中
- [x] 8 个语义 SFX 按真实 timing 混音，0 gap；无 >=3s 静音
- [x] 16 条 SRT 从 0.0s 覆盖到 48.74s，末句未截断
