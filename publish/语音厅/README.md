# publish/语音厅/ · 索引

**建立日期:** 2026-07-20
**来源:** 反向工程 `/Users/wmzuo/Downloads/听潮阁·礼-*.mp4`(4 条 · 抽帧多模态分析)
**目标:** 换立绘/换歌/换品牌即可生成同类语音厅立绘 MV · 不需重画每帧

## 文件清单

| 文件 | 用途 |
|---|---|
| [`SOP.md`](SOP.md) | **主 SOP** · 4 类玩法(A 流行/B 抒情/C 国风/D 嘻哈)· 7 步制作流程 · 与项目 4 步 5 拍板点映射 · 铁律绑定 · **§九 动效层清单**(6 类转场/7 类立绘场景/6 类大字/4 类特殊 vfx + FFmpeg/GSAP 实现方案) |
| [`analysis/01_love_theme_song.md`](analysis/01_love_theme_song.md) | V1 · 玩法 A · 特色:Q版+精修双立绘 · 假音乐播放器 UI · **37 转场高密度 · vertical motion blur whip 招牌** |
| [`analysis/02_desert_island.md`](analysis/02_desert_island.md) | V2 · 玩法 B · 特色:图字联动倒影 · 情感道具 · **180° flip 呼应"倒影" · 圆框 mask** |
| [`analysis/03_abcd.md`](analysis/03_abcd.md) | V3 · 玩法 C · 特色:书法字 · 时钟盘 · 对称镜像 · **slat 竖分屏 slide-in · 光晕 vfx** |
| [`analysis/04_rapper.md`](analysis/04_rapper.md) | V4 · 玩法 D · 特色:Q版反差萌 · 10 人头像列 · **闪切二三连卡 rap 押韵 · 火焰粒子 · 逐字露出** |
| [`templates/storyboard_template.yaml`](templates/storyboard_template.yaml) | 分镜模板 · 每首新歌复制填空 · **含 effects: 字段**(transition_in / portrait_motion / overlays / big_text_effect / beat_align) |
| [`templates/prompt_立绘_template.md`](templates/prompt_立绘_template.md) | 立绘出图 prompt 骨架 · 4 玩法 4 版 · 一致性锚点规范 |

## 快速开始(想复制一条视频时)

1. **选歌 + 选玩法** — 曲风命中 A/B/C/D 之一(见 SOP §二)
2. **复制** `templates/storyboard_template.yaml` · 填空
3. **出立绘** — 每位演唱者按 `templates/prompt_立绘_template.md` 对应玩法骨架 · GPT-image-2 出图
4. **组接** — FFmpeg 按 storyboard 时间线 · 大字层 · 底部角色标 · 品牌水印 · 字幕烧录
5. **过 gate + 外发** — palette/media gate · pre_publish_forecast ≥ B · 手动外发抖音+xhs

## 挂载 skill(agent 自动 · [feedback_agent-auto-mount-skills](feedback_agent-auto-mount-skills))

- [i2v-video-prompt](i2v-video-prompt)(项目铁律主门)
- [video-form-music-video](video-form-music-video)(节拍同步)
- [higgsfield-shotlist-director](higgsfield-shotlist-director)(分镜)
- [higgsfield-character-design](higgsfield-character-design) + [higgsfield-soul](higgsfield-soul)(立绘 + 一致性)
- [higgsfield-cinema](higgsfield-cinema)(视觉方向)
- 玩法 D 加 [higgsfield-vibe-motion](higgsfield-vibe-motion)(情绪运镜)

## 铁律扫描小结(4 视频)

| 玩法 | palette gate 风险 | dark canvas 风险 | 复制时改动量 |
|---|---|---|---|
| A 流行 | 🔴 高(霓虹粉紫多) | 🟡 中 | 需换色板 · 其他复用 |
| B 抒情 | 🟡 中(冷蓝多) | ✅ 低 | 检查蓝像素占比 · 基本可用 |
| C 国风 | ✅ 低(冷灰哀婉) | ✅ 低 | **最稳** · 直接复用 |
| D 嘻哈 | ✅ 低(血红属允许) | ✅ 低(有舞台元素非纯 canvas) | **最稳** · 直接复用 |

## 后续动作建议

1. **首条试跑**用玩法 C 或 D(最安全 · palette gate 无风险)
2. 首条跑通再决定是否新建 `pipeline/p012_voice_lounge_mv/`(不预建 stub · 教训见 [project_p011-seedance-i2v-candidate](project_p011-seedance-i2v-candidate))
3. 数据回填后按 [project_weekly-form-ab-test](project_weekly-form-ab-test) 判断玩法 A/B/C/D 哪种最受欢迎
