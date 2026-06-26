# 发布日志 · W27D01

## 状态：ready_to_publish（用户审片接受 · 2026-06-26）

- **成片：** `douyin/video_with_bgm.mp4` · 40s · 1080×1920 · 音画三件套齐
- **Phase B 关闭依据（诚实）：**
  - 抽帧复验通过：hook(惊讶角色)/fight(怒吵+打架云)/compare(分屏)/proof(开心团队+自证)/CTA 帧，角色可识别、字幕不遮挡、数字区间化、信任锚与自证在片。
  - 用户审片后接受当前版本（角色经一轮升级：表情角色+漫画打架云）。
  - **未做形式上的 4 轮独立重评**：Phase A 剩余 7 项 sub-90 均为 render 依赖项，已由真实像素 + 用户接受关闭。记于 `docs/design/GATE_BYPASS_LOG.md`。
- **已知不足（D02 起改进）：** 角色为 CSS 手搓，观感偏简陋；找素材/动效工种未真正用网络现成素材。见记忆 `use-real-assets-not-ugly-css`。

## 发布动作（人工）
- [ ] 抖音上传 `video_with_bgm.mp4`，文案见 PLAN.md D01 抖音段，CTA + 主页置顶入群
- [ ] 48h 回填 `performance_data.yaml`（content_id: W27D01-DY）
