# 贡献指南 · Contributing Guide

> **本项目采用"引擎归主库、内容归用户"的双层协作模型。**
> 读懂下面的边界，你就知道该怎么用这个项目了。

---

## 两个层的边界

```
case-study/
├── pipeline/mv_engine/        ← 引擎层（owner only）
│   ├── atoms/                 ← 原子库：与内容无关的动效原子
│   ├── camera.py              ← 相机模型
│   ├── solver/                ← 分镜求解器
│   ├── cache.py               ← 帧缓存
│   └── track.py               ← bbox 预测器
│
├── docs/RULES/                ← 项目规则 SSOT（owner only）
├── templates/mv/              ← 新片官方模板（owner only）
│
└── pipeline/voice_room/       ← 内容层（用户自由创建）
    ├── mingyue/               ← 《明月天涯》（owner 维护的示范片）
    └── <你的片名>/            ← ← ← 你的工作目录（不受限制）
```

**引擎层是只读库**：你调用它，不改它。  
**内容层是你的画布**：你自由创建，不需要任何审批。

---

## 使用流程（一般用户）

```bash
# 1. fork 或 clone 本仓库
git clone git@github.com:steven-3352/case-study.git
cd case-study

# 2. 安装依赖（见 docs/RULES/07_ENVIRONMENT.md）
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 3. 在你自己的目录工作
mkdir -p pipeline/voice_room/<你的片名>
# 参考 pipeline/voice_room/mingyue/ 的结构
# 参考 templates/mv/ 的模板

# 4. 使用引擎 —— import，不修改
from mv_engine.atoms import scan_bar, paper_fold
from mv_engine.solver import solve
from mv_engine.cache import frame_key
```

你的工作完全隔离在 `pipeline/voice_room/<你的片名>/` 里，不会污染主流程。

---

## 如果你发现了 bug 或想贡献新原子

### 步骤：

1. **Fork** 本仓库，在你的 fork 上建一个特性分支：
   ```bash
   git checkout -b feat/new-atom-bloom-v2
   ```

2. **按原子准入契约开发**（见 `docs/RULES/10_MV_ENGINE.md §4`）：
   - 不带默认颜色
   - 纯函数
   - 声明 `touches_alpha: bool`
   - 补 `lock.py` 的 case 并 `--write` 更新 lock.json

3. **验证**：
   ```bash
   python3 -m mv_engine.atoms.lock --check pipeline/mv_engine/atoms/lock.json
   ```

4. **提 PR**，目标分支 `main`，描述：
   - 原子做什么
   - 为什么它满足准入契约（没有内容依赖）
   - lock.json 已更新

5. **等待 owner（@steven-3352）审核合并**。

> PR 里如果没有更新 `lock.json`，会被自动要求补充。

---

## 哪些改动不需要 PR，自己 fork 做就好

| 改动 | 是否需要 PR |
|------|------------|
| 在 `pipeline/voice_room/<你的片名>/` 做新片 | ❌ 不需要 |
| 调整 `shots_a.yaml` 里的镜头参数 | ❌ 不需要 |
| 给你的片加新色板 `palette.py` | ❌ 不需要 |
| 修改 `pipeline/mv_engine/atoms/` 里的原子 | ✅ 必须 PR |
| 修改 `pipeline/mv_engine/camera.py` 等引擎文件 | ✅ 必须 PR |
| 修改 `docs/RULES/` 里的规则 | ✅ 必须 PR |

---

## 使用 AI 编码工具的约定

| 工具 | 加载入口 | 备注 |
|------|---------|------|
| Claude Code | `CLAUDE.md`（项目根） | 自动读取 |
| Codex | `AGENTS.md`（项目根） | 自动读取 |
| ChatGPT | `GPT.md`（项目根）| 手动复制进 system prompt |
| 其他模型 | 参考 `docs/RULES/09_MIGRATION_SOP.md` | 自建加载壳 |

**AI 工具的边界约束**：AI 在帮你做内容层工作时，不应自主修改引擎层文件。如果 AI 建议修改 `mv_engine/` 或 `docs/RULES/` 里的文件，应当提 PR 而不是直接 commit 到 main。
