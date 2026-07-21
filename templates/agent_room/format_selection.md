# [已废弃] 形式选型 · format_selection

> **2026-07-21 起废弃。** 本文件是 `templates/design/form_competition.md` 的早期草稿版本，
> 职责已完全被 `form_competition.md`（表现形式竞争·至少3方案跨家族比较）+
> `templates/design/form_strategy.md` 对应产出（逐镜表达方案·数据杠杆声明）取代。
> `pipeline/gate_check.py` 的 `check_form_competition()` / `check_form_strategy()` 门禁
> 也只认这两个文件路径，不读本文件。
>
> **不要新写内容指向本文件**，保留仅为历史存档（`publish/2026-W26/D02-团购回访/room/discussion.md`
> 等历史产出曾引用过）。新项目走 `templates/design/form_competition.md`。

---



## 本周已占用形式（防重复）

| 天 | 抖音 pipeline | 小红书 pipeline | 核心镜头语言 |
|----|---------------|-----------------|--------------|
| D01 美甲 | `render_evidence` F2 | `render_evidence` F1 短视频 | chat/table/terminal 链 |
| D02 团购 | **待填** | **待填** | **不得复制 D01** |

## 本条选型（W26Dxx）

### 形式选型师

- **render_route（抖音）:** `p004_gsap` | `render_evidence` | `p005_belt` | …
- **render_route（小红书）:** `p007_comic` | `p002_newspaper_gpt` | `carousel_html` | …
- **catalog 形式 ID（≥3，且单模板 ≤40% 时长）:**
  1.
  2.
  3.
- **与上一条差异点（必填）:** 

### 平台原生策划

| 平台 | 用户刷到时的「第一感」 | 完播/收藏机制 | 禁止 |
|------|------------------------|---------------|------|
| 抖音 | | | 与 D01 同结构 terminal→metric→CTA |
| 小红书 | | | 旧版 video 残留 |

### 动效分镜师 / 漫画分镜师

- storyboard 路径: `projects/{id}/storyboard.yaml`
- 参考模板: `pipeline/p004_video/templates/` 或 `p007_xhs_engine_comic/templates/`
- 禁用段落: flow 三步 pill + terminal「XX助手」+ metric 两周（若上条已用）

## 验收

- [ ] catalog ≥3 形式
- [ ] 与 week 矩阵不撞车
- [ ] cover 跟 pipeline 一致（非 render 默认回落）
- [ ] 形式选型师 + 导演签字
