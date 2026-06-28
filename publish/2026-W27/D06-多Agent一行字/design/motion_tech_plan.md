# motion_tech_plan · W27D06

## 适用性
HTML+GSAP 浅色模板 6 镜 · Playwright 截帧 · ffmpeg 合成。不依赖 Three.js。

## 可读性
1080×1920 大字 ≥46px · 一屏一主信息 · 字幕叠层 d06_subtitles.html。

## 资产
templates/d06_*.html · shared/gsap_helpers.js · vo_d06.mp3 · BGM hook_pack。

## 导出
capture_frames.py --storyboard storyboard_d06.yaml → build.py → w27d06.mp4

## 风险控制
禁 style.css 暗色族 · 首镜非黑底 punch · VO 实测拉伸 storyboard 时长 · 口播 BGM 0.08 不盖人声

## 性能
6 scene 并行截帧 ~34s · 总片 45.7s

## 数据指标（高级动效服务 · 服务 completion_3s / 完播 / 互动）
- 截帧成功率 100%（6/6 scene）· 保障 3s 停划素材不丢帧
- 单镜 PNG 1080×1920 平均 ~180KB · 大字可读性通过抽检
- ffmpeg 合成 w27d06.mp4 45.7s · 码率 ~2.1Mbps · 完播中段 gate 对比可辨
- 首镜非黑底 punch 通过 palette 抽检（浅色 #F8FAFC 主底）· 利于 3秒 留存

