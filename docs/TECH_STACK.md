# 技术栈

> 原则：Phase 0–1 能手工就不写代码；Phase 2+ 再脚本化。不追求完美架构。

## 总览

| 层级 | Phase 0–1（现在） | Phase 2+（有 win 形态后） |
|------|-------------------|---------------------------|
| 配置 | YAML + Markdown | 同左 |
| 脚本生成 | 人工 + ChatGPT 辅助 | `pipeline/gen_script.py` |
| 数字人 | 外部 SaaS（人工操作） | API 对接（视选型） |
| 剪辑 | 剪映（人工） | 剪映模板 + ffmpeg 批量 |
| 图文 | Figma/备忘录截图/现有 build_shots | 模板脚本化 |
| 指标 | Google Sheet / CSV 手工 | 手工导入脚本 |
| 报告 | 人工按 rules.yaml 复盘 | `pipeline/weekly_report.py` |
| 发布 | 人工发布 | 人工（平台 API 限制多，不优先） |

## 模块技术选型

### 1. IP 与人设
- **存储**: `persona/persona.yaml`
- **工具**: 任意 YAML 编辑器
- **人工**: 填 name/handle，审禁用词

### 2. 数字人 + 声音
- **形象**: 数字人 SaaS（D3 试两家后定，见 `assets/avatar/README.md`）
- **口播（默认）**: Edge TTS · `pipeline/tts/gen_speech.py`（免费、稳定）
- **备选**: 数字人 SaaS 原生音 / 剪映配音
- **已放弃**: 自研声音克隆 → `legacy/voice-clone/`

```bash
python3 pipeline/tts/gen_speech.py \
  --script pipeline/dry-run-001/script.md \
  -o pipeline/dry-run-001/speech.mp3
```

### 3. B-roll 素材
- **录屏**: 手机 / QuickTime / OBS
- **截图打码**: 系统截图 + 任意打码工具
- **登记**: `assets/broll/catalog.yaml`
- **复用**: 现有 `build_shots.py` 渲染真实页面帧（legacy）

### 4. 视频生产
- **剪辑**: 剪映专业版（字幕、比例、三平台导出）
- **规格**:
  - 抖音/小红书: 1080×1920, H.264
  - 抖音: 45–60s
  - 小红书视频: ≤60s
  - 视频号: 60–90s
- **Phase 2 可选**: `ffmpeg` 批量裁切（已有 `build_video.py` 经验）

### 5. 图文生产
- **禁止默认**: `build_slides.py` 黑金 11 张架构体
- **推荐**: 备忘录风 + 真实截图 + 数字人封面
- **可选工具**: `build_shots.py`、Canva、Figma

### 6. 选题与指标
- **选题**: `queue/topics.yaml`（Git 跟踪）
- **指标**: `ops/metrics.csv`（从 template 复制）
- **规则**: `ops/rules.yaml` + `ops/data-policy.yaml`
- **Phase 2**: Python 读 CSV 出周报（~100 行脚本即可）

### 7. 遗留代码（legacy/）
- `build_slides.py` — 架构图素材，降级
- `build_video.py` — TTS 草稿/内部预览
- `build_shots.py` — 真实截图帧，**保留使用**

## 依赖（现有环境）

- macOS
- Python 3（legacy 脚本）
- Google Chrome（build_shots）
- ffmpeg
- 剪映
- 数字人 SaaS（待定）

## 刻意不做的（Phase 0–1）

- ❌ 自动发布到三平台（API 不稳定、风控）
- ❌ 复杂 CMS / 数据库
- ❌ 全自动数字人 API（先人工跑通再对接）
- ❌ 爬虫抓平台数据（手工记录更可靠）

## Phase 2 最小脚本清单（届时再写）

```
pipeline/tts/gen_speech.py     # Edge TTS 口播（默认）
pipeline/gen_script.py        # 读 persona + topic → 脚本草稿
pipeline/weekly_report.py     # 读 metrics + rules → 周报 markdown
pipeline/export_specs.py      # 输出三平台规格 checklist
```
