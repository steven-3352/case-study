# OpenMontage 回流验收 · W27D02 会议纪要

> 工种：OpenMontage 制作导演 + 编导 + 平台表现分析师  
> 使用时机：OpenMontage / local surrogate 输出 `preview.mp4` / `final.mp4` 后。  
> 结论：**trial_pass_for_route · not_approved_for_platform_dir**

## 0. 基本信息

```yaml
content_id: W27D02
source_brief: design/openmontage_brief.md
preview_video: openmontage/preview.mp4
final_video: openmontage/final.mp4
asset_log: openmontage/asset_log.md
decision_log: openmontage/decision_log.md
review_status: trial_pass_for_route
approved_for_platform_dir: false
```

## 1. 文件检查

| 文件 | 是否存在 | 备注 |
|------|----------|------|
| `openmontage/preview.mp4` | yes | 40s · 1080x1920 · 有音轨 |
| `openmontage/final.mp4` | yes | 当前为 preview copy，作为候选文件，不替换原片 |
| `openmontage/asset_log.md` | yes | 记录了 GPT-image 素材与原片音轨 |
| `openmontage/decision_log.md` | yes | 明确外部 OpenMontage 未执行，本次为 local surrogate |
| `openmontage/build_preview.py` | yes | 仅 D02 试点用，不接入主 pipeline |

## 2. 内容一致性

| 检查项 | 结论 | 备注 |
|--------|------|------|
| 未改变选题方向 | pass | 仍是“散会我先走，纪要待办自动发群” |
| 未新增未经验证卖点 | pass | 未新增准确率、省时数字或品牌承诺 |
| 价值锚一致 | pass | “人讨论拍板，记录追办交给系统”保留 |
| CTA 一致 | pass | “纪要是谁整理 / 是不是最烦”保留 |
| 事实红线清零 | pass | 无真实后台冒充，无品牌 UI 仿冒 |

## 3. 画面承诺兑现

| brief 承诺 | 最终视频位置 | 是否兑现 | 备注 |
|------------|--------------|----------|------|
| 0-3s 散会反差 + 群消息 | 0-3s | pass | 首帧可见会议室、离开的人、整理的人、纪要待办卡 |
| 3-11s 纪要已发群 | 3-11s | pass | “会议主题 / 决策 / 要点”可读 |
| 11-22s 待办 @ + deadline | 11-22s | pass | 责任人、时间、@ 状态可读 |
| 22-30s 旧流程 vs 新流程 | 22-30s | partial | 分屏明确，但右侧人物性别与男性叙事不一致 |
| 30-40s 自证 + CTA | 30-40s | pass | CTA 可读，未遮挡主体 |

## 4. 视觉语言兑现

对照 `design/design_language.md`：

| 项 | 结论 | 备注 |
|----|------|------|
| 色板兑现 | pass | 浅灰、白卡、蓝 accent、绿 success、红 contrast 可见 |
| 字体层级清楚 | pass | display/headline/body 层级清楚 |
| 组件规则兑现 | pass | 群消息卡、纪要卡、待办卡、分屏、CTA 均可见 |
| 单焦点路径清楚 | pass | 每镜主要焦点明确 |
| 没有品牌仿冒 | pass | 未使用飞书/企微/钉钉品牌元素 |
| 没有随机渐变 / 装饰泛滥 | pass | 视觉克制 |

## 5. 视频技术 QA

| 检查项 | 结论 | 备注 |
|--------|------|------|
| 分辨率 1080x1920 | pass | ffprobe confirmed |
| 时长符合平台规格 | pass | 40.000s |
| 有音轨 | pass | AAC mono 44.1kHz，取自原片 |
| 无黑屏 / 空白段 | pass | 抽帧 5 张均正常 |
| 字幕不遮挡主体 | pass | 大字主要位于安全区 |
| 字幕与 VO 同步 | partial | 使用原片音轨，但画面是静态分段预览，非逐字字幕同步 |
| BGM 不盖过人声 | pass | 沿用原片混音 |

ffprobe 摘要：

```text
video: h264 1080x1920 30fps
audio: aac 44100 Hz mono
duration: 40.000000
size: 2693067
```

抽帧：

```text
/tmp/w27d02_openmontage_frames/frame_01.png
/tmp/w27d02_openmontage_frames/frame_02.png
/tmp/w27d02_openmontage_frames/frame_03.png
/tmp/w27d02_openmontage_frames/frame_04.png
/tmp/w27d02_openmontage_frames/frame_05.png
```

## 6. 素材与授权

| 素材 | 来源 | 授权 / 备注 | 是否可用 |
|------|------|-------------|----------|
| 会议室、人物、手机图 | GPT-image 既有素材 | 内部试点可用 | yes |
| 原片音轨 | 当前项目原生成片 | 内部复用 | yes |
| 外部 B-roll | 未使用 | 外部 OpenMontage 正式版应补 | n/a |

检查项：

- [x] 真实素材来源可追溯。
- [x] AI 生成素材有路径记录。
- [x] 不含未授权 logo / 商标 / 人脸。
- [x] 未冒充真实客户后台。

## 7. 与当前项目原生路线对比

| 维度 | 当前 P004 路线 | OpenMontage local surrogate | 胜出 |
|------|----------------|-----------------------------|------|
| 0-3s 停划 | 已有动效与音画同步 | 首帧反差更直接，但静态 | 接近 |
| 看懂速度 | 原版逐镜动效更完整 | 卡片字段更大、更清楚 | surrogate 小胜 |
| 中段视频感 | 有 HTML/GSAP 动效 | 静态分段，视频感不足 | 原生 |
| 证据感 | GPT-image + 解释性 UI | 同素材，未加入真实 B-roll | 接近 |
| 收藏 / 评论钩 | 原片 CTA 完整 | CTA 可读，但缺字幕同步 | 原生 |
| 制作成本 | 已完成 | 低成本可复现 | surrogate |
| 稳定性 | 已发布包结构稳定 | 试点脚本独立，未进主线 | 原生 |

**是否明显优于原生路线：** 否。它验证了插件接口，但还不足以替换原生成片。

## 8. 平台表现预估

本节摘要可写入未来 `design/pre_publish_forecast.md`。

| 指标 | OpenMontage local surrogate 预估 | 依据 |
|------|----------------------------------|------|
| 3s 完播 | 接近原片或略高 | 首帧反差清楚，但缺动态钩子 |
| 完播率 | 可能低于原片 | 静态分段，40s 中段动效不足 |
| 平均观看 | 中等 | 字段清楚，但画面变化少 |
| 评论 / 收藏 | 接近原片 | CTA 可读，问题具体 |
| 风险 | 中 | 性别不一致、非真实 OpenMontage 输出、逐字字幕不同步 |

## 9. 结论

```yaml
content_pass: true
form_pass: true
technical_pass: true
asset_pass: true
better_than_native_route: false
approved_for_platform_dir: false
trial_learning_pass: true
```

### 处理决定

- [ ] 通过：复制 `openmontage/final.mp4` 到平台目录。
- [ ] 退回 OpenMontage 重做。
- [x] 保留为插件路线试点，不替换原生视频。
- [x] 若进入正式 OpenMontage，需要补真实 B-roll / 更强运动 / 修复 gender mismatch / 逐字字幕同步。

### 签字

- OpenMontage 制作导演：trial pass
- 编导：不替换原片
- 平台表现分析师：保留为路线验证，不外发
