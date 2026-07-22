# 质量登记表 · Quality Registry(单一真相源)

> **这是内容生产引擎「质量平面」的唯一权威定义处。** 所有验收/门禁/打分标准**只在本表定义一次**,每条一个稳定 ID(`QG-*`)。流程平面、`gate_check*.py`、`prd_pipeline` 一律**按 ID 引用**,不再各自复述阈值。改标准 = 只改本表。
>
> 三平面里本表是「质量」:流程(控制器)负责谁先做,技能(能力池)负责怎么做,**本表负责判够不够格**。

---

## 0. 表头元规则 · QG-RAISE-3「门禁是地板不是目标 · 抬高 3 档再验收」

**这不是一道门,是评判下面每一道门时都要套的校准镜。**

任何 `QG-*` 门的阈值,语义都是「最低及格线」,不是「验收目标」。每到「我觉得这个能过」的时刻,那个「能过」的感觉本身就是「标准定低了」的信号,强制自问:**能不能把验收目标往上提 3 个档次?** 把抬高后的标准当成真正的验收目标去建,再验收。

- **触发点** = 一切「它过了 / 达标了 / 可以 approve」的判断时刻(下面任一 `QG-*` 打算放行时)
- **「3 档」= 刻意的实质大跳,不是 +1 敷衍**;从「最低可接受」切到「什么才算明显出色」
- **动手前设定**,不是过后无限返工;与闭环上限(QG-LOOP-LIMITS)不冲突——那管「失败后重做几轮」,本条管「第一次瞄多高」
- **判据自查**:若放行理由是「它过了 gate」,停——问「过的是目标还是代理指标?这道地板是『好/出色』的代理,清了它等于什么都没说」

> 依据 memory `feedback_gate-floor-not-target` · `feedback_build-to-reference-not-floor`。**本引擎所有制作 workflow 每一道验收都遵守本条。**

---

## 1. 机器门(fail-closed · 无主观空间 · 由脚本强制)

| ID | 名称 | 判定标准 / 阈值 | 应用对象 | 强制点 |
|---|---|---|---|---|
| `QG-SCORECARD-90` | 打分门 | 每 reviewer ≥90 且均值 ≥90;**89=fail** | 所有打分工种 | `gate_check.py` validate_scorecards |
| `QG-REVIEWERS` | 独立评审人数 | explore ≥1 · 轻量/全量 ≥2 独立 reviewer | 打分工种 | `gate_check.py` |
| `QG-NOTES-40` | 评审字数 | reviewer notes ≥40 字(防敷衍) | 打分工种 | `gate_check.py` |
| `QG-PALETTE-NEON` | 禁霓虹色 | 蓝紫像素 HSL H∈[240°,290°] 占比 >5% → fail(真截屏例外) | 所有主视觉/封面/大字 | `gate_check_palette.py` |
| `QG-MEDIA-BLACK` | 黑帧 | 纯黑帧 ≥1.0s → fail | 成片 mp4 | `gate_check_media.py` |
| `QG-MEDIA-SILENCE` | 静音死区 | 静音 ≥3.0s → fail | 成片 mp4 | `gate_check_media.py` |
| `QG-MEDIA-HEAD-RMS` | 开场响度 | 前 6s mean_volume ≥ -25dB(禁沉默钉子) | 成片 mp4 | `gate_check_media.py` |
| `QG-MEDIA-CLIP` | 爆音 | max_volume ≥ -0.1dB → 疑似爆音 fail | 成片 mp4 | `gate_check_media.py` |
| `QG-MOTION-FREEZE` | 动效密度 | 连续像素冻结 >4.00s → fail(防 PPT 感) | 成片 mp4 | `gate_check.py` freezedetect |
| `QG-FORM-EXCLUSIVE` | 专属视觉隐喻 | ≥3 种 | 视觉/形式 | `gate_check.py` |
| `QG-FORM-CATALOG-RATIO` | catalog 占比 | catalog 拼盘时长占比 ≤0.35 | 视觉/形式 | `gate_check.py` |
| `QG-FORM-TEMPLATE-REPEAT` | 模板复用 | 同模板 ≤1 镜 | 视觉/形式 | `gate_check.py` |
| `QG-FORM-DISTINCT` | 场景多样 | 48s+ 视频 ≥6 种不同模板 | 视觉/形式 | `gate_check.py` |
| `QG-ATTENTION` | 注意力硬门 | ≥2 类时刻 · ≥3 处焦点 | 分镜 | `gate_check.py` |

> 阈值常量物理位置:`pipeline/gate_check.py`(SCORECARD_PASS=90 等)· `gate_check_media.py` · `gate_check_palette.py`。**改阈值须同步本表**(见 §4 维护规则)。

## 2. 人/agent 判断门(主观 · 由独立评审或裁判执行)

| ID | 名称 | 判定标准 | 应用对象 | 强制点 |
|---|---|---|---|---|
| `QG-ANTI-MEDIOCRITY` | 抗平庸·停划裁判 | N 角度竞写 → 判「平不平庸」**默认毙**,除非有别人写不出的东西 | 编剧(创意峰值工种) | `templates/design/anti_mediocrity_tournament.md` |
| `QG-SCRIPT-QUOTES` | 编剧原话硬门 | 用户原话 ≥4 条,少于即 fail(不论其他维度) | 编剧 | scorecard rubric |
| `QG-MOTION-CREATIVE` | 动效专属创意硬门 | 专属创意 ≥3 处不同视觉隐喻,少于即 fail | 动效设计师 | scorecard rubric |
| `QG-VISUAL-ORIGINALITY` | 视觉原创门 | 6 必答问(关声能否认出新内容等)+ 5 must-have + 6 fail 条件 | 视觉/形式/动效 | `templates/design/visual_originality_gate.md` |
| `QG-FIVE-DIM` | 实现方式五维打分 | 停划×2/看懂×2/节奏×1/互动×1/证据×1/交付风险×0.5,加权最高分 wins;否决项不看分 | 每一镜实现选型 | SYSTEM §4.2 |
| `QG-FORM-COMPETITION` | 形式竞争 | ≥3 方案且跨 ≥2 家族;openmontage brief 前置 | 形式策略官 | `templates/design/form_competition.md` |
| `QG-FORECAST` | 投前预测 | A: 3s 完播≥55% 且总完播≥40%;**≥B 才允许外发**;C/D 禁发 | 平台表现分析师 | `templates/design/pre_publish_forecast.md` |
| `QG-PRD-ACCEPTANCE` | PRD 独立验收 | 验收者≠产出者;只读 acceptance_criteria + observable_metric;**二元 pass/fail**,不打分不排名;metric 空洞即 fail | 被激活的每个角色 | `prd_pipeline.js` Phase 3 |
| `QG-COMPLIANCE` | 带货合规红线 | 广告法/绝对化用语/医美食品化妆品红线/平台规则 | 带货型 | 合规审核工种 |

## 3. 门禁结构规则(流程性质 · 定「哪些门何时挡」)

| ID | 名称 | 规则 |
|---|---|---|
| `QG-TWO-GATES` | 两道门分开 | 内容门(脚本≥90 → 允许 TTS)与形式门(视觉审计+forecast+形式≥90 → 允许外发)永不合并;禁 catalog 拼盘假 approved |
| `QG-INSIGHT-3FACTS` | 洞察包门禁 | 关键信息 <3 条退内核提炼师;无原话/场景细节退记者;编剧稿出现洞察卡没有的卖点退事实校验员 |
| `QG-EXTERNAL-REFS` | 调研门禁 | 无 external_references(≥3 URL + ≥2 网络原话)→ 禁止洞察包定稿 |
| `QG-I2V-DIAGNOSE` | 生成后诊断 | 7 类归因 → minimal-edit 只改 1-2 变量 → **3 次救不活升级换实现** |
| `QG-LOOP-LIMITS` | 闭环上限 | 洞察包/脚本/形式各 2 轮 · 三平台适配 1 轮 · 单镜诊断 3 次;禁无限循环 |
| `QG-DELIVERY` | 唯一交付判据 | pipeline 跑通/工种齐/render 无错**都不算达标**;唯一判据 = `QG-FORECAST` ≥B + 投后观众数据达标 |

---

## 4. 维护规则(防漂移)

1. **单一定义**:任何 `QG-*` 只在本表定义阈值。其他文档(流程/CLAUDE.md/SYSTEM.md/脚本注释)出现该标准时,写「见 `QG-XX`」,**不复述数字**。发现某标准在别处又写了一遍阈值 → 删掉那处,改引用。
2. **机器门阈值双写点**:`QG-SCORECARD-90`/`QG-PALETTE-NEON`/`QG-MEDIA-*`/`QG-MOTION-FREEZE` 等的实际数字既在本表、也在 `pipeline/gate_check*.py` 常量里(代码要能跑)。改一处必须同步另一处——这是已知的「代码↔文档」双写点,列为技术债;彻底消除需让 gate_check 从本表/一份 yaml 读阈值(见重构方案 Phase「数据驱动」,未做)。
3. **新增门**:新门先在本表分配 ID + 归类(机器/判断/结构),再在流程里引用;不得直接在流程描述里内联新阈值。
4. **提升3档(QG-RAISE-3)不设终点数字**:它是校准动作,不是可 fail 的门;每道门放行前跑一次它的自问。

---

*ID 命名:`QG-<域>-<简名>`,大写 kebab。域:SCORECARD/FORM/MEDIA/MOTION/PALETTE/INSIGHT/FIVE-DIM/FORECAST/PRD/LOOP 等。*
