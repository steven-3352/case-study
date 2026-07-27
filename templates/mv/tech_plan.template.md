# Tech Plan Template · {{film_name}}

> Copy this file to `publish/{{project_path}}/design/motion_tech_plan.md` and fill in `{{…}}` fields.
> Engine-level rules are in `docs/RULES/10_MV_ENGINE.md` — don't repeat them here.

## 0 · 前置确认

- [ ] 立绘 (cutout PNG) 已就绪: `{{asset_list}}`
- [ ] 音频文件: `{{wav_path}}`
- [ ] 时间轴起止: `{{t0}}` – `{{t1}}`s (`{{n_frames}}` 帧 @ {{fps}} FPS)
- [ ] 渲染尺寸: {{W}}×{{H}}

## 1 · 本片特有的技术缺口

> 列出与上一支 MV 相比**新增**的实现缺口。通用缺口已在 `10_MV_ENGINE.md` 解决，不重复写。

| 缺口 | 优先级 | 负责人 | 预计代价 |
|------|-------|--------|---------|
| {{gap1}} | P0 | | |

## 2 · 本片使用的原子集合

从 `mv_engine/atoms/` 选用的原子（已有 10 个，可追加）：

| 原子 | touches_alpha | 用途 |
|------|-------------|------|
| scan_bar | False | |
| {{new_atom}} | {{bool}} | |

## 3 · 缺口汇总（按代价档排序）

| 代价 | 项目 | 状态 |
|------|------|------|
| 0 | 直接用现有原子 | ✓ |
| S | {{small_gap}} | |
| M | {{medium_gap}} | |

## 4 · 验收器字段（开拍前冻结）

```
gate_check_motion: window=2.0s / disp=4% / area=8%
```

额外片级验收条件（如有）：

- {{extra_gate}}

## 5 · 与上游分镜的接口约束

- **镜头边界**来自歌词/节拍时间轴，固定，不是求解变量
- **素材分配**（谁在哪镜出现）固定
- **求解变量**：运镜模板 · 景别对 · 入场转场（见 `10_MV_ENGINE.md §6`）
