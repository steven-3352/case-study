---
name: i2v-video-diagnose
description: |
  **本项目所有 i2v/t2v 视频生成后的诊断 & 迭代必调此 skill**——补 15 步流程里"生成后单镜内环闭环"的空缺。
  触发场景:视频生成完效果不满意 / 幻觉伪影 / 角色崩 / 动作不自然 / AI 味重 / 相机运动看不出 / 蓝紫溢出 / palette gate fail /
  用户说"这段不对/重生/改一下/为什么这么僵/怎么救"。
  触发词:视频质检 / 视频诊断 / video QA / 重生 / 迭代 / refine / 幻觉 / 崩了 / 塑料感 / face morph / limb warp / ghosting /
        prompt 迭代 / 只改 X / minimal edit / 失败归因 / 为什么这条不行。
  **配套 [[i2v-video-prompt]] 主门 + 15 个 video-form-* 子 skill 使用——写 prompt 用那些,写完生成完不满意用这个。**
platforms:
  - claude-code
  - cursor
  - codex
---

# i2v / t2v 视频生成后诊断 · 单镜内环闭环 skill

**位置:** 本项目 15 步流程里"渲染 → 验收"之间的**内环诊断层**。此前项目诊断力量集中在①事前 `gate_check.py` 门禁 和 ②投后 `post_publish_retro`,**中间"这条镜为什么崩、怎么最小代价救"的层缺失**——本 skill 补齐。

**边界:** 本 skill 只做**单条镜头 mp4 生成后**的 QA 诊断 + prompt 迭代;不做:
- 事前门禁(那走 gate_check.py 系列)
- 投后复盘(那走 evolution_apply / post_publish_retro)
- 选实现方式(那走 SYSTEM §4.2 form_strategy 五维打分)

---

## 一、失败原因 taxonomy(7 大类 × 精确特征)

对着生成的 mp4 逐类核对,**每类只找一个最主要问题**,避免"什么都改反而更坏":

| 类 | 视觉特征 | 常见 root cause | 修法优先级 |
|---|---|---|---|
| **1. 幻觉/伪影** | 多手指 / 少手指 / 器官错位 / 物件穿模 / 背景 morph / 文字变形 | i2v prompt 太长/太模糊 · 首帧图局部不清 · 参考图太多互相打架 | 高——观众第一眼就见 |
| **2. 角色崩(一致性)** | 脸型飘 / 发型变 / 服装换 / 年龄跳 | anchor 特征不够 · 无参考图 · 帧间 morphing · 时长过长 | 高——个人短片致命 |
| **3. 动作不自然** | 走姿飘 / 手势僵 / 嘴形对不上 / 关节反向 / 橡皮筋手臂 | grok 尤其弱(memory `feedback_camera-motion-vs-i2v-ceiling`)· 复杂多主体 · 动作 prompt 太抽象 | 高——细致人体动作换 Kling 是长期方案 |
| **4. 相机运动看不出** | 观感"像 PPT" · 首尾帧几乎一样 · zoom_max<1.05 | prompt 幅度写太小("3%" 之类)· 无 pan/tilt 组合 · 相机指令冲突 | 中——`feedback_zoompan-visible-motion` 已登记 |
| **5. 光影/色调错** | 温馨场景冷蓝调 · 呼气白雾 · 冷渲染 · 蓝紫溢出 · AI 味深色画布 | prompt 里"cold blue moonlit"/"cyberpunk neon"/"dark canvas"没删干净 · palette gate fail | 高——直接触发 [[feedback_no-neon-palette]] · [[feedback_no-ai-visual-dark-canvas]] · [[feedback_no-exaggerated-cold-atmosphere]] 铁律 |
| **6. 物理错** | 液体流向反 · 重力方向错 · 布料飘反 · 光影方向不合逻辑 | Seedance/Kling 较稳,grok 弱 · prompt 里物理常识没描述 | 中——加"gravity down / light from upper-left"这类明确物理指令 |
| **7. AI 味重(反 AI 味硬门 fail)** | 塑料感皮肤 / 磨皮过度 / 眼睛玻璃感 / 无痕迹的完美 / 冷开发者美学 | prompt 出现"AI/rendered/generated/artificial" · 无 film grain / 无自然瑕疵指令 · 首帧图本身 AI 味重 | 极高——直接毙,重生前必须换 look ref |

---

## 二、诊断标准动作(3 分钟内定位)

**不许瞎改 prompt。**按以下 4 步走:

### Step 1:视觉扫描(30s)
放视频 2 遍,列**最多 3 个**具体问题(不许列 5+),每个用一句话描述,不下判断。例:
- "S02 女主 3s 处手指有 6 根"
- "S04 男主嘴形和 VO 完全对不上"
- "S05 整体色调偏冷蓝,不温馨"

### Step 2:归因(1min)
用§一的 7 类 taxonomy 对每个问题打标签 + 定 root cause。规则:
- 一个问题**只归一类**,不许"混合原因"
- 归到某类后,先查该类的 memory 依据(feedback_camera-motion-vs-i2v-ceiling / no-neon-palette / 等)有没有讲过——**讲过就直接抄该 memory 的修法**,不重造轮子

### Step 3:minimal-edit prompt(1min)
每个问题**只改 1-2 个变量**,不整段重写。允许改的:
- 加/删 NEGATIVES 里 1-2 条
- 改 anchor 描述(如"long black hair" → "long black hair, oval face, 40 years old")
- 改相机运动幅度("3%" → "8%")
- 改光影 K 值("6500K cool blue" → "3000K warm interior tungsten")
- 改 duration(过长易 morph → 拆两段)
- 换首帧图(AI 味重 → 换真实照片)

**禁止**:
- ❌ 整段重写 prompt(变量太多无法判定谁在起效)
- ❌ 改超过 2 个变量
- ❌ 改 prompt 结构骨架(那是 i2v-video-prompt 主门定的)
- ❌ 加"very"/"more"/"better"这类无法量化的修饰

### Step 4:登记 + 重生
- 如果本次是**同 slug 第 2 次以上**迭代 → 写入 `docs/design/VIDEO_ITERATE_LOG.md`(新建):slug · 问题类别 · 改的 1-2 变量 · 新旧 prompt diff
- 第 3 次迭代仍崩 → **升级决策**:换模型(grok → Seedance 或反之)/ 换实现路线(i2v → 真实 B-roll / P001 截图 / GSAP)/ 撤这一镜(重排 storyboard)——不许无限迭代

---

## 三、诊断 prompt 模板(粘贴即用)

给 Claude / LLM 用来分析生成结果的标准问法:

```
你是 i2v 视频质检官。以下是本次生成的信息:

原 prompt:
<粘 motion_prompt 全文>

首帧图特征:
<描述首帧图关键内容 · 或 attach 图>

生成结果观察(客观描述,不下判断):
<粘 Step 1 列的 1-3 个问题>

请按 .agents/skills/i2v-video-diagnose/ 的 7 类 taxonomy:
1. 每个问题归哪一类?(单类,不许混)
2. root cause 是什么?
3. 该问题在项目 memory 里有没有先例?有的话给 memory slug
4. 给一个只改 1-2 变量的 minimal-edit 版 prompt(diff 高亮改的位置)
5. 若这已是第 3+ 次迭代,给"换模型/换实现/撤镜"的升级建议
```

---

## 四、和其他 skill / gate 的分工

| 环节 | 谁负责 | 输出 |
|---|---|---|
| 生成前:写 prompt | `.agents/skills/i2v-video-prompt/`(主门)+ `video-form-*`(子门 · 按形态) | 结构化 prompt 文本 |
| 生成中:执行渲染 | `pipeline/gen_video_frames.py`(grok)/ `pipeline/p011_seedance_i2v/gen_video.py`(Seedance) | 单段/批量 mp4 |
| 生成完:机器 QC | `pipeline/gate_check_media.py`(ffprobe 体检 · 时长/黑帧/静音/规格 fail-closed)+ `gate_check_palette.py`(蓝紫 >5% fail) | pass/fail bool |
| 生成完:**人+LLM 诊断迭代** | **本 skill**——回答"为什么崩、怎么最小代价救、要不要放弃" | minimal-edit prompt + 迭代日志 |
| 投后:数据复盘 | 数据复盘官 · `evolution_apply.py` · `post_publish_retro.md` | 下条 `evolution_overlay.md` |

**内环闭环规则**(2026-07-20 立):
- 同一 slug **最多迭代 3 次**;3 次内没救活 → 撤或换实现
- 每次迭代必须只改 1-2 变量,并登记 `VIDEO_ITERATE_LOG.md`
- 第 2 次以上迭代结果仍 fail gate_check_media/palette → 触发升级(换模型/换实现)

---

## 五、常见"救不活"的信号(直接撤镜/换实现)

出现以下**任一**,别再迭代 prompt,直接换路线:
- 3 次迭代仍角色崩 → i2v 模型天花板,该镜改**真实 B-roll**(Pexels)或**真人出镜**
- 3 次迭代仍相机运动看不出 → 该镜改 **P001 截图/录屏** 或 **GSAP 动效**
- 3 次迭代仍嘴形对不上 → 该镜改**画外音 + 全屏演示画面**(演示型)或**真人出镜**(出镜型),不硬要 i2v 说话
- 首帧图本身 AI 味重且换不到干净的 → 该镜改**真实素材**(Pexels 或用户提供),别用 GPT-image-2 出的图作 i2v 起点
- palette gate 3 次仍 fail → 视觉语言策展师返工,不是 prompt 层能救的

**升级决策记录:** 每次升级写 `VIDEO_ITERATE_LOG.md`,标"UPGRADE: <slug> from <route-A> to <route-B> because <reason>"——供投后复盘参考,避免下次同类 selection 再撞墙。

---

## 六、和项目铁律硬绑

- [[feedback_camera-motion-vs-i2v-ceiling]] · [[feedback_zoompan-visible-motion]] · [[feedback_no-neon-palette]] · [[feedback_no-ai-visual-dark-canvas]] · [[feedback_no-exaggerated-cold-atmosphere]] · [[feedback_anti-ai-visual]] · [[feedback_pipeline-burn-subs]]
- 诊断过程发现新的失败模式(如某个新 gate 反复 fail),写 `docs/design/SCRIPT_REJECT_LOG.md` 或 `FORM_FAIL_LOG.md`,同时反哺本 skill §一的 taxonomy

---

**总结一句:** 生成完不满意 → **不许瞎改**;来本 skill 走 4 步(扫描→归因→minimal-edit→登记),3 次救不活升级换路线。
