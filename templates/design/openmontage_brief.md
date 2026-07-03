# OpenMontage 制作 brief

> 工种：**OpenMontage 制作导演**  
> 状态：可选插件输入 · 不替代当前项目内容门 / 形式门  
> 使用时机：`form_strategy.md` + `design_language.md` 完成后，进入 storyboard / render 前。

## 0. 启用判断

```yaml
enabled: false
content_id:
platform: douyin
target_duration_s:
recommended_pipeline:
render_runtime:              # Remotion / HyperFrames / FFmpeg / undecided
budget_usd:
budget_mode: cap             # observe / warn / cap
target_metric:               # completion_3s / completion_rate / 理解 / 收藏 / 评论
decision: blocked            # enabled / disabled / blocked
```

### 判断结论

- **是否启用 OpenMontage：** 是 / 否
- **一句话理由：**
- **服务的北极星指标：**
- **为什么当前项目原生路线不够：**
- **为什么 OpenMontage 会更强：**

### 禁止理由自检

以下任一项为真，则不得启用：

- [ ] 只是因为“更酷 / 更电影感 / 更高级”。
- [ ] 没有明确提升 `completion_3s` / `completion_rate` / 理解 / 收藏 / 评论。
- [ ] 会改写当前项目已通过的核心脚本或价值锚。
- [ ] 只是简单图文轮播或大字卡片视频。
- [ ] 当前 P004/P007 已能稳定完成且表现力足够。

## 1. 输入文档

| 输入 | 路径 | 状态 | OpenMontage 使用方式 |
|------|------|------|----------------------|
| meta | | | |
| chosen script | | | |
| retention_beat_sheet | | | |
| form_strategy | | | |
| design_language | | | |
| storyboard | | | |
| audio_plan | | | |
| publish copy | | | |

## 2. 不可改内容

OpenMontage 制作时不得改动以下内容：

- 核心选题：
- 价值锚：
- 事实边界：
- 禁用表达：
- CTA：
- 平台限制：

## 3. Pipeline 选择

| 候选 pipeline | 适配度 | 成本 | 风险 | 结论 |
|---------------|--------|------|------|------|
| documentary montage | | | | |
| screen demo | | | | |
| animated explainer | | | | |
| cinematic | | | | |
| hybrid | | | | |

**推荐 pipeline：**

**不选其他 pipeline 的原因：**

## 4. 画面承诺

### 必须出现

| 时间段 / 镜头 | 画面承诺 | 来源 | 验收方式 |
|---------------|----------|------|----------|
| 0–3s | | | |
| 中段 | | | |
| 结尾 | | | |

### 禁止出现

- 
- 
- 

### 素材类型

| 类型 | 是否需要 | 来源偏好 | 备注 |
|------|----------|----------|------|
| 真实 B-roll | | Archive / Pexels / Wikimedia / 自有 | |
| 屏幕录制 | | 当前项目 / 自录 | |
| AI 图像 | | OpenAI / FLUX / 其他 | |
| AI 视频 | | Kling / Runway / Veo / 其他 | |
| 音乐 | | 免版税 / Suno / ElevenLabs | |
| 音效 | | ElevenLabs / 本地库 | |

## 5. 视觉语言约束

必须遵守 `design/design_language.md`：

- 色板：
- 字体层级：
- 组件规则：
- Do：
- Don't：

OpenMontage 输出若无法兑现这些约束，须在 `decision_log.md` 中说明并回到当前项目重评。

## 6. 字幕与声音

- VO 来源：
- 字幕样式：
- 字幕位置：
- BGM 风格：
- 音量 / ducking：
- 禁止项：

## 7. 输出路径

```text
publish/{week}/Dxx-*/openmontage/preview.mp4
publish/{week}/Dxx-*/openmontage/final.mp4
publish/{week}/Dxx-*/openmontage/asset_log.md
publish/{week}/Dxx-*/openmontage/decision_log.md
```

不得直接写入：

```text
publish/{week}/Dxx-*/douyin/video.mp4
```

只有 `design/openmontage_review.md` pass 后，才允许进入平台发布目录。

## 8. 回流验收标准

- [ ] 内容没有偏离 chosen script。
- [ ] 0–3s 停划比当前原生路线更强。
- [ ] 中段不是 PPT 式堆字。
- [ ] 字幕、音频、BGM 不抢主信息。
- [ ] 视觉语言约束有像素兑现。
- [ ] 素材来源可追溯。
- [ ] 成本未超预算。
- [ ] 相比 P004/P007 原生路线有明确收益。

## 9. 制作导演签字

- **OpenMontage 制作导演：** pass / fail
- **编导采纳：** pass / fail
- **下一步：** 不启用 / 人工试点 / 导出 request / 回当前项目原生路线
