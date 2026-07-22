# content-engine · AI 内容生产引擎

**以后发布就发布本文件夹的内容。**

> **安装(发布后):** `/plugin install https://github.com/yourorg/content-engine-plugin`
> **当前版本:** 1.0.0 · 许可: MIT

---

## 什么是这个引擎

**三平面清晰分离**的内容生产引擎——流程控制器 / 能力技能 / 质量标准各司其职,互不混写:

| 平面 | 职责 | 本仓位置 |
|---|---|---|
| **流程(控制器)** | 谁先做、谁后做、依赖什么 | `docs/PROCESS.md` + `.claude/workflows/prd_pipeline.js` |
| **技能(能力池)** | 出图 / i2v 视频 / TTS / 免费素材库 | `cap-*/` |
| **质量标准** | 判够不够格(单一真相源) | `quality/quality_registry.md` |

---

## 目录结构

```
skill/
├── .claude-plugin/plugin.json   ← plugin 包壳(发布元数据)
├── LICENSE                      ← MIT
├── README.md                    ← 本文件
├── .gitignore
│
├── cap-stock-footage/           ← 能力:免费素材库(Pexels CC0)
│   ├── SKILL.md
│   └── fetch_stock_footage.py
│
├── cap-video-i2v/               ← 能力:i2v/t2v 视频生成(Seedance)
│   ├── SKILL.md
│   └── gen_video.py
│
├── cap-tts/                     ← 能力:语音合成(edge/minimax/volcengine)
│   ├── SKILL.md
│   ├── gen_speech.py
│   ├── minimax_client.py
│   ├── local_env.py
│   └── config.yaml
│
├── cap-image-gen/               ← 能力:通用出图(文生图 + 参考图驱动)
│   ├── SKILL.md
│   └── gen_image.py
│
├── quality/
│   └── quality_registry.md     ← 质量标准单一真相源(QG-* ID · 25 条门)
│
├── docs/
│   └── PROCESS.md              ← 流程文档(纯控制器·引用 QG-ID 不复述阈值)
│
└── skills-manifest.json        ← 外部技能安装清单(用户自己确认安装)
```

---

## 能力清单(cap-*)

| skill | 能力 | provider | 状态 |
|---|---|---|---|
| `cap-stock-footage` | 免费素材库(拉竖屏 B-roll) | Pexels(CC0) | ✅ 已封装 |
| `cap-video-i2v` | i2v/t2v 视频生成 | Seedance(grok 待补) | ✅ 已封装 |
| `cap-tts` | 语音合成 | edge / minimax / volcengine | ✅ 已封装 |
| `cap-image-gen` | 通用出图(文生图 + 参考图驱动) | GPT-image-2 | ✅ 已封装 |

> **视频合成流水线**(帧+VO+BGM+字幕→成片)属流程平面的装配层,不是原子能力 skill,不在此目录。

---

## 质量标准(quality_registry.md)

- **表头元规则 QG-RAISE-3**:「门禁是地板不是目标 · 抬高 3 档再验收」——每道门放行前的校准镜
- **14 条机器门(fail-closed)**:QG-SCORECARD-90 / QG-PALETTE-NEON / QG-MEDIA-* / QG-MOTION-FREEZE / QG-FORM-* 等
- **9 条人/agent 判断门**:QG-ANTI-MEDIOCRITY / QG-FIVE-DIM / QG-FORECAST ≥B / QG-PRD-ACCEPTANCE 等
- **6 条门禁结构规则**:QG-TWO-GATES / QG-INSIGHT-3FACTS / QG-LOOP-LIMITS / QG-DELIVERY 等

**改任何标准只改 quality_registry.md**,流程/代码按 ID 引用。

---

## 外部技能(skills-manifest.json)

**licensing 策略:自有 skill 直接打包进引擎;别人的 skill 由用户自己确认安装。**

- ✅ 可安全安装:higgsfield(MIT 主包) · gsap-*(MIT) · ai-image-prompts-skill(MIT + LICENSE)
- ⚠️ 安装前需确认:higgsfield-* 子包(MIT 推定,子目录无独立 LICENSE)
- 🚨 使用前必须核查授权:`video-form-*`(15 个,完全无 license/source 记录)
- 🔧 随引擎自动装:i2v-video-prompt · i2v-video-diagnose(自建)

---

## 收录标准

| ✅ 能进这里 | ❌ 不进这里 |
|---|---|
| 自有代码 · 自洽可移植 · 参数化 · license 明确 | 绑死项目路径/文案的脚本 |
| | license 不明的外部 skill(改走 skills-manifest 引用) |
| | 私有选题/凭证/产出/material |

---

## 发布流程

1. `skill/` 即为发布单元
2. 补全 `.claude-plugin/plugin.json` 的 `homepage` 字段(你的 GitHub URL)
3. `/plugin install <你的 GitHub URL>` 测试本地安装
4. 通过后推送 GitHub,向 Claude Marketplace 提交审核
5. 后续更新:git tag vX.Y.Z → GitHub Release → 用户 `/plugin update`

---

## 命名约定

- 能力单元前缀 `cap-`(capability):自洽可移植的原子能力
- 质量标准 ID `QG-<域>-<简名>`:全局唯一,只在 quality_registry.md 定义一次
- 外部技能:在 skills-manifest.json 登记来源+license+安装命令,用户自装
