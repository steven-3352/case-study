# AGENTS.md · 跨环境编排指南

> **适用环境：** OpenCode · Codex · Aider · Cursor · 任何能读文件 + 调 LLM + 跑 shell 的 agent。
> **Claude Code 用户：** 直接调 `workflows/blueprint.js` + `workflows/prd_pipeline.js`，不看本文。
>
> 本文让你在**没有 Claude Code Workflow JS runtime** 的环境里，完整跑通 27 工种内容生产流程。
> 你（agent）就是编排器——逐波次执行角色、运行 Python 脚本、检查质量门。

---

## 一、前置准备

```bash
python3 setup.py          # 检查 Python 依赖 / ffmpeg / API key 就绪度
cp .env.example .env      # 填入各 cap-* 需要的 key（不用的 cap 留空）
node workflows/validate.js  # 角色注册表一致性自检（需 Node.js）
```

单一事实源（每步都要读，不要凭记忆）：
- 角色 spec：`roles/registry.yaml`
- 质量门：`quality/quality_registry.md`
- 19 维打分卡：`quality/video_19dim_scorecard.md`
- 各角色产出模板：`templates/` 对应文件（见角色 `output_template` 字段）

---

## 二、两段式流程总览

```
用户大白话描述
       ↓
[阶段一：蓝图] waves 1-10（理解→脚本→风格→分镜）
       ↓
⬛ 展示蓝图给用户 · 等一次确认（唯一人工节点）
       ↓
[阶段二：制作] waves 11-13（声音→剪辑→发布包）
       ↓
deliverable + publish.md
```

**阶段一止于分镜（wave 10），不写产出文件、不进制作。**
**阶段二用户确认后无人值守，质量门自动执行。**

---

## 三、阶段一：蓝图（waves 1–10）

### 3.1 角色激活规则

读 `roles/registry.yaml`，按如下规则决定哪些角色参与：

| activation 值 | 激活条件 |
|---|---|
| `always` | 所有形态必跑 |
| `video_only` | 非「图文轮播」形态 |
| `on_demand` | 使用 GSAP/Three/Web3D/复杂动效时激活 |
| `format:带货型` | 形态为带货型时激活（可叠加） |
| `format:出镜型` | 形态含出镜型时激活（可叠加） |

图文轮播额外跳过：`声音设计师`、`动画导演`、`动效技术导演`。

### 3.2 波次执行（同 wave 可并行，跨 wave 串行）

**每个角色执行模式：**
1. 读该角色 `output_template` 对应文件，了解产出格式
2. 读已有上下文（前序 wave 产出的文件）
3. 以该角色身份发起 LLM 调用，prompt 注入：
   - 角色 `responsibility`（职责）
   - 已激活的 `owns_dims`（该角色负责设计的 D 维 + QG-RAISE-3 目标：不是及格线是出色线）
   - 适用的 `gates`（本角色产出须过的 QG-* 门）
   - 模板格式要求
4. 产出存入内存（阶段一不落盘）
5. 检查门禁（见第五节）

**波次顺序（按 wave 编号串行）：**

| Wave | 角色 | 关键门禁 |
|------|------|---------|
| **1** | 编导 | 立项单：钩子+形态+验收标准 |
| **2** | 记者 · 纪录片导演 · 网络调研员 · [带货: 选品分析师 · 消费者声音研究员] | `QG-EXTERNAL-REFS`：≥3 URL + ≥2 网络原话，不满足退回网络调研员 |
| **3** | 选题深挖师 · 内核提炼师 · 领域专家 · 事实校验员 | `QG-INSIGHT-3FACTS`：关键信息 ≥3，无则退回；无用户原话退记者 |
| **4** | 留存与互动设计师（视频） | `QG-ATTENTION`：≥2 类注意力时刻 + ≥3 处焦点；`dual_review`=true → 需 2 名独立评审 ≥90 |
| **5** | 编剧 · [带货: 销售脚本师 · 合规审核] | `QG-ANTI-MEDIOCRITY`（抗平庸锦标赛） · `QG-SCRIPT-QUOTES`（原话≥4条） |
| **6** | 动画导演（视频） | ⚠️ `translation_layer=true`：只出「该有什么感觉」的可核验陈述，禁碰实现代码、禁写效果名 |
| **7** | 形式策略官（视频） | `QG-FORM-COMPETITION`：≥3 方案且跨 ≥2 家族；`QG-FIVE-DIM`；`QG-FORECAST`≥B |
| **8** | 视觉设计 · 视觉语言策展师 | `QG-PALETTE-NEON`（禁霓虹蓝紫）；`QG-VISUAL-ORIGINALITY`；候选须含≥1 浅色方案 |
| **9** | 动效技术导演（on_demand） | `dual_review`=true；接 wave 6 分镜拆组件任务清单 |
| **10** | 导演 · 摄像/视觉 · [出镜: 演员指导 · 造型] | 分镜须对齐 wave 4 留存节拍表 |

### 3.3 蓝图组装

所有 wave 1-10 产出汇总后，组装人类可读蓝图：
- 逐分镜大白话描述（含 VO 参考台词）
- 每镜标注用到的 D 维（`D01`–`D19`，见 `quality/video_19dim_scorecard.md`）
- 批量待确认项（决策点带推荐，不是开放问题）

---

## 四、确认节点（唯一人工节点）

**展示蓝图，等用户回复。** 接受两种输入：
- `"全部按推荐做"` → 直接进阶段二
- 指出编号改动 → 更新对应决策，进阶段二

**不得在此之前或之后再次询问用户。** 阶段二无人值守。

---

## 五、阶段二：制作（waves 11–13）

| Wave | 角色 | Python 脚本 | 关键门禁 |
|------|------|------------|---------|
| **11** | 声音设计师（视频） | `cap-tts/gen_speech.py` | `QG-MEDIA-HEAD-RMS`：前 6s ≥-25dB；`dual_review`=true |
| **12** | 剪辑 | `cap-video-i2v/gen_video.py`（i2v 镜头） | `QG-MEDIA-BLACK`·`QG-MEDIA-SILENCE`·`QG-MOTION-FREEZE`（连续冻结 ≤4s） |
| **13** | 运营/增长 | — | 三平台文案 + 评论区埋点；`QG-FORECAST`≥B 才允许外发 |

**成片后必跑机器门（shell 调用）：**
```bash
python3 -m pip show Pillow >/dev/null && python3 gate_check_palette.py <成片封面.png>
ffprobe -v error -show_entries format_tags=duration -of default=noprint_wrappers=1 <成片.mp4>
```
> gate_check_palette.py 和 gate_check_media.py 在宿主项目 `pipeline/` 里；
> 如果你是独立 clone 了本 repo 而没有宿主项目，直接用 ffprobe 手动复核 QG-MEDIA-* 阈值。

---

## 六、Python 能力调用参考（cap-*）

| 能力 | 入口 | 关键参数 |
|------|------|---------|
| TTS 口播 | `cap-tts/gen_speech.py` | `--script <文本文件>` `--provider edge\|minimax\|volcengine` |
| 图生视频 i2v | `cap-video-i2v/gen_video.py` | `--image <参考图>` `--prompt <运镜描述>` |
| 通用出图 | `cap-image-gen/gen_image.py` | `--prompt <图片描述>` `--size 1024x1536` |
| 免费 B-roll | `cap-stock-footage/fetch_stock_footage.py` | `--query <关键词>` `--orientation portrait` |

每个 cap 的完整参数见对应 `cap-*/SKILL.md`。

---

## 七、质量门触发时机（速查）

| 门 ID | 类型 | 触发时机 | 失败处理 |
|-------|------|---------|---------|
| `QG-RAISE-3` | 元规则 | **每次"能过/达标"判断前** | 强制自问：能抬高 3 档吗？ |
| `QG-INSIGHT-3FACTS` | 机器 | wave 3 后 | 退回内核提炼师（上限 2 轮） |
| `QG-EXTERNAL-REFS` | 机器 | wave 2 后 | 退回网络调研员（上限 2 轮） |
| `QG-ANTI-MEDIOCRITY` | agent 判断 | wave 5 编剧产出后 | 退锦标赛加锐度（上限 2 轮） |
| `QG-FORECAST` | agent 判断 | wave 7 形式策略官 + wave 13 发布前 | <B 退形式策略换路线（上限 2 轮） |
| `QG-PALETTE-NEON` | 机器 | wave 8 视觉产出 + 成片封面 | fail-closed，返工 |
| `QG-MOTION-FREEZE` | 机器 | 成片 mp4 | 退剪辑修复（上限 1 轮） |
| `QG-MEDIA-*` | 机器 | 成片 mp4 | fail-closed，返工 |
| `QG-PRD-ACCEPTANCE` | agent 判断 | 每个角色产出后 | 验收者 ≠ 产出者；二元 pass/fail |
| `QG-REVIEWERS` | 机器 | dual_review=true 的工种 | 至少 2 名独立评审 ≥90 |

---

## 八、铁律（违反即停工返工）

1. **角色独立性**：每个角色是独立 LLM 调用（不同的 system prompt），禁止你以主 agent 身份直接兼任多个工种产出。
2. **translation_layer**：`动画导演` 只产出「该有什么感觉」的可核验陈述（可观察量级），绝不碰实现代码，绝不写效果名（Ken Burns/parallax 这类词不得出现在 `observable_metric` 里）。
3. **验收独立性**：`QG-PRD-ACCEPTANCE` 的验收者必须是不同的 LLM 调用，不能是产出者自评。
4. **production_tier 不减角色**：轻量档/探索档只降验收强度（`QG-REVIEWERS` 人数），不减少激活的角色数量。
5. **QG-RAISE-3 优先**：每道门的阈值是地板，不是目标。放行前先问：能抬高 3 档吗？

---

## 九、闭环上限（防止无限循环）

| 失败环节 | 最多重试 |
|---------|---------|
| 洞察包不合格 | 2 轮 |
| 脚本被停划裁判判平庸 | 2 轮 |
| 形式策略 forecast fail | 2 轮 |
| 单镜 i2v 生成崩（幻觉/角色崩/AI 味重） | 3 次；救不活换路线（换模型/撤镜/换 B-roll） |
| 三平台适配失败 | 1 轮 |

上限耗尽仍未通过 → 停下来，向用户报告具体失败环节和已尝试的路线，等指令。
