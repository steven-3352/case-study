# adfilm 开发卡 · 子 agent 须知（先读这一页）

> 你被派来只完成**一张开发卡**里的一个功能。**不要**去读整份 PRD，也不要通读整个项目。
> 读你那张卡 + 本页的「公共约定」就够了。卡里已经告诉你**用哪个现成脚本**，你的活是**改/接/加薄薄一层**，不是重写。

---

## 0. 铁律（每张卡都适用）

1. **复用优先，禁止另造轮子**：adfilm 的骨架 = 现成的 `ad-agent/conductor/`。你几乎不用新写图像/视频/状态机底座，只在指定位置加功能。
2. **只读你的卡**：卡里列了「直接用这些脚本」。照着调，别去理解无关模块。
3. **底层功能走公共库**：媒体/摘要/provider 一律从 `src/mvstudio/` 导入，不在 agent 里复制实现。
4. **失败不抛异常给上层猜**：工具统一返回 `ToolResult(ok, outputs, error={code,message,hint}, meta)`。
5. **不静默死局**：走不下去就返回结构化建议包（见 `开发卡_06`），不要只报一个 error 字符串。
6. **禁止擅自改变参考内容**：用户要求复刻、延续或直接使用原视频时，若模型、provider 或当前路线不能实现，必须暂停并向用户说明具体限制，让用户确认替代路线。未经确认不得自动改人物、动作、服装、场景、时长、叙事，不得自动切骨架、换人或改成重新生成。

---

## 1. 环境（照抄）

```bash
# 解释器（系统没有裸 python，必须用这个）
PY=/Users/wmzuo/Documents/project/case-study/.venv/bin/python

# 导入路径：src 必须在 PYTHONPATH；跑 conductor 时把 ad-agent 也加上
PYTHONPATH=src $PY -c "import mvstudio.media as m; print(m.sha256_bytes(b'x'))"
PYTHONPATH=src:ad-agent $PY -m conductor.cli status <片名>
```

- KEY 统一来自**项目根 `.env`**（不是 ad-agent/.env）：`SEEDANCE_BASE_URL/SEEDANCE_API_KEY/SEEDANCE_MODEL`、`GPT_IMAGE_BASE_URL/GPT_IMAGE_API_KEY/GPT_IMAGE_MODEL`。
- 省钱开关：`export AD_MAX_SHOTS=2` → 从 02 起镜头数封顶 2，贯穿 03/04/05；正式出片前 `unset`。

---

## 2. 现成骨架模块地图（`ad-agent/conductor/`）

adfilm 的六步流水线 = 下面这套，已跑通。你的功能大概率是**改其中一两个文件**：

| 文件 | 干什么 | 你什么时候动它 |
|---|---|---|
| `cli.py` | 命令入口：`init/status/next/run/shot/ok/reject` | 加 CLI 命令时（开发卡_05） |
| `conductor.py` | 编排：读 state → 备输入 → 调工具 → 写产物 → 更新 state | 一般**不动**；只加步骤时看 |
| `pipeline.py` | 六步声明式契约（step_id → tool 函数、产物、是否拍板） | 加/改步骤时改这里，别动 conductor |
| `state.py` | `state.json` 读写、步骤状态机、hash、级联失效 | 加节点状态/失效规则时（开发卡_05） |
| `layout.py` | 建项目目录骨架、`_input/` 交接、`_meta/` 落盘 | 一般不动 |
| `contracts.py` | `ToolResult` / `StepSpec` / `Unit` / 状态常量 | 只读，理解返回结构 |
| `tools.py` | 六步的工具实现（见下表）+ `_image_provider()` 等 | 大多数功能卡改这里 |
| `media.py` | 媒体助手（合成/画布/pose 薄封装）；底层从 `mvstudio.media` 导入 | 复用，别复制实现 |
| `render.py` | 跑前/跑后统一文案 | 一般不动 |

### 六步 → 工具函数（`pipeline.py` 已连好线）

| step_id | 工具函数（在 `tools.py`） | 对应 PRD 节点 |
|---|---|---|
| `00_intake` | `intake_validate` | N00–N01 物料登记/预检 |
| `01_analysis` | `llm_analyze` | N02–N05 参考/商品/模式/概念 |
| `02_storyboard` | `llm_storyboard` | N06–N09 风格/脚本/分镜/路线 |
| `03_keyframes` | `gen_keyframe` | N10 关键帧 |
| `04_shots` | `gen_video` | N11 逐镜视频 |
| `05_delivery` | `compose` | N13 合成 |

> N12(单镜诊断)、N14–N17(验收/模板/批量) 在当前骨架里是薄层或待补——各自的卡会说明。

---

## 3. 公共底层库（`src/mvstudio/`，禁止复制实现）

- `mvstudio.media`：`sha256_bytes` / `sha256_file` / `err` / `ffmpeg_bin` / `ffprobe_bin` / `provider_config` / `max_shots(env_var)` / `generate_pose_reference(...)`。
- `mvstudio.providers.seedance`：`SeedancePort` / `SeedanceTask` / `SeedanceFrame` / `SeedanceResult`（i2v，已支持多模态参考）。
- `mvstudio.providers.image_openai`：`OpenAICompatibleImageProvider`（文生图，`gpt-image-2`）。

---

## 4. 卡片清单

| 卡 | 功能 | 主要改哪 |
|---|---|---|
| `开发卡_01_物料登记与预检.md` | N00–N01：收物料、哈希、三级问题分级 | `tools.intake_validate` |
| `开发卡_02_关键帧生成.md` | N10：display 保真合成 / generated AI 首帧 | `tools.gen_keyframe` + `media` |
| `开发卡_03_逐镜生成.md` | N11：Seedance i2v（含多模态参考）+ 本地免费镜 | `tools.gen_video` + `seedance` |
| `开发卡_04_参考视频去身份化.md` | 参考视频 → 无脸骨架，喂 Seedance | `media.pose_reference_from_video` |
| `开发卡_05_状态机与恢复.md` | 节点/状态/失效/恢复、CLI 命令 | `state.py`/`cli.py`/`conductor.py` |
| `开发卡_06_建议包永不死局.md` | 阻塞 → 结构化建议包 | 各工具的 `error` 返回 |
| `开发卡_07_成本记录与触顶.md` | jobs 成本记录、hard_limit 触顶暂停 | `tools.gen_video`/state |
| `开发卡_08_测试夹具.md` | pytest 契约测试、帧指纹回归 | `tests/` |

---

## 5. 每张卡的统一格式

`目标 → 只读本卡 → 直接用这些脚本 → 输入/输出 → 铁律 → 完成判据(Done) → 自测命令`。
Done 没全绿就不算完成，别把「跑通了一次」当验收。
