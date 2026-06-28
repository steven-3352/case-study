# motion_tech_plan · W27X06 · 轮播出图

## 适用性
Pillow 本地渲染 8 张 1080×1620 PNG · 不依赖 Playwright/GSAP 成片 · 演示工具为独立 HTML。

## 可读性
每页主标题 ≥48px 等效 · 一屏一主信息 · 示意水印 on 金额。

## 资产
`pipeline/p004_video/gen_xhs_d06.py` · `pipeline/demo_tools/quote_draft/index.html` · 字体系统默认 Pillow。

## 导出
```bash
python3 pipeline/p004_video/gen_xhs_d06.py
# → publish/.../xhs/page_01.png … page_08.png
```

## 风险
客户名/金额须标示意 · 禁绝对化用语 · P4-P5 为仿真 UI 非真录屏(可后续升级录屏替换)。

## 性能
8 页生成 <5s · 单页 ~45KB。

## 数据指标（服务 completion_3s / 看懂 / 收藏 / 评论）
- P1 封面大字对比度 ≥4.5:1 · 保障 3秒 停划
- P4-P5 工具 UI 双页 · 保障看懂率
- P6 字段表 6 行 · 收藏动机锚点
- P8 三选项 CTA · 评论互动门槛
