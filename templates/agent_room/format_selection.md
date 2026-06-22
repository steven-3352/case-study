# 形式选型 · format_selection

> 工种: **形式选型师** + **平台原生策划** + **动效分镜师**（视频）/ **漫画分镜师**（轮播）
> 依赖: `insights/` 四件套 + `assets/formats/catalog.yaml`
> **门禁:** 未通过本表 → 禁止 week_build / render

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
