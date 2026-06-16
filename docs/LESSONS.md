# 经验沉淀 · P001 及后续项目

> 每次改物料或收到平台数据后更新本文。执行依据见 [DECISIONS.md](DECISIONS.md) Q9。

---

## 2026-06-16 · 图文布局（小红书 story 首轮）

### 发现的问题

| 现象 | 根因 |
|------|------|
| 内容挤在顶部，下半屏大片留白 | 画布 1608px 高，实际内容只有 500–600px；`flex:1` 子元素未撑满 |
| 备忘录/收件箱像「空 App」 | 列表条目太少（6 条笔记、7 封邮件） |
| Analytics 像半成品 | 卡片堆叠后高度不足；`.fill { justify-content: space-between }` 在卡片**内部**制造假空白 |
| 结尾备忘录断层 | `margin-top: auto` 把提问框硬推到底，正文与 CTA 之间断开 |
| 统一 HTML 字卡 | 违反路线 1；像模版批量出图 |

### 有效做法（已写入 `gen_evidence.py`）

1. **画布**：图文与视频统一 **1080×1920（9:16）**（`screen_dims.py`）
2. **Shell 网格**：`status / main / tab / home` 固定高度分区；`main` 子节点加 `min-height:0`
3. **列表类**：条目数按行高反算，**铺满一屏**（备忘录 ~20 条、收件箱 ~17 封）
4. **Dashboard 类**：多加数据卡片（邮件漏斗、设备分布、页面洞察）；末卡不用 `space-between` 撑假空白
5. **体裁混搭**：≥3 种（备忘录 / Safari / 收件箱 / Analytics / 对比），禁统一页眉页脚
6. **三平台图文**：同套 `gen_evidence` 素材，按平台裁剪张数（见 `render_route1_carousel.py`）

### 仍须人眼验收

- 小字在信息流里是否可读（尤其 04 收件箱）
- 红圈标注是否像手写而非设计软件
- 各平台首图 3 秒内能否看懂冲突

### 2026-06-16 · 视频比例

| 问题 | 原因 | 修复 |
|------|------|------|
| 手机上看不全、画面被裁 | 非 9:16 画布 + `object-fit: cover` | 图文视频统一 **1080×1920** |

---

## 每日数据反馈 → 落地流程

```
你发各平台数据（模板见下）
    → 记入 ops/metrics.csv
    → 在本文「数据复盘」加一条
    → 能提炼的规则写进 DECISIONS / gen_evidence / 脚本
    → 下一批物料按新规则重出
```

### 你给我什么（复制改数即可）

```text
日期：YYYY-MM-DD
内容：P001 / 形态（如 xhs-story / douyin-video）

【小红书】
- 形态：图文 / 视频
- 曝光 / 阅读：
- 完播率（视频）：
- 赞 / 藏 / 评：
- 私信：
- 体感：哪张图/哪句好 / 哪块差

【抖音】
（同上字段）

【视频号】
（同上字段）

【一句话结论】
【下次想改什么】
```

### 数据写到哪里

- 结构化：`ops/metrics.csv`（列定义见 `ops/metrics.template.csv`）
- 分析与规则：`本文「数据复盘」章节`
- 视觉/流程硬规则：`docs/DECISIONS.md`

---

## 数据复盘

| 日期 | 内容 | 平台 | 关键信号 | 落地动作 |
|------|------|------|----------|----------|
| — | P001 首版未发 | — | — | 2026-06-16 完成路线 1 图文布局修复；待首发后填表 |

---

## 视频制作备忘（路线 1）

| 项 | 做法 |
|----|------|
| 画面 | `assets/broll/generated/` 仿真截图，`object-fit: contain` 完整入画 |
| 口播 | Edge TTS `zh-CN-YunjianNeural` |
| 画布 | **1080×1920（9:16）** 图文与视频同尺寸 |
| 时长 | 抖音 45–60s · 小红书 ≤60s · 视频号 60–90s |
| 禁止 | 黑金 slide、数字人、整段停一张静态字卡 |

生成命令：

```bash
python3 pipeline/gen_evidence.py
python3 pipeline/render_route1_carousel.py --all
python3 pipeline/render_p001.py --video douyin xhs channels
```
