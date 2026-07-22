# content-engine · AI 内容生产引擎

**以后发布就发布本文件夹的内容。**

> **安装：** `git clone https://github.com/steven-3352/Tonbirds-Content-Engine-Plugin && cd Tonbirds-Content-Engine-Plugin && python3 setup.py`
> **当前版本：** 1.1.0 · 许可：MIT

---

## 什么是这个引擎

**三平面清晰分离**的内容生产引擎——流程控制器 / 能力技能 / 质量标准各司其职，互不混写。它是**各工种专家的集合**：你用大白话描述想要的效果，引擎自主设计脚本/风格/画面/分镜/每镜用哪几维，只跟你确认一次，之后无人值守做完。

| 平面 | 职责 | 本仓位置 |
|---|---|---|
| **流程（控制器）** | 谁先做、谁后做、依赖什么 | `docs/PROCESS.md` + `workflows/*.js` |
| **角色目录** | 27 工种的结构化 spec（单一事实源） | `roles/registry.yaml`（+ 派生 `registry.json`） |
| **技能（能力池）** | 出图 / i2v 视频 / TTS / 免费素材库 | `cap-*/` |
| **质量标准** | 判够不够格（单一事实源） | `quality/quality_registry.md` + `quality/video_19dim_scorecard.md` |
| **产出模板** | 各角色落地格式 | `templates/` |

---

## 快速开始

```bash
# 1. 首次自检（Python 版本 / pip 依赖 / ffmpeg / API key 就绪度）
python3 setup.py --env .env

# 2. 配置 API key
cp .env.example .env    # 然后填入各 cap 需要的 key（不用的 cap 留空即可）
```

**跑一个新选题（蓝图即合约）：**

1. **出蓝图** — 调 `workflows/blueprint.js`，args 传大白话描述（可多主题）：
   ```
   { briefs: ["我想做一条讲 AI 批量处理 Excel 的短视频，要有痛点共鸣", "..."] }
   ```
   它自主跑完理解→脚本→风格→形式→分镜，**返回**一份逐分镜大白话蓝图 + 每镜用到哪几维 + 集中的待拍板点（带推荐）。**不写盘、不自动续跑。**

2. **确认一次** — 主 LLM 把蓝图展示给你，你回「全部按推荐做」或指出要改的编号。

3. **无人值守制作** — 对每个定稿主题调 `workflows/prd_pipeline.js`，args 传 `{totalPRD, projectId, productionTier, formatType, overlays}`。制作段的机器门/质量门/闭环上限照常自动运行（不算人工干预），跑完交付可发布内容 + `publish.md`。

> 详见 `docs/PROCESS.md`「顶层模型：蓝图即合约」。

---

## 目录结构

```
skill/
├── LICENSE                      ← MIT
├── README.md                    ← 本文件
├── setup.py                     ← 首次环境自检（Python/依赖/ffmpeg/key）
├── .env.example                 ← API key 配置模板（按 cap 分组）
│
├── roles/                       ← 角色目录（单一事实源）
│   ├── registry.yaml            ← 27 工种结构化 spec（id/wave/activation/owns_dims/gates…）
│   └── registry.json            ← 派生 JSON（workflow 校验用）
│
├── workflows/                   ← 流程控制器
│   ├── blueprint.js             ← 预生产 + 蓝图组装（止于分镜，返回不续跑）
│   ├── prd_pipeline.js          ← 生产编排（全波次 · 确定性激活 · 独立验收）
│   └── validate.js              ← 一致性校验（镜像==json · gates/dims 无悬空）
│
├── templates/                   ← 各角色产出模板（17 个）
│   ├── subagent_prd_schema.md   ← 子 PRD 结构（observable_metric 禁效果名）
│   ├── anti_mediocrity_tournament.md · form_competition.md · motion_storyboard.md …
│   └── insights/                ← 洞察包 5 件（topic_brief/core_message/…/external_references）
│
├── quality/                     ← 质量标准（单一事实源）
│   ├── quality_registry.md      ← QG-* 门（14 机器 + 9 判断 + 6 结构）
│   └── video_19dim_scorecard.md ← 19 维打分卡（既是设计输入，也是验收表）
│
├── docs/
│   ├── PROCESS.md               ← 流程文档（蓝图即合约 · 引用 QG-ID 不复述阈值）
│   └── styles/                  ← 风格方法论（如 comic_music_mv.md）
│
├── cap-stock-footage/  cap-video-i2v/  cap-tts/  cap-image-gen/   ← 能力池
│
└── skills-manifest.json         ← 外部技能安装清单（用户自己确认安装）
```

---

## 能力清单（cap-*）

| skill | 能力 | provider | 状态 |
|---|---|---|---|
| `cap-stock-footage` | 免费素材库（拉竖屏 B-roll） | Pexels（CC0） | ✅ 已封装 |
| `cap-video-i2v` | i2v/t2v 视频生成 | Seedance（grok 待补） | ✅ 已封装 |
| `cap-tts` | 语音合成 | edge / minimax / volcengine | ✅ 已封装 |
| `cap-image-gen` | 通用出图（文生图 + 参考图驱动） | GPT-image-2 | ✅ 已封装 |

> **视频合成流水线**（帧+VO+BGM+字幕→成片）属流程平面的装配层，不是原子能力 skill，不在此目录。

---

## 角色目录（roles/registry.yaml）

- **27 工种**：理解 4 + 调研 1 + 核心 10 + 表达音画 5 + 增长复盘 1 + 带货扩展 4 + 出镜扩展 2。
- 每条含 `wave`（生产波次）、`activation`（always/video_only/on_demand/format:X）、`dual_review`、`translation_layer`、**`owns_dims`**（该角色在 19 维中负责设计的维度）、`gates`（须过的 QG-*）、`output_template`。
- **owns_dims 是"19 维成为设计输入"的机制**：workflow 把角色负责的维度 + 其「提升 3 档目标」注入该角色 prompt——角色一开工就知道自己该设计哪几维、按什么高度做，不是事后打分。
- workflow 内嵌 registry 镜像（沙箱无 fs），`workflows/validate.js` 守镜像 == `registry.json` 一致，防双写漂移。

---

## 质量标准（quality/）

- **表头元规则 QG-RAISE-3**：「门禁是地板不是目标 · 抬高 3 档再验收」——每道门放行前的校准镜。大模型太容易只做到及格分，本条 + owns_dims 注入是把及格分顶上去的两个抓手。
- **14 条机器门（fail-closed）**：QG-SCORECARD-90 / QG-PALETTE-NEON / QG-MEDIA-* / QG-MOTION-FREEZE / QG-FORM-* 等
- **9 条人/agent 判断门**：QG-ANTI-MEDIOCRITY / QG-FIVE-DIM / QG-FORECAST ≥B / QG-PRD-ACCEPTANCE 等
- **6 条门禁结构规则**：QG-TWO-GATES / QG-INSIGHT-3FACTS / QG-LOOP-LIMITS / QG-DELIVERY 等
- **19 维打分卡**：任意视频的设计 + 验证框架（不是某类视频专属）。设计时按 owns_dims 分派给角色，验收时逐维对照「提升 3 档目标」打分。

**改任何标准只改 `quality/`**，流程/代码/角色按 ID 引用。

---

## 外部技能（skills-manifest.json）

**licensing 策略：自有 skill 直接打包进引擎；别人的 skill 由用户自己确认安装。**

- ✅ 可安全安装：higgsfield（MIT 主包） · gsap-*（MIT） · ai-image-prompts-skill（MIT + LICENSE）
- ⚠️ 安装前需确认：higgsfield-* 子包（MIT 推定，子目录无独立 LICENSE）
- 🚨 使用前必须核查授权：`video-form-*`（15 个，完全无 license/source 记录）
- 🔧 随引擎自动装：i2v-video-prompt · i2v-video-diagnose（自建）

---

## 收录标准

| ✅ 能进这里 | ❌ 不进这里 |
|---|---|
| 自有代码 · 自洽可移植 · 参数化 · license 明确 | 绑死项目路径/文案的脚本 |
| | license 不明的外部 skill（改走 skills-manifest 引用） |
| | 私有选题/凭证/产出/material |

---

## 发布 / 更新

1. `node workflows/validate.js` 通过（角色/门/维度一致性）
2. 推送 GitHub：`git push origin main`
3. 打版本 tag：`git tag v1.1.0 && git push origin v1.1.0`
4. 用户获取最新版：`git pull`（已 clone）或重新 `git clone`

---

## 命名约定

- 能力单元前缀 `cap-`（capability）：自洽可移植的原子能力
- 角色 ID：`roles/registry.yaml` 的英文 `id`，workflow 内部引用永不改名
- 质量标准 ID `QG-<域>-<简名>`：全局唯一，只在 quality_registry.md 定义一次
- 19 维 ID `D01`–`D19`：只在 video_19dim_scorecard.md 定义一次
- 外部技能：在 skills-manifest.json 登记来源+license+安装命令，用户自装
