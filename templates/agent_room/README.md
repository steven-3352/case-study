# Agent 讨论室 · 周发布门禁

> **铁律：** 不看系统有什么，只看能做到什么。每个工种对**最终结果**负责，不是对「交差文件」负责。  
> 完整责权表：`.cursor/rules/content-outcome-accountability.mdc`

> **规则（CLAUDE.md）：** 洞察包 + 多工种讨论定稿后，才允许生成 `publish.md` / 进 `pipeline/` 渲染。

## 目录结构（每天）

```
publish/{week}/Dxx-{slug}/
├── room/
│   ├── discussion.md      # 多工种圆桌记录（必跑）
│   └── verdict.yaml       # 定稿决议 + status: approved
├── design/
│   ├── format_spec.md     # 形式选型师：能做到什么（非 F? 标签）
│   └── cover_review.md    # 视觉设计：PNG pass/reject
├── insights/              # 理解层四件套（必跑）
├── scripts/chosen.md
├── retention_beat_sheet.md
├── projects/{id}/storyboard.yaml          # 动效分镜师（视频）
├── projects/{id}/storyboard_carousel.yaml # 漫画分镜师（轮播）
├── douyin/publish.md
└── xhs/publish.md
```

## 讨论顺序（结果导向）

0. **网络调研员** → 痛点有公开依据
1. **编导** → 立项 + **本条要达成什么观众反应**
2. **记者 + 选题深挖师** → 钉子场景、原话
3. **洞察包** → P0、价值锚、红区
4. **形式选型师 + 平台原生策划** → `design/format_spec.md`（render_route + 与已发条目不撞）
5. **纪录片导演** → 故事弧（禁默认改造实录模板）
6. **编剧** v0/vA/vB → **留存设计师 + 运营** 选稿
7. **动效/漫画分镜师** → storyboard（能进 P004/P007 渲染）
8. **视觉设计** → cover_review **对 PNG 像素签字**
9. **导演 + 剪辑 + 声音设计师**（视频）→ 时长、音画三件套
10. **verdict.yaml** approved → week_build → render → **同步后各工种复验成片**

## 门禁（失败 = 负责工种退稿）

| 检查 | 失败动作 | 负责工种 |
|------|----------|----------|
| 成片与上一条同质 | 换 pipeline / 重写分镜 | 形式选型师 + 编导 |
| 抖音/小红书 delivery 相同 | 拆包重做 | 平台原生策划 |
| 无 storyboard 却走 P004/P007 | 补分镜或改 route | 动效/漫画分镜师 |
| cover_review reject | blocked，不可发 | 视觉设计 |
| 单模板 >40% 或中段拖沓 | 改节拍/压段 | 留存设计师 |
| P0 不实 / 红区表述 | 改脚本 | 事实校验员 + 编剧 |
| `verdict approved` 但不敢外发 | **整体退稿**，不开 `--force` 糊弄 | 编导 |

```bash
python3 pipeline/week_build.py              # 仅已 approved 的天
python3 pipeline/week_build.py --render     # render 后必须复验 PNG/mp4
python3 pipeline/week_build.py --force      # 仅调试，不可当外发依据
```

## 交稿前一句（所有工种）

> 「我敢不敢用这条代表账号？」——不敢就继续改，不推给 render。
