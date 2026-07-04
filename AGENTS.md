# AGENTS.md · Model-Agnostic Entry

> **任何 AI 编码 agent（Codex / Aider / Cline / Cursor / Claude Code / 其他）接入本仓库，先读本文。**
> 本文档 = 项目宗旨 + 铁律 0 + 分工指路 · **语言/模型无关**。

---

## 项目一句话

AI 内容自动化生产引擎：给对 AI 工具/AI 应用感兴趣的受众，产出**愿意看完且愿意互动的**短视频/图文轮播/带货内容。

---

## 铁律 0 · Audience-First, Not Pipeline-First（最高优先级 · 全局元规则）

**交付的评判基准是观众成果，不是工程产出。**

### 三要素（正向标准）

| 要素 | 含义 | 反面（禁） |
|---|---|---|
| **内容共鸣** | 命中真实情绪/场景，观众愿意在评论里接话 | 干货堆砌 · 泛泛而谈 · 蹭热点无锚 |
| **强观赏性** | 每 2-4s 视觉变化 · 首屏停划 · 中段不塌 · 音画同步 | 单场景占大部分时长 · 静态字幕 · catalog 拼盘 |
| **强内容** | 信息密度真材实料 · 可复现的方法/prompt/清单 | 空喊口号 · AI 拼凑 · 概念糊弄 |

### 反例（工程完成心态 · 全部不算交付达标）

- ❌「pipeline 跑通了」
- ❌「15 步走完了」
- ❌「所有工种产出都齐了」
- ❌「render 无报错」
- ❌「发布包三平台文案齐了」
- ❌「Task #XX completed」但没确认下游用没用、观众看没看

### 唯一交付判据

`pre_publish_forecast` 评级 ≥ **B** + 投后观众数据（3s 完播 / 完播率 / 互动 / 收藏）达标。C/D 或无 forecast 一律 `blocked`。

### 触发时刻（任何"完成"判定语义节点 · 自查三问）

- Task 打勾前
- Write 完文件后
- 脚本终稿声明
- render 出 mp4
- 发布包齐
- 「Task #XX completed」声明

**自查三问**：
1. 观众看到会不会**共鸣**？（场景是真的吗？情绪是命中的吗？）
2. 画面**观赏性**够吗？（每 2-4s 有变化吗？首屏停划吗？）
3. 内容**真材实料**吗？（有可复现的 prompt/clip/清单？还是空喊/概念糊弄）

**任何一问答不上"是" → 状态仍是 `draft`，未 done。**

### 正向表达（写文档/规范/汇报时的默认措辞）

- ✅「本条 3s 完播预测 X% · 达 `pre_publish_forecast` B 级 · 可外发」
- ✅「共鸣：钉子场景来自 X 平台 Y 条网络原话；观赏性：每 3s 变化 + catalog 占比 28%；强内容：3 段 prompt 可复制粘贴」
- ❌「pipeline 已跑通 · 发布包齐 · 可外发」
- ❌「15 步完成 · Task closed」

---

## 协作宗旨（用户 ↔ agent 协作方式）

- **用户只出选题和反馈数据。** 中途不追问决策，任何 agent 扮演各工种自己拍板。
- **不看仓库有什么，看哪条实现更强。** pipeline / 场景文件 / 工种名单不是完成标准；标准是观众停不停、懂不懂、互动/收藏，以及发布包能不能直接外发。
- **内容门 + 形式门分开 · fail-closed。** 脚本 90+ 允许 TTS；形式 forecast pass 才允许外发。两道门永不合并。
- **形式服务数据假设。** 每个高级视觉镜头必须声明服务 `completion_3s / completion_rate / 理解 / 收藏 / 评论` 中的哪一项，声明不了就不进片。

---

## 分工指路（按你是谁选入口）

| 你是 | 首读顺序 | 补充 |
|---|---|---|
| **Codex / Aider / 通用模型 agent** | 本文 → `docs/SYSTEM.md` → `CLAUDE.md`（工种/15 步细则同样适用） | `docs/DECISIONS.md`（辩论锁定） · `docs/CONVERSION.md`（转化路径） |
| **Claude Code** | `CLAUDE.md` → 本文 → `docs/SYSTEM.md` | project memory：`~/.claude/projects/-Users-wmzuo-Documents-project-case-study/memory/MEMORY.md` |
| **Cursor** | `.cursor/rules/*.mdc`（alwaysApply）→ 本文 | `audience-first.mdc` · `content-outcome-accountability.mdc` · `content-prep-multi-agent.mdc` · `platform-same-video-delivery.mdc` |
| **Cline / 其他** | 本文 → `docs/SYSTEM.md` → `CLAUDE.md` | 视 IDE agent 支持情况 |

---

## 项目结构（一屏）

```
case-study/
├── AGENTS.md                    # 本文 · model-agnostic 入口
├── CLAUDE.md                    # Claude Code 执行细则
├── docs/
│   ├── SYSTEM.md                # 完整规范 · 五层架构 · 15 步 · 铁律 0-11 · 候选实现清单
│   ├── DECISIONS.md             # 战略辩论锁定（Q1-Q11）
│   ├── CONVERSION.md            # 私信转化路径
│   ├── ASSET_LIFECYCLE.md       # 素材生命周期
│   └── design/                  # 各类 REJECT/FAIL/MISS 登记
├── .cursor/rules/*.mdc          # Cursor alwaysApply 规则
├── queue/topics.yaml            # 选题池 · 开放选题
├── publish/2026-WNN-*/          # 每周选题产出（洞察/设计/scripts/build/xhs/douyin/weixin）
├── pipeline/                    # 生产脚本（P001-P007 · TTS · gate_check）
├── integrations/openmontage/    # 外部制作插件（每条必跑 openmontage_brief）
├── templates/                   # 模板（洞察/设计/音画/发布包）
├── assets/
│   ├── formats/catalog.yaml     # 形式词汇（观感类型）
│   └── broll/catalog.yaml       # B-roll 素材目录
└── persona/persona.yaml         # 默认人设兜底
```

---

## Git

- **唯一工作分支：`main`**。日常开发、提交、推送均在 `main`。
- 不建日期分支或长期 feature 分支；短期分支跑完 merge 回 `main` 并删。
- 克隆后：`git checkout main && git pull origin main`

---

## 关键铁律速览（详见 `docs/SYSTEM.md` §3.1）

| # | 铁律 | 一句话 |
|---|---|---|
| 0 | Audience-First, Not Pipeline-First | 观众成果 = 唯一交付标准 |
| 1 | 不看仓库有什么，看哪条更强 | pipeline 存量不代表选型正确 |
| 2 | 内容门 + 形式门分开 | 两道门永不合并 fail-closed |
| 3 | 合规分 vs 效果分 | scorecard 90+ ≠ 能投 |
| 4 | 各环节专家对最终结果负责 | 不是对交差文件负责 |
| 5 | 尽一切可能让内容更好 | 宁可多一轮，不「能出片就行」 |
| 6 | 自我进化 | 提高标准 + REJECT_LOG + gate_check 升级 |
| 7 | 形式为数据假设服务 | 声明不了数据杠杆的形式不进片 |
| 8 | 承诺兑现到像素 | storyboard 承诺 → render 逐帧核 |
| 10 | `draft_self_generated` 无门禁效力 | 单跑 agent 不算通过 |
| 11 | 数据 A/B/C 分级 | 真实带来源 = A · 估算 = B · 无来源 = C |

---

## 完整规范（必读）

- **`docs/SYSTEM.md`** — 五层架构 · 15 步流程 · 工种组织 · 两道门 · 铁律 0-11 · 候选实现清单
- **`CLAUDE.md`** — 工种清单 · 环境配置 · 反例 · Claude Code 特定细则（对其他 agent 也适用工种/流程部分）
- **`docs/DECISIONS.md`** — 战略辩论锁定（Q1-Q11）
- **`docs/CONVERSION.md`** — 私信转化路径

---

**任何模型 / 任何 IDE agent 接入本仓库 = 铁律 0 生效。不读 = 不合规。**
