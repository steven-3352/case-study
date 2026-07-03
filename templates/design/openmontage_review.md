# OpenMontage 回流验收

> 工种：**OpenMontage 制作导演 + 编导 + 平台表现分析师**  
> 使用时机：OpenMontage 输出 `preview.mp4` / `final.mp4` 后，复制到平台发布目录前。  
> 结论：本文件 pass 前，`openmontage/final.mp4` 不得替换 `douyin/video.mp4`。

## 0. 基本信息

```yaml
content_id:
source_brief: design/openmontage_brief.md
preview_video: openmontage/preview.mp4
final_video: openmontage/final.mp4
asset_log: openmontage/asset_log.md
decision_log: openmontage/decision_log.md
review_status: pending       # pass / fail / blocked
```

## 1. 文件检查

| 文件 | 是否存在 | 备注 |
|------|----------|------|
| `openmontage/preview.mp4` | | |
| `openmontage/final.mp4` | | |
| `openmontage/asset_log.md` | | |
| `openmontage/decision_log.md` | | |

## 2. 内容一致性

| 检查项 | 结论 | 备注 |
|--------|------|------|
| 未改变选题方向 | pass / fail | |
| 未新增未经验证卖点 | pass / fail | |
| 价值锚一致 | pass / fail | |
| CTA 一致 | pass / fail | |
| 事实红线清零 | pass / fail | |

失败处理：回到当前项目 `script_review.md` / `fact_check.md` 重评，不得直接外发。

## 3. 画面承诺兑现

| brief 承诺 | 最终视频位置 | 是否兑现 | 备注 |
|------------|--------------|----------|------|
| 0–3s | | | |
| 中段 | | | |
| 结尾 | | | |

## 4. 视觉语言兑现

对照 `design/design_language.md`：

| 项 | 结论 | 备注 |
|----|------|------|
| 色板兑现 | pass / fail | |
| 字体层级清楚 | pass / fail | |
| 组件规则兑现 | pass / fail | |
| 单焦点路径清楚 | pass / fail | |
| 没有品牌仿冒 | pass / fail | |
| 没有随机渐变 / 装饰泛滥 | pass / fail | |

## 5. 视频技术 QA

| 检查项 | 结论 | 备注 |
|--------|------|------|
| 分辨率 1080×1920 | pass / fail | |
| 时长符合平台规格 | pass / fail | |
| 无黑屏 / 空白段 | pass / fail | |
| 无静音异常 | pass / fail | |
| 无音频削波 | pass / fail | |
| 字幕不遮挡主体 | pass / fail | |
| 字幕与 VO 同步 | pass / fail | |
| BGM 不盖过人声 | pass / fail | |

建议记录 `ffprobe` / 抽帧 / 音频分析摘要：

```text

```

## 6. 素材与授权

| 素材 | 来源 | 授权 / 备注 | 是否可用 |
|------|------|-------------|----------|
| | | | |

检查项：

- [ ] 真实素材来源可追溯。
- [ ] AI 生成素材有 provider / prompt / 成本记录。
- [ ] 不含未授权 logo / 商标 / 人脸。
- [ ] 打码符合事实校验与合规要求。

## 7. 与当前项目原生路线对比

| 维度 | 当前 P004/P007 路线 | OpenMontage 版本 | 胜出 |
|------|---------------------|------------------|------|
| 0–3s 停划 | | | |
| 看懂速度 | | | |
| 中段视频感 | | | |
| 证据感 | | | |
| 收藏 / 评论钩 | | | |
| 制作成本 | | | |
| 稳定性 | | | |

**是否明显优于原生路线：** 是 / 否

## 8. 平台表现预估

本节摘要写入 `design/pre_publish_forecast.md`。

| 指标 | OpenMontage 版本预估 | 依据 |
|------|----------------------|------|
| 3s 完播 | | |
| 完播率 | | |
| 平均观看 | | |
| 评论 / 收藏 | | |
| 风险 | | |

## 9. 结论

```yaml
content_pass: false
form_pass: false
technical_pass: false
asset_pass: false
better_than_native_route: false
approved_for_platform_dir: false
```

### 处理决定

- [ ] 通过：复制 `openmontage/final.mp4` 到平台目录。
- [ ] 退回 OpenMontage 重做。
- [ ] 放弃 OpenMontage，回当前项目原生路线。
- [ ] 只保留为内部参考，不外发。

### 签字

- OpenMontage 制作导演：
- 编导：
- 平台表现分析师：
