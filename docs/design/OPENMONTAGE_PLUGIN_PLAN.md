# OpenMontage 插件化改造方案

> 状态：P1 插件集成已落地 · 默认关闭 · 按内容项启用  
> 目标：让当前项目保留“内容判断与增长系统”角色，把 OpenMontage 作为**可插拔高阶视频制作引擎**使用。

## 0. 当前落地位置

集成入口已经收敛到：

```text
integrations/openmontage/
```

关键文件：

| 文件 | 作用 |
|---|---|
| `integrations/openmontage/README.md` | case-study 与 OpenMontage 的插件边界、命令、回滚方式 |
| `integrations/openmontage/openmontage.env.example` | OpenMontage 侧 relay / provider 环境变量模板 |
| `integrations/openmontage/scripts/export_request.py` | 将 `openmontage_request.md` 导出到 OpenMontage project |
| `integrations/openmontage/scripts/collect_output.py` | 将 OpenMontage 输出回收进 `openmontage_production/` |
| `integrations/openmontage/patches/README.md` | sibling OpenMontage 本地补丁清单 |

W27D02 已作为 production pass 样例：

```text
publish/2026-W27/D02-会议纪要/openmontage_request.md
publish/2026-W27/D02-会议纪要/openmontage_production/
```

## 1. 一句话结论

当前项目做大脑，OpenMontage 做可选的视频制作插件。

```text
当前项目：选题、洞察、脚本、留存、平台策略、视觉语言、发布复盘
OpenMontage：真实素材检索、参考视频拆解、Remotion/HyperFrames/FFmpeg 合成、视频 QA
```

不要让 OpenMontage 接管选题和内容判断。它只接收当前项目已经定义好的内容任务，并把更强的视频表现力带回来。

## 2. 为什么要插件化

OpenMontage 是端到端视频制作系统，能力边界大于本项目的单个模块。如果直接并入，会带来三类风险：

| 风险 | 说明 |
|------|------|
| 架构污染 | Node/Remotion/Python 工具链、provider、预算系统会侵入当前轻量仓库 |
| 职责重叠 | OpenMontage 自带研究、脚本、提案、资产、剪辑流程，容易覆盖当前项目的内容门 |
| 回滚困难 | 如果代码和流程深度混合，后续发现不适合会很难剥离 |

所以采用插件模式：

```text
当前仓库只保留接口文档、brief、回流验收
OpenMontage 作为 sibling repo 或外部工具运行
两者通过文件交换，不共享运行时
```

## 3. 目标架构

```text
queue/topics.yaml
  → 当前项目完成 insights / scripts / retention / form_strategy / design_language
  → OpenMontage 制作导演判断是否启用
  → 导出 openmontage/request.md 或 request.json
  → OpenMontage 在外部仓库执行制作
  → 成品回流到 publish/{week}/Dxx-*/openmontage/
  → 通过 openmontage_review + gate_check + pre_publish_forecast
  → 才能进入 douyin/video.mp4 或其他发布包
```

## 4. 插件边界

### 当前项目负责

- 选题是否值得做
- 目标观众与平台
- 洞察包与事实边界
- 脚本三版与 chosen 稿
- 留存节拍与互动设计
- `design/form_strategy.md`
- `design/design_language.md`
- 发布文案与数据复盘
- 最终 go/no-go

### OpenMontage 负责

- 参考视频拆解
- 真实素材 / 档案素材检索
- AI 图像 / 视频资产生成
- Remotion / HyperFrames / FFmpeg 合成
- 字幕、配乐、音频混合
- ffprobe、抽帧、静音/黑屏/字幕 QA
- 产出制作日志与素材来源记录

### 禁止 OpenMontage 做

- 改变选题方向
- 新增未经洞察包验证的卖点
- 私自改写价值锚
- 绕过当前项目的内容门 / 形式门
- 把“更电影感”“更酷”作为启用理由
- 将 AGPL 代码直接复制进当前仓库

## 5. 新增工种提案

### OpenMontage 制作导演

位置：

```text
form_strategy + design_language 之后
storyboard / motion_tech_plan / render 之前
```

产出：

```text
design/openmontage_brief.md
```

职责：

- 判断本条是否适合启用 OpenMontage
- 选择 OpenMontage pipeline
- 明确输入文档、预算、素材类型、输出路径
- 写清成片必须兑现的画面承诺
- 写清回流验收标准

## 6. 推荐新增文件

### P0：只加文档与模板

```text
templates/design/openmontage_brief.md
templates/design/openmontage_review.md
docs/design/OPENMONTAGE_PLUGIN_PLAN.md
```

### P1：加软门禁

```text
templates/design/content_form_split_gates.md
templates/design/scorecard_rubric.md
templates/agent_room/scorecards_index.yaml
```

P1 只声明规则，不强制所有项目启用。

当前 P1 已落地为软规则：

- `content_form_split_gates.md` 增加 OpenMontage 外部制作路由，规定启用/禁用/回流条件。
- `scorecard_rubric.md` 增加 OpenMontage 制作导演评分 Rubric。
- `scorecards_index.yaml` 将 OpenMontage 制作导演列为按需激活角色。
- 不改 `gate_check.py`，不新增 `.env`，不要求历史项目补文件。

### P2：加导出/回流脚本

```text
pipeline/export_openmontage_brief.py
pipeline/import_openmontage_result.py
```

脚本只做文件转换，不运行 OpenMontage。

### P3：可选运行包装器

```text
pipeline/run_openmontage.py
```

该脚本只检查外部路径、写入 request、提示下一步。默认不自动执行昂贵生成。

## 7. openmontage_brief 字段

```markdown
# OpenMontage 制作 brief

enabled: false
reason:
target_metric: completion_3s / completion_rate / 理解 / 收藏 / 评论
recommended_pipeline:
render_runtime:
budget_usd:

## 输入
- meta:
- script:
- retention:
- form_strategy:
- design_language:
- storyboard:

## 画面承诺
- 必须出现:
- 禁止出现:
- 素材类型:
- 字幕/配乐:

## 输出
- work_dir:
- preview:
- final_video:
- asset_log:
- decision_log:

## 回流验收
- 内容一致性:
- 视觉语言兑现:
- 素材来源:
- 音频/字幕:
- 是否优于本项目原生路线:
```

## 8. 何时启用

| 场景 | 是否建议 |
|------|----------|
| 真实素材蒙太奇 / 纪录片感 | 建议 |
| 参考视频节奏拆解 | 建议 |
| Remotion 数据可视化 / 复杂合成 | 建议 |
| 产品广告 / 电影级预告 | 可试点 |
| 小红书图文轮播 | 不建议 |
| 简单大字卡片视频 | 不建议 |
| 当前 P004 已能稳定高质量完成 | 不建议 |
| 只是想“更酷” | 禁止 |

## 9. 对系统的影响评估

### 正向影响

| 影响 | 说明 |
|------|------|
| 表现力上限提高 | 可做真实素材、电影级、Remotion、复杂音画合成 |
| 降低 PPT 感 | OpenMontage 有素材检索、运动承诺和渲染后 QA |
| 强化证据优先路线 | 真实素材和档案素材可补当前 B-roll 短板 |
| 提高视频 QA 能力 | ffprobe、抽帧、音频电平、字幕检查可反哺当前 gate |
| 保持内容中枢不变 | 当前项目继续决定内容是否值得发 |

### 负向影响

| 影响 | 风险 |
|------|------|
| 流程变重 | 每条视频多一个 route 判断和外部制作环节 |
| 依赖变多 | Node、Remotion、额外 API key、素材 provider |
| 成本不确定 | 视频生成、音乐、TTS、素材检索可能增加费用 |
| 审核复杂 | 多一套 decision log / asset log / QA 结果需要读 |
| 许可证风险 | OpenMontage 为 AGPLv3，不应直接复制代码进本仓库 |

### 对现有工种的影响

| 工种 | 影响 |
|------|------|
| 编剧 | 不变；OpenMontage 不得重写核心脚本 |
| 形式策略官 | 增加一个候选实现路线：OpenMontage |
| 视觉语言策展师 | 约束 OpenMontage 的视觉输出 |
| 动效技术导演 | 判断 Remotion/HyperFrames/FFmpeg 方案风险 |
| 平台表现分析师 | 多评估一版 OpenMontage 成片 |
| 编导 | 保留最终驳回权 |

## 10. 插件开关

建议 `.env.example` 后续新增：

```bash
OPENMONTAGE_ENABLED=false
OPENMONTAGE_ROOT=../OpenMontage
OPENMONTAGE_DEFAULT_BUDGET_USD=1.00
OPENMONTAGE_MAX_BUDGET_USD=3.00
```

默认关闭。只有 `OPENMONTAGE_ENABLED=true` 且 `design/openmontage_brief.md enabled: true` 才允许进入外部制作。

## 11. 文件交换协议

### 导出给 OpenMontage

```text
publish/{week}/Dxx-*/openmontage/request.md
publish/{week}/Dxx-*/openmontage/request.json
```

### OpenMontage 回流

```text
publish/{week}/Dxx-*/openmontage/final.mp4
publish/{week}/Dxx-*/openmontage/preview.mp4
publish/{week}/Dxx-*/openmontage/asset_log.md
publish/{week}/Dxx-*/openmontage/decision_log.md
publish/{week}/Dxx-*/design/openmontage_review.md
```

只有 `openmontage_review.md` 通过后，才允许复制到：

```text
publish/{week}/Dxx-*/douyin/video.mp4
```

## 12. 回滚方案

### 回滚等级 A：只回滚本提案

删除：

```text
docs/design/OPENMONTAGE_PLUGIN_PLAN.md
```

影响：无。当前系统完全不变。

### 回滚等级 B：回滚模板接入

删除：

```text
templates/design/openmontage_brief.md
templates/design/openmontage_review.md
```

并从相关文档删除 OpenMontage 章节。

影响：不影响现有视频生产线。

### 回滚等级 C：回滚脚本接入

删除：

```text
pipeline/export_openmontage_brief.py
pipeline/import_openmontage_result.py
pipeline/run_openmontage.py
```

恢复 `.env.example` 中 OpenMontage 变量。

影响：只失去导出/回流能力。

### 回滚等级 D：禁用但保留文件

设置：

```bash
OPENMONTAGE_ENABLED=false
```

并要求 `design/openmontage_brief.md enabled: false`。

影响：最适合长期保留实验能力。

### P1 软接入回滚清单

如果只想撤回本次软接入，删除以下章节即可，不影响代码和历史发布包：

| 文件 | 删除内容 |
|------|----------|
| `templates/design/content_form_split_gates.md` | `13.5 OpenMontage 外部制作路由` |
| `templates/design/scorecard_rubric.md` | `OpenMontage 制作导演 · 可选插件门禁` 及“其他工种”表中该行 |
| `templates/agent_room/scorecards_index.yaml` | `conditional_roles` 中 `OpenMontage 制作导演` |
| `templates/agent_room/README.md` | 目录结构、讨论顺序、门禁表里的 OpenMontage 行 |
| `templates/README.md` | 外部制作插件说明与 OpenMontage 插件目录说明 |

撤回后：

- `openmontage_brief.md` / `openmontage_review.md` 可继续作为孤立模板保留。
- `gate_check.py` 无需恢复，因为 P1 没改代码。
- 已有内容生产流程不需要迁移。

## 13. P1 对系统影响

### 改变了什么

| 层 | 变化 |
|----|------|
| 工作流 | 在 `design_language.md` 后新增一个可选判断点 |
| 工种 | 新增条件角色 `OpenMontage 制作导演` |
| 评分 | 增加启用前与回流后的评分标准 |
| 文件流 | 规定外部成片先落 `openmontage/`，不得直接覆盖平台目录 |

### 没改变什么

| 层 | 保持不变 |
|----|----------|
| 内容门 | 编剧、事实、价值锚、CTA 仍由当前项目决定 |
| 形式门 | `form_strategy.md` / `design_language.md` 仍是前置 |
| gate | 暂不修改 `pipeline/gate_check.py` |
| 运行时 | 不引入 OpenMontage 依赖、API key、Node/Remotion 工具链 |
| 历史项目 | 不要求历史 publish 包补 OpenMontage 文件 |

### 风险控制

| 风险 | P1 控制方式 |
|------|-------------|
| 流程变重 | 只在 brief `enabled: true` 时激活 |
| 表现力压过内容 | 禁止改写选题、脚本、价值锚、CTA |
| 成本不可控 | brief 必填预算与 budget_mode |
| 授权不清 | review 必验 `asset_log.md` |
| 外部系统污染仓库 | OpenMontage 作为 sibling repo / 外部工具，不复制 AGPL 代码 |

## 14. 试点建议

先只选一条抖音 45–60s 视频试点，不碰小红书图文。

候选类型：

- 真实素材蒙太奇
- 有参考视频节奏可拆
- 当前 P004 容易像 PPT
- 需要强 B-roll 和配乐氛围

对比方式：

```text
A: 当前项目原生 P004 / GSAP 版本
B: OpenMontage 插件版本
```

评估：

- `pre_publish_forecast` 是否明显更强
- 0–3s 停划是否更清楚
- 中段是否更像视频而非 PPT
- 制作成本是否可接受
- 48h actual 是否值得扩大试点

## 15. 当前状态与建议

P0 已完成到文档与模板层：

```text
docs/design/OPENMONTAGE_PLUGIN_PLAN.md
templates/design/openmontage_brief.md
templates/design/openmontage_review.md
```

P1 已完成到软接入层：

```text
templates/design/content_form_split_gates.md
templates/design/scorecard_rubric.md
templates/agent_room/scorecards_index.yaml
```

当前建议：

1. 暂不改 `gate_check.py`，不把 OpenMontage 变成硬门。
2. 选一条未来视频，用人工方式填写 `design/openmontage_brief.md`。
3. 只让 OpenMontage 输出到 `publish/{week}/Dxx-*/openmontage/`。
4. 用 `design/openmontage_review.md` 判断是否值得替换原生视频路线。
5. 只有人工试点证明收益明显，再考虑 P2/P3 脚本化。

这样改造是可回滚的，且不会破坏当前项目的内容生产节奏。
