# 选题深挖 · topic_brief

> 选题 ID: ___ · 内容 ID: ___ · 工种: **选题深挖师**（`skill/roles/registry.yaml` → `topic-digger`）
> 状态: draft | approved
> 对应质量门：**`QG-INSIGHT-3FACTS`**（洞察包门禁：无原话/场景细节退记者）· **`QG-PRD-ACCEPTANCE`**。

## 0. 入口必读（开工前打勾）

> 流程与门位见 `skill/docs/PROCESS.md`；不过清单不得写下面任何字段

- [ ] **流程 refs**：`skill/docs/PROCESS.md` 波次表（W2 选题深挖师 · 洞察包门位）
- [ ] **质量 refs**：`skill/quality/quality_registry.md`（`QG-INSIGHT-3FACTS` · `QG-EXTERNAL-REFS` · `QG-RAISE-3`）
- [ ] **template refs**：`skill/templates/insights/` 全部（本条 + core_message / domain_notes / fact_check / external_references + hook_benchmark）
- [ ] **角色 refs**：`skill/roles/registry.yaml` 形态激活映射（皮肤按选题激活，不跨条继承）
- [ ] **历史成品参考**：最近 1-2 条同节点 `topic_brief.md` 实读

**触发词打断**（出现即回本清单）：「上条 skin 差不多我抄一下」「audience 写『泛 AI 爱好者』就行」

## 本条皮肤（skin · 必填）

> 说明：项目走「开放选题 · 选题定皮肤」——每条选题在此声明自己的**受众/人设/话术**，皮肤不跨条继承；本段填得清，后面工种才能不套模板。
> 未填 → 编导驳回，禁止进入洞察包定稿与写稿。

```yaml
skin:
  audience:            # 本条服务谁（尽量具体：X 类人 + X 场景；不写"泛 AI 爱好者"）
  persona_anchor:      # 这条我是谁（如"做过 20 年互联网自己创业"，或"刚试用某工具的普通人"）
  tone_direction:      # 口吻方向（克制/热血/自嘲/学术/评测），关键词、禁词
  hook_scene:          # 本条钉子场景（一句话可视化）
  landing_intent:      # 转化落点（私信聊 X / 主页看 Y / 纯讨论）
  format_leaning:      # 建议形态倾向（真实项目案例/工具评测/方法论/观察/新品拆解/带货），仅倾向不锁死
  differ_from_last:    # 本条皮肤与最近 2 条有何不同（防止皮肤"惯性套用"）
```

**皮肤边界（自查）：**
- [ ] `audience` 是具体人群+场景，不是"AI 兴趣者"这类空词
- [ ] `persona_anchor` 与 `audience` 内在一致（一个 20 年老兵不适合装小白）
- [ ] `landing_intent` 走「等私信」路径，无「私信我 / 扣 1 / 加微信」
- [ ] `differ_from_last` 至少写 1 条实质差异（不是"这次讲的工具不同"这种表面差异）

## 受众画像

- 行业/角色: 
- 规模/场景: 
- 当前解法: 

## 钉子场景（一句话）

> 

### 场景细节（至少 3 个，要具体）

1. 
2. 
3. 

## 用户原话（≥5 条，标注来源）

| # | 原话 | 来源 |
|---|------|------|
| 1 | | |
| 2 | | |
| 3 | | |
| 4 | | |
| 5 | | |

## 改造前 / 改造后

| 改造前（现在怎么做） | 改造后（目标状态） |
|---------------------|-------------------|
| | |
| | |
| | |

## 本条不写什么（边界）

- 

## 编导签字

- [ ] 洞察包可进入内核提炼（`QG-INSIGHT-3FACTS`：场景细节 ≥3、原话齐备）
