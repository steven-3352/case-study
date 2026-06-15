# 自动化获客系统 · 实战案例(图文 + 视频)

一个**半匿名**的自动化交付案例素材包,用于获客(展示"端到端搭全自动获客系统"的能力)。
载体是某海外女性向生活方式 DTC 品牌(品牌名与具体 niche 已隐去)。

## 成品
- **图文轮播**:`slides/slide_01.png … slide_11.png`(1080×1920,9:16)
- **视频**:`out/case_study_narrated.mp4`(竖屏,带中文配音,约 140s)
- **发布文案**:`article.md`(标题/正文/标签,直接复制)
- **配音文案与做法**:`voiceover.md`

## 11 张结构
01 封面 · 02 系统全景 · 03 邮件全自动 · 04 项目背景 · 05 落地承接 ·
06 内容生产 · 07 数据闭环 · 08 技术栈&成本 · 09 交付速度 · 10 当前进度 · 11 行动号召

## 重新生成
```bash
python3 build_slides.py          # 渲染全部 11 张(或 build_slides.py 1 2 渲指定张)
python3 -m venv .venv && .venv/bin/pip install edge-tts   # 配音依赖(微软神经 TTS,首次)
python3 build_video.py           # 用 Edge TTS 合成带配音 MP4
```
依赖:macOS、Google Chrome(无头渲染)、ffmpeg、中文字体 Hiragino Sans GB、`edge-tts`(经 `.venv`,联网)。
> 配音方案借鉴自同机 `VedioDubbing` 项目(edge-tts)。比 macOS `say` 自然很多。

## 改动指引
- 页脚/品牌:`build_slides.py` 顶部 `HANDLE`
- 配色/版式:`build_slides.py` 的 `CSS`
- 文案/旁白:各 `SLIDES[i]` 与 `build_video.py` 的 `NARR`
- 视频节奏:`build_video.py` 的 `RATE`(语速)、`PAD`(停顿)

> 半匿名原则:不出现真实品牌名、域名、玄学 niche;只展示系统架构、自动化能力与技术栈。
