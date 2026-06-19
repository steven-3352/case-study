# CLAUDE.md — AI 小系统获客引擎 · 项目规则

> 本文件随仓库提交，克隆即可复现规则。Claude Code 启动时自动加载。

## 项目概览

用 AI 把小老板每天烦的事做成能跑的小系统，通过三平台（小红书/抖音/视频号）内容持续展示获客。

- 定位文档：`PROJECT.md`
- 总蓝图：`docs/BLUEPRINT.md`
- 决策锁定：`docs/DECISIONS.md`

## 环境配置

```bash
# 复制 .env 模板填入 key
cp .env.example .env

# Python 依赖
pip install openai pillow python-dotenv edge-tts

# 系统依赖
# macOS + Python 3 + ffmpeg + Google Chrome + 剪映
```

## 统一画布规格

- 全局 9:16 → 1080×1920（图文 + 视频统一）
- 常量定义：`pipeline/screen_dims.py`（CANVAS_W/H, VIDEO_W/H, IPHONE_W/H）

## 流水线入口

| 路线 | 脚本 | 用途 |
|------|------|------|
| P001 真实截图风 | `pipeline/render_p001.py --all` | 仿真 B-roll + 三平台视频/图文 |
| P001 仿真素材 | `pipeline/gen_evidence.py` | Chrome 渲 HTML 出 9:16 满铺帧 |
| P002 报纸风出图 | `pipeline/p002_carousel_gen.py` | GPT-image-2 整版报纸风轮播 |
| TTS 配音 | `pipeline/tts/gen_speech.py --script <path>` | Edge TTS 口播 |

## GPT-image-2 API（报纸风首选）

- 中转：tonbirds（`GPT_IMAGE_BASE_URL=https://us.tonbirds.com/v1`）
- 尺寸：1024×1536 原生 → 升采样 1080×1620
- 单张耗时 60-130s，需 4 次重试 + 5s 退避
- 中文标题渲染质量高，正文长段落约 5% 乱码（可接受）
- 不适合：精确文字排版、可编辑版面、品牌 logo

## 可用但未启用的能力

### GSAP Skills（全局注册，8 个）

gsap-core / gsap-timeline / gsap-scrolltrigger / gsap-plugins / gsap-performance / gsap-utils / gsap-react / gsap-frameworks

来源：https://github.com/greensock/gsap-skills.git

适用场景（未来）：
- 项目演示落地页 / 长滚动案例页
- 交互式作品集 / Before-After 对比
- 网页动效 → 录屏当 B-roll
- 报纸风不适合时 HTML+GSAP 拼版面再截图

---

## 核心工作流程：新选题多工种协作模式

每次出现新选题（queue/topics.yaml 新增、口头抛一个场景、或给某项目做内容落地），**必须**先按多工种协作跑一遍，不能直跳 prompt 写作或剪辑。

### 工种清单

| 工种 | 职责 | 输出 |
|------|------|------|
| **编导（总导）** | 选题是否符合主线、四形态拆分 | 选题立项单：钩子 + 形态分工 + 验收标准 |
| **记者** | 真实性、数据、证据链 | 调研笔记：小老板原话、痛点佐证、数据点 |
| **纪录片导演** | 故事弧线、改造前后对比 | 叙事大纲：起承转合 + 情绪锚点 |
| **导演（执行）** | 镜头语言、节奏、信息密度 | 分镜表：画面/口播/字幕/时长 |
| **摄像/视觉** | 画面可拍性、构图、可复用素材 | 画面清单：B-roll 列表、截图需求 |
| **编剧** | 钩子、逐字稿、字幕节奏 | v0/vA/vB 三版脚本 + 前 3s 大字钩子 |
| **视觉设计** | 版面、色彩、品牌一致性 | 视觉路线：P001 截图风 / P002 报纸风 / 新路线 |
| **剪辑** | 时长卡控、三平台规格 | 剪辑说明：抖音 45-60s / 小红书 ≤60s / 视频号 60-90s |
| **运营/增长** | 分发策略、私信转化承接 | 三平台文案 + 评论区埋点 + 私信路径 |

### 标准动作

1. **立项** — 编导给一句话选题，确认进 `queue/topics.yaml`
2. **平行调研** — 记者（挖证据）+ 纪录片导演（找故事）并行
3. **脚本三版** — 编剧产出 v0/vA/vB
4. **视觉路线** — 视觉设计决定 P001 / P002 / 新路线
5. **分镜 + 画面清单** — 导演 + 摄像确认素材就绪（参考 `assets/broll/catalog.yaml`）
6. **剪辑/出图** — 进入对应 pipeline 脚本
7. **发布包** — 运营出三平台文案，套 `templates/publish_三平台.md`
8. **验收** — 跑 `pipeline/CHECKLIST.md`，不过就回到对应工种返工

### 规则

- 允许某个工种声明"本选题不输出"，但必须显式说明原因
- 可由 Claude 串行扮演各工种，也可调 Agent 工具并行
- 每个工种产出独立、可审阅的段落，不合并成"四不像"
- Phase 0 全人工串行；Phase 2+ 半自动后 Agent 并行

### 反例（不要这么做）

- ❌ 选题一来直接跳进 `p002_carousel_gen.py` 写 prompt
- ❌ 只用编剧视角，跳过记者 → 没真实感
- ❌ 跳过视觉设计 → 所有选题都出报纸风
- ❌ 工种产出混成一份不可分辨的文档

---

## 内容硬约束（来自 DECISIONS.md）

- 全屏演示：录屏/数据/系统画面 100% 画面
- 无人物出镜：真人、数字人、画中画均不做
- 口播 + 字幕：Edge TTS 配音，字幕叠主画面
- 前 3s 冲突钩子 = 大字字幕 + 演示画面
- 项目结果先于方法论，业务问题先于技术栈

## 刻意不做（Phase 0–1）

- ❌ 三平台自动发布（API 风控）
- ❌ 数字人 / 真人出镜（已暂停）
- ❌ 自研声音克隆
- ❌ 爬虫抓平台数据
- ❌ CMS / 数据库
