# Paperdoll MV 导演编排工程交接 · 2026-07-27

> 状态：导演规则与视觉总谱校验层已落地；自动导演编译器和渲染连接层待开发。
>
> 明日续做入口：先读本文，再读 `.agents/skills/paperdoll-mv-packaging/SKILL.md` 的“强制读取路由”和 §9.1。

## 1. 今日目标

围绕“用户只提供人物立绘、歌曲和歌词，系统如何有节奏地组织成角色 MV”完成以下工作：

1. 拆解两条参考视频，区分图生视频路线与确定性 2.5D 包装路线。
2. 提炼歌曲、歌词、人物关系和能量曲线之间的导演规则。
3. 形成可复用的《立绘音乐视频导演编排 SOP》。
4. 将导演 SOP 合并进现有 `paperdoll-mv-packaging` skill。
5. 给机器可执行的 `visual_score.yaml` 增加模板与结构校验器。
6. 明确从规则层继续走到“一次输入直接出最终视频”仍缺哪些工程连接件。

## 2. 参考视频分析结论

### 2.1 参考视频 A

源文件：`/Users/wmzuo/Desktop/e3e277ea97010aca532a499f20ec9275.mp4`

- 60.2 秒，368×640，24fps，竖屏。
- 主要是“角色设定图 + 多段图生视频 + 后期文字 + 音乐卡点”。
- 多数后期转场本身是硬切；流畅感来自生成镜头内部预先设计的入退场：烟雾聚合、人物消散、水滴、幕布、倒影和花瓣遮挡。
- 制作原则：将转场动作做到素材内部，在遮挡最完整、画面最暗或动作最强的位置切镜。
- 分析接触表：`/Users/wmzuo/video_analysis_e3e277/contact_1s.jpg`。

### 2.2 参考视频 B

源文件：`/Users/wmzuo/Desktop/62af5df0baddf2010a9f83a3d61ce5e7.mp4`

- 53.125 秒，640×368，24fps，横屏。
- 主要是“多张角色/场景插画 + 2.5D 动态海报 + 歌词书法 + 卡点剪辑”，不是以视频模型为主。
- 人物连续数秒姿态基本固定；动态主要来自分层视差、推拉、光带、粒子、文字、闪白和斜线遮罩。
- 同一角色实际使用了正面、侧身、背面、动作、双人和群像等多张素材；一张正面源立绘只能完成裁切、重构和轻微 2.5D，无法真实生成背面或复杂动作。
- 分析接触表：`/Users/wmzuo/video_analysis_62af5d/contact_1s.jpg`。

## 3. 今日锁定的导演模型

```text
歌曲结构决定什么时候变化
歌词语义决定画什么
人物关系决定谁前后相连
能量曲线决定画面有多强
素材条件决定使用哪种技术
```

### 3.1 三层卡点

- 一级：段落、乐句、主语或关系变化，用于切镜、换角色、换空间。
- 二级：歌词重音和关键词，用于改景别、人物进入、大字出现。
- 三级：普通鼓点和装饰音，用于扫光、粒子、涟漪和微震动。

不得将所有鼓点都变成硬切。主切点先服从乐句和语义完整性。

### 3.2 人物递进

```text
第一次出现：说明身份
第二次出现：建立关系
第三次出现：推进选择、情绪或冲突
最后一次出现：进入群像并完成归位
```

多角色片必须有首次介绍、双人关系、高潮群像和高潮后回收。只有 A→B→C→D 轮播的方案判“电子相册”。

### 3.3 能量旋钮

能量由人物数量、景别、镜头速度、文字尺寸、光效强度和剪辑密度共同控制。副歌相对主歌至少提升两项，全曲峰值至少提升四项，峰值后必须释放，除非歌曲在峰值直接截断。

### 3.4 技术路由

```text
身份介绍/歌词/群像排版 → 2.5D
雾/花瓣/光带/摄影机运动 → 确定性合成
0.5-2 秒大字快切 → 静态图
转身/抬手/消散 → i2v
缺侧身/背影/动作/关系姿势 → 先用参考立绘补图
```

## 4. 今日落地文件

### 4.1 Skill 主文件

`.agents/skills/paperdoll-mv-packaging/SKILL.md`

改动：

- frontmatter 只保留 `name` 和 `description`，补全导演编排触发语义。
- 增加“强制读取路由”。新片、重排或修复角色轮播时必须先读导演 reference。
- 阶段 0 增加音乐地图与人物地图。
- 阶段 ② 从普通分镜升级为“视觉总谱 + 素材计划 + 分镜”。
- §9.1 增加导演前置门，`visual_score.yaml` 校验不通过不得进入正式生成与渲染。
- 终审增加导演合同、关系镜头、能量曲线和补姿势来源检查。
- R1 改为“源立绘像素不可改；补姿势作为独立生成资产登记”。
- 背景生成器从“默认最终背景”改为“场景语法/预览路由”；廉价程序化背景不得进入正式片。
- §12.2 明确记录“导演编译器尚未接入主渲染入口”。

### 4.2 导演 reference

`.agents/skills/paperdoll-mv-packaging/references/director-orchestration.md`

包含：

- 十二条硬性导演规则
- 音乐、歌词、人物关系和能量地图
- `music_map.yaml` / `character_map.yaml` / `asset_plan.yaml` 最小结构
- 单镜任务、事件上限、首尾帧接力和转场决策
- 2.5D、静态、补图和 i2v 的路由规则
- 导演评分与返工顺序

### 4.3 视觉总谱模板

`.agents/skills/paperdoll-mv-packaging/assets/visual-score.template.yaml`

每镜强制字段：

```text
id / time / section / energy
purpose / leverage / characters / lyric
composition / primary_action / beats
first_frame / last_frame
transition_out.shared_element
technique / assets.use / assets.missing
```

### 4.4 视觉总谱校验器

`.agents/skills/paperdoll-mv-packaging/scripts/validate_visual_score.py`

当前检查：

- 顶层与逐镜必填字段
- 时间线覆盖、间隙和重叠
- 人物、段落、技术路线和转场枚举
- 卡点是否位于镜头时间内
- 能量是否有变化
- 多角色片是否存在关系/群像镜
- 连续相同人物与景别的幻灯片风险
- 峰值是否过早、峰值后是否释放

## 5. 素材来源裁定

遵循项目 `docs/RULES/08_ASSETS_LIFECYCLE.md` 的来源枚举：

```yaml
# 用户原始立绘
source_type: real_private
asset_role: source_portrait

# GPT-image-2 补姿势
source_type: synthetic_visual
asset_role: generated_supplement
```

源立绘不得被覆盖。补图必须新文件名、引用源立绘、保留 prompt/provider/成本，并检查脸、发型、服装结构、饰品和身体比例。

## 6. 今日验证

已运行：

```bash
python3 .agents/skills/paperdoll-mv-packaging/scripts/validate_visual_score.py \
  .agents/skills/paperdoll-mv-packaging/assets/visual-score.template.yaml

python3 /Users/wmzuo/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  .agents/skills/paperdoll-mv-packaging

git diff --check
```

结果：

```text
Visual score: PASS · 0 errors · 0 warnings
Skill: valid
git diff --check: PASS
```

## 7. 当前能力边界

### 已完成

- 导演方法论
- Skill 强制路由
- 机器可执行视觉总谱格式
- 独立结构校验器
- 源立绘/补姿势的合法来源边界
- 包装前置导演 gate

### 尚未完成

- 自动生成 `music_map.yaml`
- 自动生成 `character_map.yaml`
- LLM/规则混合的导演编译器
- `visual_score.yaml → shots_*.yaml / build_shots()` 编译器
- 低清 Animatic 自动生成器
- `asset_plan.yaml` 自动执行器
- GPT-image-2 补姿势与身份一致性自动检查
- Style Pack / L1-L7 与主渲染循环完整连接
- 歌词逐字显影渲染器
- 从项目目录一键产出 `final.mp4` 的 CLI

当前结论：Skill 已经能规范地产出和校验“导演合同”，但尚不能仅凭三输入自动直出最终视频。

## 8. 明日工程优先级

### P0 · 先打通导演到粗剪

1. 定义项目输入 `project.yaml` 和规范化目录。
2. 实现音乐地图生成器：节拍、段落、三级卡点、能量。
3. 实现人物地图生成器：导演功能、关系、出场预算。
4. 实现导演编译器：输出 `visual_score.yaml` 与 `asset_plan.yaml`。
5. 实现低清 Animatic：占位背景 + 原始立绘 + 歌词 + 基础切镜。
6. 实现 `visual_score.yaml → shots_*.yaml/build_shots()` 适配层。

P0 验收目标：给定一首歌、歌词和两张立绘，单命令产出校验通过的视觉总谱与可观看的 540p Animatic；不要求正式背景和高成本生成。

### P1 · 补素材并正式渲染

1. `asset_plan.yaml` 执行器。
2. GPT-image-2 背景和补姿势路由。
3. 人物身份一致性检查。
4. Style Pack / 七级强度接入。
5. 歌词和艺术字渲染。

### P2 · 一键成片和完整质量门

1. 三件套完整接入。
2. 小屏、卡点、遮挡、连续性和身份 QA。
3. 一键入口：`python3 -m pipeline.paperdoll.make --project <dir> --mode full`。
4. 输出 `music-analysis / visual-score / storyboard / animatic / quality-report / final.mp4`。

## 9. 明日启动顺序

```bash
cd /Users/wmzuo/Documents/project/case-study
git status --short
sed -n '1,240p' docs/design/PAPERDOLL_DIRECTOR_HANDOFF_2026-07-27.md
sed -n '1,120p' .agents/skills/paperdoll-mv-packaging/SKILL.md
sed -n '1,220p' .agents/skills/paperdoll-mv-packaging/references/director-orchestration.md
python3 .agents/skills/paperdoll-mv-packaging/scripts/validate_visual_score.py \
  .agents/skills/paperdoll-mv-packaging/assets/visual-score.template.yaml
```

然后从 P0 的输入合同和音乐地图模块开始，不先做正式背景、补图或渲染特效。

## 10. 工作区注意事项

今日开始前仓库已有以下未跟踪内容，未修改、未删除：

```text
.cache/
pipeline/gen_jimeng_firstframes.py
pipeline/gen_jimeng_prompts.py
```

今日新增/修改均位于：

```text
.agents/skills/paperdoll-mv-packaging/
docs/design/PAPERDOLL_DIRECTOR_HANDOFF_2026-07-27.md
docs/design/WORKFLOW_EXECUTION_LOG.md
```

不要把上述原有未跟踪文件误当成本次改动清理或回退。

## 11. 已知后续清理项

- `SKILL.md` 仍超过 1000 行。已经为导演规则使用 progressive disclosure，但原有包装参数库、人物运动库和验证细节仍在主文件中。后续可拆为 `references/packaging-system.md`、`references/motion-techniques.md` 和 `references/execution-validation.md`，并保留原章节索引，避免一次性大改破坏引用。
- `docs/RULES/memory/skill_meta/reference_paperdoll-mv-packaging-skill.md` 是旧摘要，包含已经过时的 R1/色板/流程描述。因本次任务只更新 skill，且项目规则禁止在此节点直接修改 `docs/RULES/`，未动该文件；后续应走规则 owner 审核后同步。
- 校验器目前只验证结构和部分导演不变量，不判断音乐切点是否真的来自音频，也不做人物身份视觉检查。这些属于后续生成器和 QA 层。

## 12. 本次最终判断

今天完成的是“把导演规则变成可执行合同的第一层”，不是完整自动视频工厂。明日最有价值的工作不是继续扩充风格包或特效，而是打通：

```text
音频/歌词/立绘
→ music_map + character_map
→ visual_score
→ validated animatic
→ shots/build_shots
```

这条链跑通后，现有包装引擎、Style Pack、背景、艺术字和 QA 才有稳定的导演上游。
