# 资产生命周期 · 长期知识 vs 可清理重资产

> 目标：项目完成后保留可复盘、可迭代的知识资产；视频、图片、素材、音频等重资产归属到具体项目目录，允许按项目清理。

## 1. 长期保留

这些文件是系统能力和复盘依据，默认保留并入库：

| 类型 | 示例 |
|------|------|
| 设计文档 | `design/form_strategy.md`、`design/motion_tech_plan.md`、`design/pre_publish_forecast.md`、`design/post_publish_retro.md` |
| 内容文档 | `insights/`、`scripts/`、`retention_beat_sheet.md`、`audio_plan.yaml`、`storyboard.yaml` |
| 实现文档 | `format_spec.md`、`script_review.md`、`cover_review.md`、`vo_listen_notes.md` |
| 结构化数据 | `content.yaml`、`storyboard.yaml`、`performance.yaml`、`evolution_overlay.md` |
| 代码 | `pipeline/` 渲染器、公共组件、脚本、模板 HTML/CSS/JS |
| 公共能力 | 可复用模板、公共渲染器、公共规则、公共素材登记 `catalog.yaml` |

## 2. 可清理

这些文件是某次生产的重资产或中间产物，默认不入库，可按项目清理：

| 类型 | 扩展名 / 路径 |
|------|---------------|
| 视频 | `*.mp4`、`*.mov`、`*.webm`、`*.m4v` |
| 图片 | `*.png`、`*.jpg`、`*.jpeg`、`*.webp`、`*.gif` |
| 音频 | `*.mp3`、`*.wav`、`*.aiff`、`*.m4a` |
| 渲染中间物 | `pipeline/**/out/`、`publish/.staging/`、`**/_tmp/`、帧序列 |
| 下载素材 | 只服务单条内容的 B-roll、封面底图、TTS、临时截图 |

## 3. 存放边界

### 项目专属重资产

必须放在具体项目或发布包目录下：

```text
publish/{week}/Dxx-{slug}/assets/
publish/{week}/Dxx-{slug}/douyin/video.mp4
publish/{week}/Dxx-{slug}/douyin/cover.png
publish/{week}/Dxx-{slug}/xhs/
projects/{id}/assets/
projects/{id}/out/
```

项目结束后，以上目录中的视频、图片、音频、下载素材可以清理；文档和 yaml 保留。

### 公共素材

`assets/broll/` 只保留两类内容：

1. `catalog.yaml`、`README.md`、授权/来源元数据等可复盘记录。
2. 经确认可跨项目复用的公共素材。

只服务单条项目的素材，不应长期停留在 `assets/broll/raw/`；应复制或移动到对应项目目录，并在文档里记录来源。

### 公共代码资产

`pipeline/**/templates/`、公共 JS/CSS、公共 Python 渲染器属于代码资产，保留。  
`pipeline/**/out/` 是生成物，不保留。

## 4. 复盘依赖

清理重资产前，必须确认这些文件已存在，保证后续补真实数据后仍能复盘：

- `insights/`
- `scripts/` 或 `script_vo.md`
- `retention_beat_sheet.md`
- `design/form_strategy.md`
- `design/motion_tech_plan.md`（若使用 Web 3D/GSAP/复杂动效）
- `projects/{id}/storyboard.yaml`
- `design/pre_publish_forecast.md`
- `design/post_publish_retro.md` 或待补位置
- `performance.yaml` / 平台 actual 数据入口

## 5. 清理原则

- 不删除文档、代码、yaml、json 元数据、来源记录。
- 不删除公共模板和公共渲染器。
- 不把单项目素材放进公共目录长期占位。
- 不依赖视频/mp3/png 才能理解当时决策；文档必须能还原当时的假设。
- 清理动作按项目目录执行，避免跨项目误删。
