# 08 · 素材生命周期(长期知识 vs 可清理重资产)

> **目标:** 项目完成后保留可复盘、可迭代的知识资产;视频、图片、素材、音频等重资产归属到具体项目目录,允许按项目清理。
>
> **根本边界(§3.0):** 本仓库是工具 / 系统,不是用户数据的容器。用户每次生产的中间文件一律归属该用户项目目录,不与系统代码掺杂,更不落 `/tmp` 或系统级临时目录。

---

## 1. 长期保留

这些文件是系统能力和复盘依据,默认保留并入库:

| 类型 | 示例 |
|------|------|
| 设计文档 | `design/form_strategy.md`、`design/motion_tech_plan.md`、`design/pre_publish_forecast.md`、`design/post_publish_retro.md` |
| 内容文档 | `insights/`、`scripts/`、`retention_beat_sheet.md`、`audio_plan.yaml`、`storyboard.yaml` |
| 实现文档 | `format_spec.md`、`script_review.md`、`cover_review.md`、`vo_listen_notes.md` |
| 结构化数据 | `content.yaml`、`storyboard.yaml`、`performance.yaml`、`evolution_overlay.md` |
| 代码 | `pipeline/` 渲染器、公共组件、脚本、模板 HTML/CSS/JS |
| 公共能力 | 可复用模板、公共渲染器、公共规则、公共素材登记 `catalog.yaml` |

## 2. 可清理

这些文件是某次生产的重资产或中间产物,默认不入库,可按项目清理:

| 类型 | 扩展名 / 路径 |
|------|------|
| 视频 | `*.mp4`、`*.mov`、`*.webm`、`*.m4v` |
| 图片 | `*.png`、`*.jpg`、`*.jpeg`、`*.webp`、`*.gif` |
| 音频 | `*.mp3`、`*.wav`、`*.aiff`、`*.m4a` |
| 渲染中间物 | `pipeline/**/out/`、`publish/.staging/`、`**/_tmp/`、帧序列 |
| 下载素材 | 只服务单条内容的 B-roll、封面底图、TTS、临时截图 |

## 2.5 素材来源类型(五类 · 必须显式标注)

系统允许五类素材来源,`asset_strategy.md` / `asset_log.md` 必须标清:

| source_type | 含义 | 可用于 | 禁止 |
|---|---|---|---|
| `real_private` | 真实私域素材:真实截图、真实录屏、真实客户沟通、真实后台 | 证据、复盘、真实案例 | 未打码暴露隐私 |
| `public_reference` | 公开来源:公开视频、公开评论、公开报告、素材库 | 调研、benchmark、公开背景 | 不记来源、不管授权 |
| `generated_fact` | AI 生成事实型素材:虚构但合理的表格、聊天、日报、报价、业务数据样本 | 场景表达、案例演示、脚本叙事、画面素材 | 冒充真实客户/真实成交/真实后台/真实用户原话 |
| `synthetic_visual` | AI/代码生成解释性视觉:仿真界面、流程看板、动作计数器、AI B-roll | 帮观众看懂流程 | 伪造品牌/平台/客户身份 |
| `hybrid` | 真实结构 + 生成内容,或公开结构 + 生成字段 | 泛化案例、脱敏演示 | 混淆来源 |

**核心原则:事实可以生成,但来源不能伪造。**

`generated_fact` 是合法的一等素材来源,不是低级 fallback。它可以用于构造合理业务事实,但不得声称这些事实真实发生在某个客户或项目中。

## 3. 存放边界

### 3.0 铁律:系统 ≠ 用户数据(最高优先级)

**本仓库是工具 / 系统,不是用户数据的容器。** 用户每一次生产(某支 MV、某条内容、某个项目)产生的中间文件、产物、脚本、审批锚点,一律归属到**该用户项目自己的目录**,不得与系统代码、公共规则、公共模板掺杂在一起,更不得散落到系统级临时目录。

| | 系统 / 工具(本仓库) | 用户数据(用户项目) |
|---|---|---|
| 内容 | 渲染器、公共模板、公共规则、`docs/RULES/`、`pipeline/mv_engine/` 引擎代码、公共 skill | 某支片的分镜、素材、生成脚本、style-contract、approval JSON、帧、预览、成片 |
| 归属 | 仓库长期资产,跨项目复用 | 对应项目目录,随项目生灭 |
| 落盘位置 | 仓库对应模块目录 | `pipeline/voice_room/<片名>/`、`projects/{id}/`、`publish/{week}/Dxx-{slug}/` 之内 |

**硬性禁止:**

1. ❌ 把用户项目的任何产物写到 `/tmp`、`~/tmp`、系统级临时目录或仓库根散落 —— 这些位置一重启 / 一清理就没,审批锚点和可复现资产会永久丢失。
2. ❌ 把用户项目的生成脚本(`generate_*.py`、`assemble_*.py`、`run_*.py`)留在 `/tmp` —— 脚本属于该项目的可复现资产,进项目目录。
3. ❌ 把单个用户项目的素材 / 脚本 / 中间物混进系统公共目录(`pipeline/mv_engine/`、公共模板、`assets/broll/` 公共区)长期占位。

**唯一允许用 `/tmp` 的情形:** 引擎 / 工具自身在单次运行内开的 scratch(`mkdtemp()` 隔离目录、冒烟测试临时区),且**必须在运行结束时自清**;任何需要跨运行、需要复盘、需要审批留痕的文件都不属于此类。

**若发现用户产物已经落在 `/tmp` 或系统目录:** 先归位到对应用户项目目录,再清理,不得直接删。

### 3.0.1 用户项目目录约定(物料锚定 · 新项目强制)

**约定(owner 2026-08-05 拍板):新项目的"用户项目目录"= 用户原始物料文件所在的目录。**

不再由工具钦定一个固定路径(如 `mv-agent/projects/` 或 `pipeline/voice_room/`)。用户数据天然和用户物料在一起,顺势就和工具仓库分开——这正是 §3.0 的落地方式。

**执行规程:**

1. **开工第一步先确认物料在哪。** 任何新项目(mv-agent 线 G / 线 P 皆同)在建骨架前,先问清 / 定位用户的原始物料(音乐、歌词、人物图等)所在目录。
2. **那个目录就是用户项目根。** 骨架、分镜、keyframes、shots、审批 JSON、成片全部落在该目录下,不再复制到工具仓库内。
3. **物料散落多处时**,取其共同父目录,或与用户确认一个明确的项目根;不得默认落回工具仓库。
4. **工具仓库(本 repo)只出代码和公共资产**,不再接收新项目的用户数据。

**新旧分界(owner 明确):**

- **老项目维持现状,不迁**:`pipeline/voice_room/青衣`、`pipeline/voice_room/mingyue`、`mv-agent/projects/*`、`projects/P00x` 等既有项目原地不动,不做架构手术。
- **从下一个新项目起严格执行本约定。** 新项目一律物料锚定,不得再往 `pipeline/voice_room/<片名>/` 或 `mv-agent/projects/<name>/` 里建。
- 因此 §3.0 表格「落盘位置」列的 `pipeline/voice_room/`、`projects/{id}/` 等路径,仅对**存量老项目**有效;新项目以本节的物料锚定为准。

**工具支持(已落地 · 2026-08-05):** `mv-agent/conductor/cli.py` 的 `init` 已强制要求项目根参数:

```bash
python -m conductor.cli init <片名> <项目根>   # 项目根 = 物料目录,必填
```

- 缺参数直接报错,**不落回 `mv-agent/projects/`**——工具层面堵死"忘传参数就静默违规"。
- `init` 把「片名 → 项目根」记入 `mv-agent/projects/_registry.json`(工具指针元数据,非用户数据);之后 `status/run/ok/reject <片名>` 按片名查注册表定位,日常用法不变。
- 骨架、各步产物、`state.json` 全部建在项目根(物料目录)下,工具仓库不再接收新项目数据。

### 3.1 项目专属重资产

必须放在具体项目或发布包目录下:

```text
publish/{week}/Dxx-{slug}/assets/
publish/{week}/Dxx-{slug}/douyin/video.mp4
publish/{week}/Dxx-{slug}/douyin/cover.png
publish/{week}/Dxx-{slug}/xhs/
projects/{id}/assets/
projects/{id}/out/
```

项目结束后,以上目录中的视频、图片、音频、下载素材可以清理;文档和 yaml 保留。

每个发布包建议保留:

```text
publish/{week}/Dxx-{slug}/design/asset_strategy.md
publish/{week}/Dxx-{slug}/assets/asset_log.md
```

其中 `asset_strategy.md` 说明哪些素材已有、需要采集、允许生成、必须标示意;`asset_log.md` 记录实际素材来源、生成 prompt / provider / 成本 / 授权。

### 3.2 公共素材

`assets/broll/` 只保留两类内容:

1. `catalog.yaml`、`README.md`、授权/来源元数据等可复盘记录
2. 经确认可跨项目复用的公共素材

只服务单条项目的素材,不应长期停留在 `assets/broll/raw/`;应复制或移动到对应项目目录,并在文档里记录来源。

### 3.3 公共代码资产

`pipeline/**/templates/`、公共 JS/CSS、公共 Python 渲染器属于代码资产,保留。
`pipeline/**/out/` 是生成物,不保留。

## 4. 复盘依赖(清理前必须存在)

清理重资产前,必须确认这些文件已存在,保证后续补真实数据后仍能复盘:

- `insights/`
- `scripts/` 或 `script_vo.md`
- `retention_beat_sheet.md`
- `design/form_strategy.md`
- `design/motion_tech_plan.md`(若使用 Web 3D/GSAP/复杂动效)
- `projects/{id}/storyboard.yaml`
- `design/pre_publish_forecast.md`
- `design/post_publish_retro.md` 或待补位置
- `performance.yaml` / 平台 actual 数据入口

## 5. 清理原则

- 不删除文档、代码、yaml、json 元数据、来源记录
- 不删除公共模板和公共渲染器
- 不把单项目素材放进公共目录长期占位
- 不依赖视频/mp3/png 才能理解当时决策;文档必须能还原当时的假设
- 清理动作按项目目录执行,避免跨项目误删
- **不把用户项目产物写进 `/tmp` 或系统级目录**(见 §3.0);`/tmp` 只容许引擎单次运行的自清 scratch,任何需复盘 / 需审批留痕的文件一律进用户项目目录

---

## Source Map

- 原 `docs/ASSET_LIFECYCLE.md` 全文迁入
- 原 `docs/SYSTEM.md` §2.7 引用
