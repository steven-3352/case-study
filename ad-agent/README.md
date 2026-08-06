# 广告/视频创作助手（ad-agent）

用对话，一步步把**产品图 + 一段文本**做成完整的广告/视频。产品图 **100% 原样展示**——AI 只做背景、氛围、运镜，产品一个像素都不改。

---

## 核心理念：产品图两个身份

- **展示帧**：产品原图像素锁死，AI 只生成周围背景铺满画幅。100% 保真，负责精确展示。
- **生成镜**：产品图喂 i2v 跑动感/氛围镜，允许画面自由。

成片里两者交织：展示帧兜底保真，生成镜提供动感。分镜（第 2 步）决定每镜用哪种。

---

## 快速开始

### 1. 装依赖 + 配 Key

```bash
pip install -r requirements.txt
cp .env.example .env    # 填 LLM / 图像 / Seedance 的 Key
```

### 2. 开始对话

告诉助手"帮我做个广告"，给它**物料目录**（图片 + 文本）和**画幅**，它会引导你走完六步。

---

## 六步流程

| 步骤 | 做什么 | 你需要做什么 |
|------|--------|-------------|
| 第 0 步 | 收图片 + 文本 + 画幅，校验 | 提供物料目录 |
| 第 1 步 | LLM 分析 → 需求理解书 | **确认方向对不对** |
| 第 2 步 | 视频故事 + 逐镜分镜（标展示/生成） | 确认分镜 |
| 第 3 步 | 首帧图（展示帧 = 原图贴背景） | 逐张确认 |
| 第 4 步 | 每镜视频（生成镜 i2v · 展示镜本地） | 逐段确认 |
| 第 5 步 | 拼接 + 卖点/CTA 文字 | 确认成片 |

---

## 手动运行（不用对话时）

```bash
# 初始化（项目根 = 物料目录，必填）
python -m conductor.cli init 我的广告 /path/to/物料目录
python -m conductor.cli run 我的广告          # 跑到下一个拍板点
python -m conductor.cli ok 我的广告 01_analysis   # 批准
python -m conductor.cli reject 我的广告 02_storyboard "第2镜换成产品特写"  # 打回
python -m conductor.cli shot 我的广告 03_keyframes 1   # 只出第1镜看风格（省钱）
```

---

## 目录结构

```
ad-agent/
  AGENTS.md          ← 对话指南（人格/话术）
  WORKFLOW.md        ← 执行契约（每步跑什么）
  .env               ← API Key（自己填，不提交）
  conductor/         ← 控制器（引擎复用 mv-agent，纯编排）
  prompts/           ← 可编辑的中文提示词模板
  projects/          ← _registry.json（片名→物料目录）
  <物料目录>/         ← 你的产物落这里（不进工具仓库）
    00_intake/ 01_analysis/ 02_storyboard/ 03_keyframes/ 04_shots/ 05_delivery/
```

---

## 画幅支持

`9:16`（竖 · 抖音/Reels）· `16:9`（横 · YouTube/官网）· `1:1`（方 · 朋友圈/feed）。
注：`1:1` 的生成镜（i2v）受 Seedance 限制按 9:16 出片，再由合成步填充到方画布；展示帧直接按 1:1 画布合成。

## 当前版本

- ✅ 六步流水线（复用 mv-agent 引擎骨架）
- ✅ 保真：展示帧 = 产品原图 PIL paste 到 AI 背景
- ✅ 展示镜本地路径（static/ken_burns）免费，不调付费服务
- ⏳ 音频/口播：当前版本纯画面 + 文字，暂不做
