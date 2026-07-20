# P011 · Seedance 2.0 i2v/t2v

**状态:** 生产可用(2026-07-20 拉齐到 grok-imagine 集成完备度)。`gen_video.py` 640 行 · py_compile 通过 · CLI 双模式(单段 / yaml 批量)· 重试 + 并发 + 恢复 + 后置 QA 就绪。**API key 补上即通。**

## 能力清单(gen_video.py)

- **单段快调** — `--prompt "..." --first-frame path.png --duration 5 --out out.mp4`
- **yaml storyboard 批量** — `--config storyboard.yaml --out-dir tmp/xxx/videos`(不用每条选题拷 py 脚本)
- **重试** — 429/503/timeout 指数退避 3 次;auth/url/payload/content-policy 立即失败不重试
- **并发** — 默认 2 worker(沿用 `feedback_gpt-image-model-fallback` 教训 · `--workers` 或 env `SEEDANCE_WORKERS` 覆盖)
- **恢复** — `--resume` 读 `.status.json` 跳过已完成 slug
- **sync/async 双兼容** — 复用 grok 的响应结构探测(video.url / task_id 双路)
- **后置 QA** — 下载完自动调 `gate_check_media.py`(若存在),ffprobe 体检不阻断只报告
- **错误分类** — auth / url / payload / rate-limit / timeout / content-policy / server / network / poll-timeout / download

## yaml 格式

```yaml
workers: 2                        # 可选
aspect_ratio: 9:16
resolution: 720p
scenes:
  - slug: S01_kitchen
    prompt: |
      <走 .agents/skills/i2v-video-prompt/ 骨架的 motion prompt>
    duration: 5
    first_frame: tmp/short/frames/S01.png    # 相对 project root · 可省略走 t2v
    ref_frames:                              # 可选
      - tmp/short/frames/S01_ref.png
    negatives: |
      NO face morphing, NO body stretching, NO breath puff, NO neon purple/cyan.
```

## 定位

- **候选身份:** SYSTEM §4.2 `外部制作插件` 家族的 i2v 候选,与 `grok-imagine-video`(现役)并列
- **不是默认路线** —— 每一镜按 §4.2 五维打分决定;违反者见 memory `feedback_no-default-tech-stack` 与 `SCRIPT_REJECT_LOG`
- **prompt 工程走** `.agents/skills/i2v-video-prompt/`(**通用 skill,不专属 P011**,任何视频模型 prompt 都走它)+ 按形态挂载 `video-form-*` 子 skill(15 个 · 电影/3D/漫画/打斗/日漫/SaaS/电商/360/MV/病毒钩子/品牌/时尚/美食/房产)

## 何时选它,何时不选(与 grok-imagine 分工)

| 情况 | 倾向 | 依据 |
|---|---|---|
| 需要**明确相机运动**(bullet time / 360 orbit / crash zoom / dolly zoom) | Seedance | Higgsfield 蒸馏 prompt 本就是给它 |
| 需要**照片级真实**(反 AI 味硬门) | 优先 Seedance,备选真实 B-roll | grok 目前塑料感明显 |
| **人体细致动作**(手势/嘴形/走姿) | 都不够稳,考虑接 Kling | Kling 未接入,memory 有登记 |
| **续做已跑通的 grok 选题** | grok-imagine | §4.2 tie-breaker "少赶工 = 少毁片" |
| **氛围/空镜/静物** | 五维打分,不预设 | 差异不大 |
| 需要 **>10s 单镜** | 无 —— 都 ≤ 10-15s,必须拆多段 | — |
| **投后差评"AI 味重"** | 换 Seedance 试;仍差 → 真实 B-roll | 别硬撑同管线(§4.2 tie-breaker) |

## API 集成(与 grok 同风格)

- **端点:** `POST {SEEDANCE_BASE_URL}/v1/videos/generations`(与 `pipeline/gen_video_frames.py` 一致)
- **中转:** 云雾 `https://yy.tonbirds.com` · **具体前缀待确认** —— 若 4xx 先核对 URL 拼写,不要直接降级到 grok(memory `feedback_read-env-example-first`)
- **模型:** `doubao-seedance-2-0`(火山方舟标准名 · 中转可能重命名)
- **凭证:** `.env` 里 `SEEDANCE_API_KEY` / `SEEDANCE_BASE_URL` / `SEEDANCE_MODEL`(见 `.env.example`)
- **响应:** 参考 grok,可能同步(直返 video URL)或异步(返 task_id 需轮询)—— `gen_video.py` 复用 grok 的 `extract_video_url` / `poll_task` 两路兼容策略
- **成本参考:** 1 元/秒(火山方舟官价);15s 视频 ≈ 15 元 —— 比 Higgsfield $39-99/月订阅便宜

## 完善路线(按需触发)

第一条真选中 P011 的选题产出时,按顺序完善:

1. **首帧图路径** —— 复用 GPT-image-2 出图(`pipeline/gen_scene_frames.py` 类) → data URL 传 `image.url`
2. **motion prompt** —— 走 `.agents/skills/i2v-video-prompt/` 骨架,禁蓝紫 + 禁 AI 味深色 + NEGATIVES 段
3. **参考图** —— 需要人物一致性时传 `reference_images: [{url: ...}, ...]`(与 grok 同)
4. **失败重试** —— 参考 memory `feedback_gpt-image-model-fallback`:503 通常是并发过高,降 `SEEDANCE_WORKERS=2` 才是真解法,不换模型名
5. **逐帧 QA** —— i2v 必做,幻觉/伪影/尺寸变化一票否决(memory `feedback_camera-motion-vs-i2v-ceiling`)
6. **config-driven** —— 参考 `p004_video/lib/` 拆 `config.py` / `render.py` / `submit.py` / `poll.py`,不写巨型 main
7. **成片进 gate_check** —— `pipeline/gate_check_palette.py`(禁蓝紫)+ `pipeline/gate_check_media.py`(ffprobe 体检)必过再进 pre_publish

## 参考实现

- `pipeline/gen_video_frames.py` —— grok-imagine 集成模式的 golden reference,i2v prompt 4 段范式
- `pipeline/gen_d06_wuxia_motion.py` —— i2v + 4 张背景 motion 的实战
- `pipeline/client_projects/d07_moon/gen_bg_motion.py` —— 客户项目 i2v 场景

## 铁律绑定

- **禁默认心智** —— 出现"就走 Seedance 吧"念头立即回 SYSTEM §4.2 打分(memory `feedback_no-default-tech-stack`)
- **反 AI 味优先** —— prompt 里禁 "AI/generated/rendered/artificial",走 "shot on Kodak Portra 400 film"/"documentary"(memory `feedback_anti-ai-visual`)
- **禁蓝紫铁律** —— 生成后必过 `gate_check_palette.py`,>5% 蓝紫直接返工(memory `feedback_no-neon-palette`)
- **禁 AI 味深色画布** —— prompt 不默认深色场景,除非本条形态实拍就是暗光(memory `feedback_no-ai-visual-dark-canvas`)
