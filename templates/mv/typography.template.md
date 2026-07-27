# 视觉语言 §4.1 排版规范 Template · {{film_name}}

> Copy to `publish/{{project_path}}/design/design_language.md` §4.1 section.
> 通用排版引擎规范在 `docs/RULES/10_MV_ENGINE.md §4`（原子准入）。

## 4.1 字幕排版参数

| 参数 | 值 | 说明 |
|------|----|------|
| 字体 | {{font_name}} | 完整路径: `{{font_path}}` |
| 基础字号 | {{base_size}} px | 按画幅宽 {{font_ratio}}% 定 |
| 字间距 | {{letter_gap}} px | 固定 |
| 空格宽 | 字宽 × {{space_ratio}} | |
| 字幕 Y | 画高 {{baseline_y}}% | |
| 入场动画 | {{entry_anim}} | 时长 {{entry_ms}} ms |

### 墨色规则

| 状态 | 填色 | 描边 |
|------|------|------|
| 正在唱 | `{{ink_active}}` | `{{edge_active}}` |
| 未唱 / 字幕 A 版 | `{{ink_inactive_a}}` | `{{edge_inactive_a}}` |
| 未唱 / 字幕 B 版 | `{{ink_inactive_b}}` | `{{edge_inactive_b}}` |

### 与光条的交互（A 版专有）

光条以上的字使用灰版颜色，规则与立绘的 scan_split 一致。
颜色混合公式：`int(c * 0.42 + SHADOW[j] * 0.58)` for j in (0,1,2)。
