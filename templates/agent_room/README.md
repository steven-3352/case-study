# Agent 讨论室 · 周发布门禁

> **铁律：** 不看系统有什么，只看能做到什么。每个工种对**最终结果**负责，不是对「交差文件」负责。  
> **双人互评：** 每工种 ≥2 人 · 不同角度 · **avg ≥ 90** 才 pass · 迭代至 90+。  
> 完整责权表：`.cursor/rules/content-outcome-accountability.mdc`  
> 防应付清单：`templates/design/anti_perfunctory_gates.md`

> **规则（CLAUDE.md）：** 洞察包 + 多工种讨论定稿 + **全工种 scorecard 90+** 后，才允许 render / 外发。

## 目录结构（每天）

```
publish/{week}/Dxx-{slug}/
├── room/
│   ├── discussion.md           # 多工种圆桌 + 每轮 optimization_round 留痕
│   ├── verdict.yaml            # 定稿决议 + gates
│   ├── scorecards_index.yaml   # 全工种打分汇总
│   └── scorecards/
│       ├── 编剧.yaml           # 每工种 ≥2 reviewer · ≥90
│       ├── 动效设计师.yaml
│       └── …
├── design/
│   ├── format_spec.md
│   ├── design_language.md     # 视觉语言策展师：色板/字体/组件/禁用项
│   ├── openmontage_brief.md   # 可选：外部视频制作插件启用判断
│   ├── openmontage_review.md  # 可选：OpenMontage 回流验收
│   ├── script_review.md        # 编剧 pass/reject（90+ 前置）
│   ├── motion_wow.md
│   └── cover_review.md
├── insights/
├── scripts/  v0.md vA.md vB.md chosen.md
├── projects/{id}/storyboard.yaml
├── douyin/publish.md
└── xhs/publish.md
```

## 讨论顺序（结果导向 · 顺序不可颠倒）

0. **网络调研员** → 公开依据 + **hook_benchmark（同行前3秒）** · scorecard 90+
1. **编导** → 立项 + **完播/3s 目标** · 90+
2. **记者 + 选题深挖师** → 钉子场景、≥5 原话 · 90+
3. **洞察包** → P0、价值锚、红区 · 内核+事实 90+
4. **编剧 v0/vA/vB**（结构须不同，禁 stub）→ **留存 + 内核** 选稿 · 编剧 90+
5. **`script_review.md` pass** → 禁止 TTS 前必过
6. **留存** → **hook_benchmark 映射 0–3s** · 估 VO 时长（禁止为卡时长先删叙事）
7. **形式选型 + 平台策划 + 纪录片导演** → format_spec · 90+
8. **视觉语言策展师** → design_language（DESIGN.md 参考本地化为 token/组件/禁用项）· 90+
9. **OpenMontage 制作导演**（可选）→ 若原生路线不足，写 openmontage_brief；默认不启用 · 90+
10. **动效设计师 + 动效分镜师** → storyboard + motion_wow（标注口播句）· 90+
11. **漫画分镜师**（若 P007）· 90+
12. **视觉设计** → cover_review · 90+
13. **Phase A scorecards 全工种 ≥90** → render
14. **Phase B Round 6–8** → mp4/PNG 复验 + scorecard 复评 ≥90 → 编导 approved

**触发重评：** storyboard/动效大版本变更 → Round 4b + 编剧 scorecard 重评。

## 门禁（失败 = 负责工种退稿）

| 检查 | 失败动作 | 负责工种 |
|------|----------|----------|
| 任一工种 scorecard avg < 90 | 改产出 → 重评至 90+ | 该工种 + 编导 |
| 仅 1 人评分 / 自评 / 同角 | scorecard 无效，重评 | 编导 |
| script_review reject | 禁止 TTS/build | 编剧 |
| 先分镜后挤口播 | 退稿，按顺序重来 | 编剧 + 分镜师 |
| 原话 <4 进片 | 编剧重写 | 编剧 + 内核 |
| 动效无专属创意 / catalog 标配 | motion_wow 重做 | 动效设计师 + 形式选型 |
| 无 design_language / 只有“高级感”口号 | design_language 重做 | 视觉语言策展师 + 视觉设计 |
| OpenMontage 未说明必要性 / 直接覆盖平台成片 | 回退插件路线 | OpenMontage 制作导演 + 编导 |
| 三版 stub / 克隆上条骨架 | reject | 编剧 |
| 假讨论 / 无 Round 6+ | blocked | 编导 |
| cover_review reject | blocked | 视觉设计 |
| `verdict approved` 但不敢外发 | 整体退稿 | 编导 |

```bash
python3 pipeline/gate_check.py --all --phase approve   # 铁律 fail-closed
python3 pipeline/week_build.py              # approved 时自动 gate_check
python3 pipeline/week_build.py --render
python3 pipeline/week_build.py --force      # 登记 GATE_BYPASS_LOG · 不可外发
```

## 交稿前一句（所有工种）

> 「我敢不敢用这条代表账号？」——不敢就继续改，**scorecard 不到 90 不推下一环**。
