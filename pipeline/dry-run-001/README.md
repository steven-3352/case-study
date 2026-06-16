# Project-001 空跑 · 海外品牌自动化获客

> content_id: DRY-001 · topic: T001 · variant: P001-A
> 状态: draft

## 说明

首期用**自己做的真实项目**打磨 pipeline（配音、剪辑、多形态）。**数字人暂停，视频不出真人。**
辩论结论见 `docs/DECISIONS.md` Q5。

## 文件

| 文件 | 状态 |
|------|------|
| script.md | draft |
| speech.mp3 | Edge TTS 生成（不入库） |
| ~~avatar_raw.mp4~~ | 暂停（不做数字人） |
| douyin.mp4 | pending |
| xhs_video.mp4 | pending |
| carousel/ | pending |
| publish.md | pending |
| feedback.md | pending |

## 可复用素材

| 来源 | 用途 |
|------|------|
| `build_shots.py` | 真实页面帧 |
| `slides/` | 图文补充（降级，不作主视觉） |
| `legacy/发布/图文_A_故事踩坑/` | 文案 + 配图顺序参考 |
| `out/case_study_narrated.mp4` | Edge TTS 完整草稿参考 |

## 生成口播（Edge TTS）

```bash
python3 pipeline/tts/gen_speech.py \
  --script pipeline/dry-run-001/script.md \
  -o pipeline/dry-run-001/speech.mp3
```

音色见 `pipeline/tts/config.yaml`。

## 剪映构图（当前默认）

| 轨道 | 内容 |
|------|------|
| 视频轨（全屏） | B-roll：录屏 / 后台数据 / 落地页 / 截图 |
| 音频轨 | `speech.mp3` |
| 字幕轨 | 口播字幕，前 1s 大字钩子 |

**不做：** 真人/数字人出镜、画中画小窗、纯架构 PPT 主画面。

## B-roll 映射

| 脚本段落 | 素材 ID |
|----------|---------|
| 15–35s 过程 | BR001–BR003 |
| 35–50s 改法 | BR006, BR007 |
| 图文 | 见 `legacy/发布/图文_A_故事踩坑/` 顺序 |

## Project-001 其他形态（Phase 1 发布测效果）

| 形态 | 路径 | 平台 |
|------|------|------|
| A 故事踩坑 | legacy/发布/图文_A | 小红书 |
| B 干货拆解 | legacy/发布/图文_B | 小红书 |
| C 成长视频 | legacy/发布/视频_C成长 | 抖音+小红书 |
| D 视频号复盘 | 待产 | 视频号 |
