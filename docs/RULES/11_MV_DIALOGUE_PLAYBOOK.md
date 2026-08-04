# 11 · 新片对话剧本（AI 客户端专用）

> **触发**：用户说「我想做一支MV / 短片」「新做一个片子」「想做卡点视频」「帮我做一段音乐动画」——识别到这类意图，AI 客户端（Codex / Claude / GPT）**必须按本剧本主导流程**，不要等用户自己问下一步做什么。
>
> **底层规范**：见 `10_MV_ENGINE.md`（相机 · 原子 · 缓存 · 求解器） · `.github/CONTRIBUTING.md`（双层边界）。
>
> **铁规**：AI 全程不修改 `pipeline/mv_engine/`、`docs/RULES/`、`templates/mv/`。有原子层需求就明说「需要新原子，建议提 PR 给 owner」，绝不自己动引擎。

---

## 剧本总纲

新用户做一支 MV 分成 **6 个阶段 + 1 个循环**：

```
A. Onboarding      环境/依赖/示范片跑通       (~10 分钟, 一次性)
B. Foundation      音频/时间轴/色板           (~15 分钟, 每片一次)
C. Structure       镜头边界 + 主体分配        (~20 分钟, 决定叙事)
D. Camera Solve    运镜/景别/转场            (~5 分钟, 求解器或手调)
E. Render          冷渲染出片                 (~5 分钟, 全自动)
F. Verify          gate 验收 + 肉眼看         (~2 分钟)

  ↓ (发现问题)
Iteration Loop     改一镜 → 8 秒重渲 → 再看   (无限循环直到满意)
```

**每阶段都有明确的入场条件和出场产物**。AI 不能跳阶段，也不能省略确认——每个阶段结束前必须让用户确认。

---

## 阶段 A · Onboarding

### 入场条件
- 用户在项目根目录（`case-study/`）
- 用户已装 Python 3.9+

### AI 主动做的事

1. **检查环境**：
   ```bash
   python3 --version
   test -d .venv || echo "缺 venv"
   test -f pipeline/voice_room/mingyue_render.py || echo "不在项目根"
   which ffmpeg || echo "缺 ffmpeg"
   ```
   缺什么就引导装什么（参考 `docs/RULES/07_ENVIRONMENT.md`）。

2. **跑示范片确认环境 OK**：
   ```bash
   cd pipeline
   python3 -m mv_engine.tools.render_cached \
       --out ../.cache/mv_engine/demo --cache ../.cache/mv_engine/framecache \
       --version a --limit 24 --jobs 4
   ```
   （只渲前 24 帧看能不能出图，约 30 秒。全渲要 3 分钟不合适放这。）

3. **问用户创意的一句话概述**：
   > 「用一句话告诉我这支片是什么。比如：『关于告别的下午 / 一个人拆一封老信 / 城市黄昏的通勤』——**不要**告诉我技术参数，就一句情绪。」

### 出场产物
- 环境验证通过
- 一句话创意概述（记在心里，后续每个决策都对着它检查）

---

## 阶段 B · Foundation

### 入场条件
- Onboarding 完成
- 用户手里有音频文件（wav/mp3）

### AI 主动问的三个问题（按顺序）

**B.1 音频**
> 「音频文件在哪？丢给我路径。」

拿到路径后：
```bash
# 用 ffprobe 或 pydub 提音频时长和采样率
ffprobe -v error -show_entries format=duration -of default=nokey=1:noprint_wrappers=1 <path>
```

**B.2 时间轴片段**
> 「整段音频多长？片子做全长还是只做其中一段？如果只做一段，起止时间告诉我（秒）。」

**必要**：确定 `SEG_T0` 和 `SEG_T1`。如果用户不确定，帮他找音乐的一个自然段落（有明显起承转合的 5-15 秒）。

**B.3 情绪色调**
> 「片子的情绪偏冷（蓝/灰/绿）还是偏暖（橙/红/黄）？两三种基调色，说词就行——比如『黄昏的橙 / 老照片的褐 / 深海蓝』。」

**不要问用户 hex 值**。用户说情绪词，AI 自己转成 hex（参考 `pipeline/voice_room/mingyue/palette.py` 里两套色板的写法：每个色都能回答「这是那个场景的哪个部位」）。

### AI 主动做的事

1. 在用户业务目录建骨架：
   ```bash
   mkdir -p pipeline/voice_room/<片名>
   cp templates/mv/tech_plan.template.md pipeline/voice_room/<片名>/tech_plan.md
   ```

2. 写 `palette.py`（AI 生成，用户确认）：
   ```python
   # pipeline/voice_room/<片名>/palette.py
   # 按用户情绪词转 hex，每个色写一句"这是场景里的什么"
   ```

3. 让用户看色板：
   > 「色板初稿在 `pipeline/voice_room/<片名>/palette.py`，五个色 + 每个的用途注释。看一眼，改错了告诉我。」

### 出场产物
- `pipeline/voice_room/<片名>/palette.py` 通过
- `SEG_T0`、`SEG_T1`、音频路径记录在 `tech_plan.md`

---

## 阶段 C · Structure（叙事骨架，最重要）

### 入场条件
- Foundation 完成
- 用户能说出这段片「讲一件什么事」

### AI 主动问的两个问题

**C.1 镜头节奏**

> 「这段音频里有几个明显的节点？比如鼓点进、人声起、副歌爆。数一下大概有多少个『需要切镜』的点。」

**关键**：镜头边界是**用户耳朵定的**，不是 AI 猜的。如果用户说「不知道」，AI 用节拍分析（librosa/ffmpeg loudness）给个候选让用户挑。

**C.2 每个镜头拍什么**

对每个候选镜头，AI 问：
> 「镜头 S03 从 X.Xs 到 X.Xs，画面里应该有什么？（主角人物？道具？空场？）」

**收集到的信息**：
- 每镜的 `t: [t0, t1]`
- 每镜的 `subject`（哪个 item 是主体，进 R9 冻结门）
- 每镜的 `layout` 大致（哪些 item）

### AI 主动做的事

写 `shots_a.yaml`（先不填 cam 参数，只填结构）：
```yaml
shots:
  - sid: S01
    t: [0.0, 2.5]
    layout:
      items:
        - fn: doll
          name: heroine
          world_h: 1800
    subject: [0]
    bg: [sky, SKY_ORANGE, 0.5, 2000.0]
    note: 开场 · 主角远景
    # cam 留白, 阶段 D 填
```

### 出场产物
- `shots_a.yaml` 结构完整（sid / t / layout / subject / bg / note）
- `cam` 字段留白，或只有 pin 的少数镜

---

## 阶段 D · Camera Solve

### 入场条件
- shots_a.yaml 结构 OK

### 两条路，AI 让用户选

**路 1 · 求解器（推荐首次用）**

```bash
cd pipeline
python3 -m mv_engine.tools.solve_shots \
    --in voice_room/<片名>/shots_a.yaml \
    --out voice_room/<片名>/shots_a.solved.yaml \
    --report voice_room/<片名>/solve_report.md \
    --verify-gate
```

AI 把 `solve_report.md` 里的表格给用户看：
> 「求解器给的方案在这。运镜多样性 X 种 / 转场 Y 种，gate 全过。有想固定的镜头吗？（比如『第 3 镜必须是特写』）」

如果用户 pin 了某镜：AI 在原 `shots_a.yaml` 里补 `cam:` 字段，重跑求解器。

**路 2 · 手调（有明确视觉预设的用户）**

AI 参照 `pipeline/voice_room/mingyue/shots_a.yaml` 里每镜的 `cam:` 参数写法（size0/size1/zoom/dx/dy/ease/e0/e1），一镜一镜和用户对着写。

### 出场产物
- `shots_a.yaml` 每镜有完整 `cam:` 字段
- gate_check_motion 通过

---

## 阶段 E · Render

### 入场条件
- shots_a.yaml 完整

### AI 主动做的事

```bash
cd pipeline
python3 -m mv_engine.tools.render_cached \
    --out ../.cache/mv_engine/<片名>_out \
    --cache ../.cache/mv_engine/framecache \
    --version a --jobs 4
```

**给用户报进度**：
- 冷渲染 ~3-5 分钟（AI 提示可以去泡杯咖啡）
- 完成后立即拼视频：
  ```bash
  ffmpeg -framerate 30 \
      -i .cache/mv_engine/<片名>_out/a/_frames/f%05d.png \
      -i <音频路径> \
      -c:v libx264 -pix_fmt yuv420p -crf 17 \
      -c:a aac -b:a 192k -shortest \
      <片名>_a.mp4
  ```

### 出场产物
- `<片名>_a.mp4`

---

## 阶段 F · Verify

### AI 主动做的事

```bash
python3 pipeline/gate_check_motion.py \
    .cache/mv_engine/<片名>_out/a/motion.json
```

**结果处理**：
- `[motion] OK` → 让用户看视频
- `[motion] FAIL` → 报告哪一段冻了，回阶段 D 改运镜

**看视频后 AI 主动问**：
> 「视频看完，说三件事：**最喜欢的一处** / **最想改的一处** / **总体节奏是快了慢了还是刚好**。」

---

## Iteration Loop（改-渲-看，8 秒一圈）

### 常见改动 → AI 对应动作

| 用户说 | AI 改哪 | 重渲代价 |
|--------|---------|---------|
| 「第 3 镜太快了」 | 调 `S03.cam.ease` 或延长 `t` | 8s（缓存命中其他镜） |
| 「颜色太冷」 | 改 `palette.py` | 全量重渲（key 变了）|
| 「S05 主角应该在左边」 | 改 `S05.layout.items[0].center` | 8s |
| 「加一层胶片颗粒」 | 改所有镜的 `fx.grain` | 全量重渲 |
| 「Gate 说 S07 冻了」 | 加大 S07 的 `cam.dx` 或换 ease | 8s |

**AI 的行为约束**：
- 每次改动**只改一处**，改完立即渲，让用户看效果
- **不要**一次改五处后统一渲——用户没法判断哪个改动带来了哪个效果
- 改完必跑 `gate_check_motion`，报告结果

---

## 边界铁规（AI 必须遵守）

### AI 可以自主做的

- ✅ 在 `pipeline/voice_room/<片名>/` 下创建、修改任何文件
- ✅ 读 `pipeline/mv_engine/` 下的任何代码（作为文档参考）
- ✅ 运行 `mv_engine` 的 CLI 工具
- ✅ 在 `.cache/mv_engine/` 下写渲染产物

### AI 不能自主做的（必须停下来告诉用户）

- ❌ **修改 `pipeline/mv_engine/` 下任何文件**
  - 就算发现引擎有 bug，也是「告诉用户，建议 PR」，不是「我给你改了」
  - 语句模板：
    > 「我在 `mv_engine/atoms/paper.py` 里发现一个 bug（描述）。这是引擎层文件，我不能直接改。你要不要我起草一个 PR 让 owner 审核？」
- ❌ **修改 `docs/RULES/` 下任何规则**
- ❌ **修改 `pipeline/mv_engine/atoms/lock.json`**（原子锁）
- ✅ **`git push origin main`**（2026-08-04 起:main 分支保护已撤、PR 通道已关,直连 main 是当前唯一合并路径;仅在 owner 明确要求时推送)

### 需要新原子时的行为

用户可能会说「我想要一个类似电影胶片划痕的效果」——如果引擎里没有这个原子，AI 必须：

1. 先确认现有原子是否能组合出效果（`scan_bar` + `banding` + `grain` 可能就够）
2. 如果确实缺，明说：
   > 「实现这个效果需要新原子 `film_scratch`。这是引擎层修改，我不能直接加。**两个选项**：
   > (a) 我在你的片子里用现有原子做一个 90% 相似的版本
   > (b) 我起草一个 PR 描述这个原子，你提交给 owner 审核」

---

## 完整对话样例

```
用户: 我想做一支 15 秒的告别 MV，音乐已经剪好了

AI: 好。先跑三个检查：Python 版本、venv、ffmpeg。
    [执行环境检查]
    环境 OK。音频文件在哪？丢路径给我。

用户: /Users/me/music/goodbye.wav

AI: [执行 ffprobe] 音频 42.3 秒。你要做的 15 秒是从哪到哪？
    (提示：我看到 8.4s 有一个明显的音量爆点，可以做起点)

用户: 就从 8.4 开始吧

AI: 好，SEG_T0=8.4 SEG_T1=23.4。用一句话告诉我这片是什么。

用户: 一个女孩收拾行李，翻到一张老照片

AI: 情绪偏冷还是偏暖？两三种基调色说词就行。

用户: 老照片那种褐色，加点窗外的青

AI: [生成 palette.py，用 SEPIA_PAPER/SEPIA_INK/WINDOW_CYAN/DUST_GRAY/DEEP_SHADOW]
    色板初稿在 pipeline/voice_room/goodbye/palette.py，五个色。看一下。

用户: 深阴影再深一点

AI: [改 palette.py 里 DEEP_SHADOW 的 hex]
    改好了。现在音频里我数了 4 个明显节点：8.4 起唱、11.2 副歌进、15.7 停顿、19.8 尾音收。
    可以切成 4 镜，也可以在停顿前后再加 1-2 镜到 5-6 镜。

用户: 就 4 镜吧

AI: 每镜画面是什么？
    S01 (8.4-11.2): 起唱 —— 建议 中景，主角背影翻箱子
    S02 (11.2-15.7): 副歌 —— 建议 特写，手拿起照片
    S03 (15.7-19.8): 停顿 —— 建议 空镜，照片特写 + 灰尘光
    S04 (19.8-23.4): 尾音 —— 建议 全景，主角站在窗前
    
    对不对？

用户: 对，但 S03 我想要主角眼睛的特写

AI: [调整 S03 layout] 好。写 shots_a.yaml。[产出 yaml]
    要不要让求解器帮你选运镜？

用户: 好

AI: [跑 solve_shots + verify_gate]
    求解器给了：S01 慢推、S02 track_r、S03 hold、S04 pull。
    Gate 全过。渲一次看看？

用户: 渲

AI: [跑 render_cached，等 4 分钟]
    [拼 mp4]
    在 ~/goodbye_a.mp4 了。看一下，告诉我三件事。

用户: S03 太慢了，其他都好

AI: [把 S03 的 ease 从 hold 改成 ease_out_sine，dx 加 0.1]
    [重渲 —— 只有 S03 miss，其他缓存命中，8 秒完]
    改好了。这版 S03 有轻微横移。

用户: 完美，就这样了

AI: 好。原始产物在 .cache/mv_engine/goodbye_out/，视频在 ~/goodbye_a.mp4。
    要不要我把 shots_a.yaml 和 palette.py 整理进 pipeline/voice_room/goodbye/
    做归档？以后再改这片直接用。
```

---

## 快速参考卡（AI 对话时随时查）

```
6 阶段:   A → B → C → D → E → F → (Iterate)
不跳阶段, 每阶段完必让用户确认

引擎位置:  pipeline/mv_engine/         ← 只读
用户位置:  pipeline/voice_room/<片名>/  ← 读写

核心命令:
  render_cached  → 冷渲 3-5 分钟 · 热渲 8 秒
  solve_shots    → 秒级出 solve_report.md
  gate_check_motion → 秒级验 R9

边界铁规:
  改引擎 = 提 PR, 不 push
  改内容 = 直接改, 用户业务目录
```
