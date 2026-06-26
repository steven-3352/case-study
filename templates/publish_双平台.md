# 双平台发布模板（W27 起 · 日更 · 禁止三平台同稿）

> **节奏：** 抖音 + 小红书 **每天各 1 条**（本周 7+7=14 条）  
> **时间：** 小红书 12:30 · 抖音 19:30（可调，须写入 week.yaml）  
> 禁止 `video_reuse` · 禁止同题 mp4 直复用。

---

## 选题
- week_id: `2026-W27`
- project_id:
- topic_id:
- 平台: `douyin` | `xhs`（二选一或成对但独立生产）

---

## 抖音（仅当本周做抖音）

**标题（≤30字，冲突前置）：**

**简介：**（2–3行，第一人称，无术语）

**标签（3–5个，窄）：**

**规格：**
- 1080×1920 · **38–45s**（W26 均播未达标前上限）
- 前 1s 字幕钩子 · 单场景 · 原话进片 · 讨论型 CTA 完整进片

**门禁：**
- [ ] `retention_beat_sheet.md` 已填
- [ ] `content_version` / `form_version` 对齐 · 无 form>content 静默复用
- [ ] `gate_check(pre_render)` + `gate_check(approve)` PASS

---

## 小红书（仅当本周做小红书）

**标题（≤20字，收藏动机）：**

**正文：**（清单/复盘体，可稍长）

**标签：**

**规格：**
- **默认轮播** 6–8 张 · 封面生活感 · 标题含「可收藏」
- 禁止挂载抖音 `video.mp4`
- 漫画/报纸风须与选题强相关 · 非通用 newsprint 草稿

**门禁：**
- [ ] 独立 carousel brief · 无 dy 口播复用
- [ ] `pre_publish_forecast` 标「非 video_reuse」

---

## 发布后

1. 分平台 `content_id` 写入 `ops/metrics.csv`（例：`W27D01-DY` / `W27X01-XHS`）
2. 48h 填 `publish/{week}/performance_data.yaml`
3. 跑 `python3 pipeline/evolution_apply.py --week publish/{week}`
4. 弱信号对照 `ops/rules.yaml` R08–R12
