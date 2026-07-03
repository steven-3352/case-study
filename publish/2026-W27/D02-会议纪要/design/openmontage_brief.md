# OpenMontage 制作 brief · W27D02 会议纪要

> 工种：OpenMontage 制作导演  
> 状态：enabled-for-trial  
> 使用时机：`form_strategy.md` + `design_language.md` 完成后，外部制作前。

> Superseded for production: this file is the original trial brief. For any production-grade OpenMontage pass, use `publish/2026-W27/D02-会议纪要/openmontage_request.md` as the source of truth.

## 0. 启用判断

```yaml
enabled: true
content_id: W27D02
platform: douyin
target_duration_s: 40
recommended_pipeline: hybrid_meeting_montage
render_runtime: external_openmontage_preferred_local_surrogate_now
budget_usd: 0
budget_mode: cap
target_metric: completion_3s / completion_rate / 理解
decision: enabled
```

### 判断结论

- **是否启用 OpenMontage：** 是，作为一次不覆盖原片的试点。
- **一句话理由：** 这条原生版已经能讲清楚，但仍偏“插画 + UI 卡片”，OpenMontage 路线适合验证真实会议蒙太奇、手机消息、待办追踪和分屏反差是否能提升视频感。
- **服务的北极星指标：** 3s 停划、完播率、理解速度。
- **为什么当前项目原生路线不够：** 原生成片依赖 GPT-image 插画底图和 HTML 卡片，信息清楚但“真实职场现场感”和“视频流动感”不足。
- **为什么 OpenMontage 会更强：** 可引入真实 B-roll / 参考节奏拆解 / 混剪式节奏 / QA 回流，强化“散会瞬间”的代入。

### 禁止理由自检

- [x] 不是因为“更酷 / 更电影感 / 更高级”。
- [x] 有明确提升 `completion_3s` / `completion_rate` / 理解 的假设。
- [x] 不改写当前项目已通过的核心脚本或价值锚。
- [x] 不是简单图文轮播或大字卡片视频。
- [x] 当前 P004 已能完成，但试点要验证更强视频感是否值得。

## 1. 输入文档

| 输入 | 路径 | 状态 | OpenMontage 使用方式 |
|------|------|------|----------------------|
| meta | `publish/2026-W27/D02-会议纪要/meta.yaml` | ready | 锁定平台、时长、版本 |
| chosen script | `scripts/script_three_versions.md` vA | ready | 锁定口播，不改写 |
| retention_beat_sheet | `retention_beat_sheet.md` | ready | 锁定 0-3s / 5-8s 节拍 |
| form_strategy | `design/form_strategy.md` | ready | 锁定画面任务与数据杠杆 |
| design_language | `design/design_language.md` | ready | 约束色板、组件、字体 |
| storyboard | `design/storyboard.yaml` | ready | 作为镜头承诺基础 |
| audio_plan | `design/audio_plan.yaml` | ready | 使用原片音频作为试点音轨 |
| publish copy | `douyin/publish.md` | ready | 锁定标题与 CTA |

## 2. 不可改内容

- 核心选题：开完会就走，纪要和待办 AI 已发群。
- 价值锚：人负责讨论拍板，记录和追办不该靠人脑。
- 事实边界：不承诺 AI 替人决策；不写死准确率/节省分钟；不绑定具体 SaaS。
- 禁用表达：品牌 UI 仿冒、真实客户后台、伪造群聊。
- CTA：你们公司开会，纪要是谁在整理？是不是最烦的活？
- 平台限制：抖音 9:16，40s，不私信导流。

## 3. Pipeline 选择

| 候选 pipeline | 适配度 | 成本 | 风险 | 结论 |
|---------------|--------|------|------|------|
| documentary montage | 高 | 中 | 真实素材授权 | 外部 OpenMontage 首选 |
| screen demo | 中 | 低 | 容易像工具演示 | 可作为中段补充 |
| animated explainer | 中 | 低 | 与原生 P004 接近 | 非首选 |
| cinematic | 低 | 高 | 可能喧宾夺主 | 不选 |
| hybrid | 高 | 中 | 需控信息可读性 | 本次推荐 |

**推荐 pipeline：** hybrid meeting montage。

**不选其他 pipeline 的原因：** 纯 animated explainer 与原生版差异不足；纯 cinematic 不利于看懂待办；纯 screen demo 缺少散会现场反差。

## 4. 画面承诺

### 必须出现

| 时间段 / 镜头 | 画面承诺 | 来源 | 验收方式 |
|---------------|----------|------|----------|
| 0-3s | 会议室散会，同事还在整理，我起身离开，群消息弹出 | `meeting_room.png` / 外部 B-roll | 首帧和 2s 抽帧能看懂反差 |
| 3-11s | 纪要卡已自动发群 | HTML/UI overlay | 抽帧可读“纪要已发群” |
| 11-22s | 待办带责任人、deadline、@、提醒 | HTML/UI overlay | 至少一帧完整读到待办字段 |
| 22-30s | 旧流程熬夜整理 vs 新流程自动追办 | `tired.png` / `relaxed.png` | 分屏反差明确 |
| 30-40s | 自证 + 评论 CTA | `me_phone.png` | CTA 完整可读 |

### 禁止出现

- 真实品牌 UI 仿冒。
- 未授权人物、logo、公司名。
- 修改脚本价值锚。
- 只用抽象科技背景替代会议场景。

### 素材类型

| 类型 | 是否需要 | 来源偏好 | 备注 |
|------|----------|----------|------|
| 真实 B-roll | 外部 OpenMontage 推荐 | Pexels / 自有 / Archive | 本地 surrogate 暂用 GPT-image |
| 屏幕录制 | 可选 | 当前项目仿真 UI | 不冒充真实后台 |
| AI 图像 | 已有 | GPT-image | `assets/characters/w27d02/` |
| AI 视频 | 暂不需要 | - | 控成本 |
| 音乐 | 使用原片 | 原片音轨 | 试点不新增 |
| 音效 | 可选 | 本地/外部 | 本地 preview 暂不新增 |

## 5. 视觉语言约束

必须遵守 `design/design_language.md`：

- 色板：浅灰 canvas、白色 surface、蓝色 accent、绿色 success、红色 contrast。
- 字体层级：0-3s display，卡片 body/data，CTA headline。
- 组件规则：群消息卡、纪要卡、待办卡、分屏反差、CTA。
- Do：保持中文清晰，焦点单一，卡片少而准。
- Don't：品牌仿冒、随机渐变、装饰泛滥、文字拥挤。

## 6. 字幕与声音

- VO 来源：原生成片音轨 / `pipeline/p004_video/out/audio_d02/vo_d02_padded.mp3`。
- 字幕样式：本地预览用大字卡 + 原片音频，不重新烧全量逐字字幕。
- 字幕位置：底部安全区以上，不压核心卡片。
- BGM 风格：沿用原片，轻快职场节奏。
- 音量 / ducking：沿用原片混音。
- 禁止项：BGM 盖过 VO、字幕遮挡责任人/deadline。

## 7. 输出路径

```text
publish/2026-W27/D02-会议纪要/openmontage/preview.mp4
publish/2026-W27/D02-会议纪要/openmontage/final.mp4
publish/2026-W27/D02-会议纪要/openmontage/asset_log.md
publish/2026-W27/D02-会议纪要/openmontage/decision_log.md
```

不得直接写入：

```text
publish/2026-W27/D02-会议纪要/douyin/video_with_bgm.mp4
```

## 8. 回流验收标准

- [ ] 内容没有偏离 chosen script。
- [ ] 0-3s 停划比当前原生路线更强。
- [ ] 中段不是 PPT 式堆字。
- [ ] 字幕、音频、BGM 不抢主信息。
- [ ] 视觉语言约束有像素兑现。
- [ ] 素材来源可追溯。
- [ ] 成本未超预算。
- [ ] 相比 P004 原生路线有明确收益。

## 9. 制作导演签字

- **OpenMontage 制作导演：** pass-for-trial
- **编导采纳：** trial-only
- **下一步：** 生成 `openmontage/preview.mp4`，再填写 `design/openmontage_review.md`
