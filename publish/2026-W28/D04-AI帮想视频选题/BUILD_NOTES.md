# BUILD_NOTES · W28D04 pipeline 出片前置清单

> 用途：`pipeline/p004_video/run_pipeline.py --config pipeline_config.yaml --step all` 之前必跑的资产/校验步骤
> 依赖：`audio_plan.yaml` · `storyboard.yaml` · `motion_storyboard.md` · `form_strategy.md`（pass_dual_review avg=92）
> 状态：**`SHIP_READY_2026-07-05_15:00`** · UI PNG 占位版 · 三平台 mp4 已出（62.77s / 4.7-4.8 MB）
> **不阻塞后续 15 步流程推进**（步 13/14 可先跑；步 12 render 已完成占位版）

## 0. 资产 gap 现状（2026-07-05 · check）

| 类别 | 需求 | 当前 | 状态 |
|------|------|------|------|
| **Pexels 白天办公 B-roll** | M1/M4 白天办公桌 3800-4200K × 2 场 | ✅ `assets/broll/raw/office_desk_daylight_overhead__19798260.mp4` + `person_at_desk_daylight_back_view__6024431.mp4` · 已入 pipeline_config.yaml | ✅ Agent 完成 2026-07-05 |
| **QuickTime 屏录** | S1(M2/M3)/S2(M6)/S3(M7) × 4 场次 | 使用 UI PNG 占位版 · `build/assets_ui/{02,03b,06,07}_*_placeholder.png` | ⚠️ 占位版 ✅ · 用户 QuickTime 后可无缝替换 broll |
| **真机截图** | M5 分屏 40w vs 800 × 2 张 + 马赛克 | 使用 UI PNG 占位版 · `build/assets_ui/05_m5_split_400w_vs_800.png` | ⚠️ 占位版 ✅ · 用户提供真截图后 gen_ui hstack 合成 |
| **4 段 prompt 家居收纳版全文** | M7 演示内容 | ✅ `design/prompt_4_segments_home_organization.md` · 屏录规范齐 | ✅ 完成 |
| **UI 叠层 PNG** | M3/M5/M8/M9/M10 + M2/M3b/M6/M7 占位 · 共 9 张 | ✅ `gen_ui_w28d04.py` · palette gate 0.00% Dracula PASS | ✅ 完成 |
| **sfx CC0 素材** | ambient/tick/whoosh/hit × 10 项 | 无 · 当前渲染无 sfx 轨 | ⚠️ 待 Freesound 拉 · 不阻塞外发 · 密 VO 演示型可 off |
| **TTS VO** | MiniMax male-qn-jingying-jingpin | ✅ `build/audio/vo_w28d04.mp3` · 62.77s · loudnorm -16dB | ✅ 2026-07-05 完成 |
| **三平台 mp4** | douyin/xhs/weixin | ✅ `douyin/video_no_bgm.mp4` + `xhs/` + `weixin/` · 62.77s / 4.7-4.8 MB | ✅ 2026-07-05 完成 |

## 0.5 最终交付状态（SHIP_READY）

**渲染时间：** 2026-07-05 15:00

**交付物：**

| 平台 | 路径 | 大小 | 时长 | 特色 |
|------|------|------|------|------|
| Douyin | `douyin/video_no_bgm.mp4` | 4.7 MB | 62.77s | 42pt 字幕 · margin_v 200 |
| Xiaohongshu | `xhs/video_no_bgm.mp4` | 4.8 MB | 62.77s | 50pt 字幕 · margin_v 220 · **>60s 平台风险已登记** |
| Weixin Channels | `weixin/video_no_bgm.mp4` | 4.7 MB | 62.77s | 42pt 字幕 · margin_v 200 |

**关键 QC 通过：**
- ✅ 禁霓虹色板 gate：6 帧 rendered mp4 采样 · 蓝紫占比 0.00-0.03% << 5% 阈值
- ✅ CTA 完整性：s8 起 57.67s 结 62.77s · "私信「账号方向」——我给 5 条选题。不推服务。" 5.1s 完整播出
- ✅ VO 覆盖：VO 全程 3-62.77s（0-3s 沉默钉子设计）· 覆盖率 95%
- ✅ 字幕 burn-in：ffmpeg-full libass · SRT 生成 · ASS 烧录
- ✅ palette 硬门：0 fail 5% 阈值 (`gate_check_palette.py`)
- ✅ scene-VO 对齐：Δ=0.00s ✓（scene total_dur 全部匹配 seg_timing window）

**知悉风险（不阻塞外发）：**
- xhs 62.77s > 60s 平台推荐上限 · 见 `docs/design/PLATFORM_LIMITS_RISK_LOG.md` · 走"平台风险登记"不改 VO
- 无 sfx 轨（whoosh/tick/hit/ambient）· 密 VO 演示型允许 off · sfx 建 P1/P2 库后可后期补 mix
- M2/M3b/M6/M7 4 段是 UI PNG 占位版 · 视觉信息完整（真机 ChatGPT mock/AI 对话框/红叉/勾选表）· 用户后期 QuickTime 屏录替 broll 需重跑 `--step preview + --step platforms`

**用户后期升级路径（可选）：**
1. QuickTime 屏录 4 场次 → 替换 `pipeline_config.yaml` M2/M3/M6/M7 的 `src_type: img` → `src_type: broll` · 指向新 mp4 路径
2. 提供 M5 真机 40w/800 截图 → 重跑 `gen_ui_w28d04.py` 自动 hstack 合成真截图版
3. 拉 Freesound 10 项 sfx 到 `assets/sfx/**/*.wav` → 待 sfx-mixer P1 上线后可自动 mix

## 1. 前置资产任务清单（历史 · 用户升级路径参考）

### 1.1 Pexels 白天办公 B-roll 新拉（**用户或本机跑 fetch_broll.py**）

```bash
# 新拉关键词组（4 条候选 · 优先俯拍 + 摄像头红点 + 白天光）
python pipeline/p004_video/fetch_broll.py \
  --query "daylight office desk overhead" \
  --query "webcam recording setup" \
  --query "hand hovering keyboard morning" \
  --query "blank notebook desk morning" \
  --query "behind view person at desk daylight" \
  --target-count 6 \
  --min-duration 3 \
  --output assets/broll/raw/
```

**必需素材（对齐 pipeline_config.yaml.scenes）：**
- ✅ `assets/broll/raw/office_desk_daylight_overhead__19798260.mp4`（Pexels 白天办公桌俯拍 8s · Ali Alcántara CC0）→ M1（1s 用）
- ✅ `assets/broll/raw/person_at_desk_daylight_back_view__6024431.mp4`（Pexels 主角背影办公桌 7s · Pavel Danilyuk CC0）→ M4（5.75s 用）

**筛选口径：**
- 白天光 3800-4200K（区别 D03 深夜 3000-3500K · D02 傍晚 2800-3000K）
- M1 优先带摄像头亮红点素材（若无 · 用 drawbox 小红点 5×5 覆盖右上）
- M4 主角背影不露脸（保代入性）

### 1.2 QuickTime 4 场次真机屏录（**用户本机操作**）

**S1 · M2+M3 · 2s（0.6s 打字 + 1.4s AI 输出 + 反差留白）**
- 打开 ChatGPT/DeepSeek/豆包（建议 ChatGPT · 识别度高）
- 屏录：打字「帮我想 10 个抖音选题」14 字（真人节奏 · 30ms/字） → 回车 → AI 输出 3 条固定文案：
  - 「如何做好家居收纳」
  - 「浅谈家居收纳的重要性」
  - 「5 个家居收纳误区」
- 保留 iOS/macOS 状态栏 · 不打 AI 工具 logo（后期马赛克）
- 输出：`assets/screenrec/raw/w28d04_M2_typing_14chars.mp4`（0.6s）+ `assets/screenrec/raw/w28d04_M3_ai_output_3lines.mp4`（0.8s）

**S2 · M6 · 10s（3 段烂 prompt 反例）**
- 屏录 3 个 AI 对话框反例（每段约 3.3s）：
  - ①「帮我想 10 个抖音选题」→ 通用套话
  - ②「加平台词：帮我想 10 个抖音选题」→ 同行都在拍模板
  - ③「帮我想 10 个类似 XX 的选题」→ 换数字的同质品
- 输出：`assets/screenrec/raw/w28d04_M6_wrong_3flash.mp4`（10s · 3 段拼接）

**S3 · M7 · 15s（4 段 prompt 演示核心 · 全片主场）**
- 屏录连续 15s：
  - 25-27s：粘贴完整 4 段 prompt（家居收纳版 · JetBrains Mono 32-40pt）全屏可见
  - 27-40s：AI 输出 10 条候选表格（每条 1s 打字机式出现 · 表格列 = 标题/场景/钩子/成本/差异化）
- 输出：`assets/screenrec/raw/w28d04_M7_4prompt_15s.mp4`（15s）
- **观众需暂停截屏 · 镜头不晃**

**S4 · vB backup · 3s（可选 · 备胎）**
- 若 vA 3s 完播 <52% 触发 vB · vB 用主角背影 + 秒表 30:00 静态 · 不录

**输出目录：** `assets/screenrec/raw/`（若不存在需创建）

### 1.3 M5 分屏截图 × 2 + 马赛克

- 截图 1：同行 40w 赞爆款截图（马赛克遮挡真实同行头像/账号名）
- 截图 2：自己 800 赞截图（同样马赛克）
- **单位显式硬约束**：两图必须保留"赞"字（避 800 粉起号歧义）
- 工具：PhotoRoom / PixelMator / Photoshop 打马赛克
- 输出：`assets/screenshot/raw/w28d04_M5_400w.png` + `w28d04_M5_800.png`

### 1.4 4 段 prompt 家居收纳版全文（用于 M7 屏录）

**声明：** 家居收纳是 D04 演示 skin（不推广具体家居品牌 · 与内容 skin 一致）

需在开工前写完 · 4 段结构：
- 身份卡：本账号定位（如「家居收纳 · 30 岁小家庭主妇 · 3 房 1 厅 · 2 猫 1 娃」）
- 账号定位：（如「粉丝 800 · 已发 42 条 · 收纳类 aov ≥3 · 期望 30 天涨 5000）
- 粉丝痛点：（如「租房不能改造 · 猫抓东西没处放 · 老公不配合」）
- 输出约束：（10 条候选 · 表格结构 = 标题/场景/钩子/成本/差异化 · 每条 ≤30 字）

**产出位置：** `publish/2026-W28/D04-AI帮想视频选题/design/prompt_4_segments_home_organization.md`
**门禁：** 若无此文件 · S3 屏录无法开始（M7 15s 主场用不了）

### 1.5 UI 叠层 PNG 生成（开发 `gen_ui_w28d04.py`）

**建议路径：** `pipeline/p004_video/gen_ui_w28d04.py`（学 D03 `gen_ui_w28d03.py` 结构）

**需生成的 PNG（对齐 pipeline_config.yaml.scenes.src_rel）：**
1. `build/assets_ui/03_m3_display_reveal_dark.png` · display 140pt 白字两行「打帮我想 10 个 / AI 全给如何做好」· canvas_office_dark 底
2. `build/assets_ui/05_m5_split_400w_vs_800.png` · 分屏 hstack 两张真机截图 + 2px 白分割线 + drawtext 大字
3. `build/assets_ui/08_m8_5criteria_table_dark.png` · 10 行 × 5 列 SVG 表格 + accent_green 打勾 × 8 + accent_red 打叉 × 2 + headline 大结论
4. `build/assets_ui/09_m9_anti_tutorial_dark.png` · canvas_office_dark + display 140pt 白字两行「不是教你」/「是把 4 段 prompt 给你」
5. `build/assets_ui/10_m10_cta_dark.png` · CTA headline 88pt + caption 底部小字

**颜色约束（design_language.md 硬门）：**
- canvas_office_dark: `#1a1a1a`
- ink_light: `#f5f5f0`（白字）
- accent_soft: `#ffc857`（淡黄）
- accent_green: `#4caf50`（打勾）
- accent_red: `#e53935`（打叉/红叉/描边 · 禁 `#ff5252` 偏粉红）
- **禁 Dracula 霓虹**：`#bd93f9` / `#ff79c6` / `#8be9fd`（gate_check_palette.py 硬拦）

### 1.6 sfx CC0 素材拉取（10 项 · Freesound）

对齐 `audio_plan.yaml.assets_prep.sfx_can_auto_fetch`：

| sid | kind | 关键词 | 目录 |
|-----|------|--------|------|
| sfx01 | ambient | `office room tone daylight` 或 `ac hum low frequency` | `assets/sfx/ambient/` |
| sfx02 | tick | `keyboard single tap soft` | `assets/sfx/tick/` |
| sfx03 | tick_seq | 用户 QuickTime 屏录 M2 自带打字音（推荐 · 更同频） | 或 `keyboard typing sequence` |
| sfx04 | tick | `keyboard enter key press` | `assets/sfx/tick/` |
| sfx05-07 | whoosh | `whoosh transition swish` × 3（不同变体） | `assets/sfx/whoosh/` |
| sfx08 | hit | `impact soft boom cinematic` | `assets/sfx/hit/` |
| sfx10-16 | hit | `impact boom soft` + `impact hard cut` | `assets/sfx/hit/` |
| sfx17-20 | whoosh | `whoosh soft transition` × 1（4 处复用） | `assets/sfx/whoosh/` |
| sfx21-30 | hit_seq | `soft click check mark` + `cross click soft` | `assets/sfx/hit/` |
| sfx32 | hit | `impact deep resonance`（M9 深长版） | `assets/sfx/hit/` |

**铁律：** 禁 ffmpeg aevalsrc/sine/棕噪合成假 sfx（memory: `feedback_no-synth-bgm`）

## 2. 前置校验（fail-closed 门禁）

### 2.1 TTS 时长前置估算（硬门 · memory: `tts-estimate-duration-pre-synth`）

```bash
python pipeline/tts/estimate_duration.py \
  --config publish/2026-W28/D04-AI帮想视频选题/audio_plan.yaml \
  --output publish/2026-W28/D04-AI帮想视频选题/build/tts_duration_estimate.json
```

**门禁：**
- 单段溢出 >10% → 预警（可继续）
- 单段溢出 >30% → **fail-closed · 按 audio_plan.overrun_action 改稿**
- **D04 已识别高溢出风险段位：**
  - M6（15-25s · char=62 · est=11.2s · 溢出 12%）→ speed 已提到 1.00 · 若仍 >30% 用 overrun_fallback
  - M9（48-54s · char=41 · est=7.4s · 溢出 23%）→ speed 已提到 1.00 · 若仍 >30% 用 overrun_fallback
  - M10（54-58s · char=38 · est=6.9s · 溢出 72% SEVERE）→ speed 已提到 1.05 · 若仍 >30% **必用 overrun_fallback**「私信「账号方向」——我给 5 条选题。不推服务。」

### 2.2 色板兜底

```bash
# render 完后必跑（对每张 PNG + 中间帧）
python pipeline/gate_check_palette.py build/assets_ui/*.png
```

**门禁：** Dracula H=240~290（蓝紫）占比 >5% → fail-closed（直接删素材重做）

## 3. 主 render 命令

```bash
# 前置资产齐 + TTS 估算过关后执行
python pipeline/p004_video/run_pipeline.py \
  --config publish/2026-W28/D04-AI帮想视频选题/pipeline_config.yaml \
  --step all
```

**步骤（run_pipeline.py 内置）：**
1. `step_vo`：MiniMax TTS 逐段合成 → concat → loudnorm -16 → `build/vA_no_bgm.wav`
2. `step_preview`：scenes 合成 → concat → 挂 VO → `build/preview_no_bgm.mp4`
3. `step_platforms`：三平台字号（42/50/42）+ overlays drawtext + ffmpeg 一次性烧 → `build/w28d04_douyin_no_bgm.mp4` / `xhs` / `weixin`
4. `step_ui`（如需）：预生成 UI PNG（若 `gen_ui_w28d04.py` 未跑）

**字幕烧片：**
- 由 `pipeline/p004_video/lib/subs.py` 自动生成 SRT + ASS
- 用 `/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg`（libass 支持 · 系统 ffmpeg 无 libass）
- memory: `feedback_pipeline-burn-subs`

## 4. 交付验收清单

- [ ] `build/w28d04_douyin_no_bgm.mp4`（58s · 1080×1920 · 42pt 字幕）
- [ ] `build/w28d04_xhs_no_bgm.mp4`（58s · 50pt 字幕 · 若走小红书视频版；主推 xhs_carousel 7 页）
- [ ] `build/w28d04_weixin_no_bgm.mp4`（58-65s · 42pt 字幕）
- [ ] `build/xhs_carousel_p{1-7}.png`（7 页轮播 · 分辨率 1080×1350 · 由 `pipeline/p002_carousel_gen.py` 或 `gen_ui_w28d04.py` 生成）
- [ ] `build/tts_duration_estimate.json`（前置估算结果）
- [ ] `build/sfx_mix.log`（sfx 34 events 混音日志）

## 5. 阻塞情况处理

**若无法本机跑 QuickTime 屏录：**
- 走 vB v2 备胎路径（M2/M3/M6/M7 全部改用 UI PNG 静态版）
- 需回改 `pipeline_config.yaml.scenes` 的 src_type: broll → img
- 增加 `gen_ui_w28d04.py` 生成 UI PNG 数量

**若无法拉 Pexels 白天素材：**
- 用 canvas_office_dark 灰底 + drawtext「(白天办公 3800-4200K)」占位测试渲染链路
- 但**不外发**（chaos_must_be_real_footage 硬门）

**若 TTS 全段仍溢出 >30%：**
- 优先用各段 overrun_fallback
- 极端情况延总时长到 60s（抖音上限内）· 但需回改 storyboard 段位

## 6. 变更历史

| 日期 | 版本 | 说明 |
|------|------|------|
| 2026-07-05 | v1.0 | 新建 · 步 12 config-driven 前置文档 · 6 类资产 gap 明列 · TTS 前置估算硬门声明 · M6/M9/M10 高溢出 overrun_action 3 段备案 |
| 2026-07-05 | v2.0 | A-fix · 删 0-3s 沉默钉子 · 双平台化 · 二次外发 |

## 7. A-fix 二次外发（2026-07-05 下午）

### 触发
用户 2026-07-05 反馈："前 3 秒只有画面没有音效、没有配音，3s 完播率还能看吗"

### 根因
1. **sfx-mixer P1 task #67 未实施** · audio_plan.yaml 34 sfx events 仅为声明，未真的烧入 VO
2. **违反 memory feedback_dense-vo-no-dead-air** · "视频前 6s 禁沉默钉子设计"
3. **agent 未在交付前听 vo_w28d04.mp3 前 5s 波形** · 形式监控盲区

### 用户决策（三选一 · 选 A）
- **A：删 0-3s 沉默钉子（选中）** · 抖音 + 小红书均删
- B：sfx 补 · 拒（sfx-mixer 未实施）
- C：VO hook 补 · 拒（改写增开销）

### Config diff

| 项 | v1 | v2 (A-fix) |
|---|----|-----------|
| TTS 段数 | 8（s1_silence + s2-s8）| 7（s2-s8 target_start -3s） |
| Scenes | 10（M1-M10） | 7（M4-M10） |
| Overlays | 8 | 8（t_start/t_end -3s） |
| Platforms | douyin + xhs + weixin | douyin + xhs（memory `feedback_dual-platform-only`） |
| tts.target_total_cap | 无 | 60.0 |

### 估算 vs 实测

| 指标 | v1 (silence nail) | v2 (A-fix) |
|-----|-------------------|-----------|
| 估算总长 | 62.35s | 53.96s |
| MiniMax 实发 | 62.77s | 59.45s |
| 抖音 60s 上限 | 超 2.77s（当时无 target_total_cap gate） | 0.55s 内 |
| CTA ship gate | pass（scene 61.99s ≥ seg 57.67s） | pass（seg 59.45s ≤ plan 59.77s · Δ=-0.32s） |
| buffer 精度 | — | 预测 59.36s vs 实测 59.45s · 差 0.09s |

### 输出
- `douyin/video_no_bgm.mp4` · 59.45s / 4.4 MB / 42pt 字幕
- `xhs/video_no_bgm.mp4` · 59.45s / 4.4 MB / 50pt 字幕
- ~~`weixin/`~~ 停做

### D05 承接
- P1 task #66-70（sfx-catalog / sfx-mixer / bgm-catalog / sfx-fetcher / sfx-search-helper）尚未启动
- D05 前 6s 若为密 VO 演示型（本条同样）· 不再需 sfx 兜底 · 走 VO 从 0s 覆盖路径
- xhs 形态判定移到形式策略官（本条为视频；D05 起 xhs 视频/图文由 form_strategy 判定）
