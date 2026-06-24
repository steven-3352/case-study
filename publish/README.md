# 待发布成品

> 引擎最终输出层（SYSTEM §2 Layer 3 下游）：讨论定稿 → pipeline 生产 → 文案 + 素材。
> 系统说明：[docs/SYSTEM.md](../docs/SYSTEM.md)

## 目录一览

```
publish/
├── README.md
├── 2026-W26/              ← 【主】周发布包（按天：文案+素材+讨论室）
├── P001/                  ← 单项目：Project-001 多形态（backlog）
├── P004/                  ← 单项目：K1 介绍片（ready_to_publish）
├── P005/                  ← 单项目：微信体演示
└── .staging/              ← 渲染中间落盘（W26D* 等，git 忽略；同步到周目录后可选删）
```

| 目录 | 用途 | 可否删 |
|------|------|--------|
| `2026-W26/` | 本周 7 天发布包 | **保留** |
| `P001/` `P004/` `P005/` | 队列中引用的单项目成品 | **保留** |
| `.staging/W26Dxx/` | `render.py` 输出，已同步到周目录 | 可删，下次 render 再生 |
| `W26Dxx/`（根目录） | 旧版重复目录 | **已清理，勿再出现** |
| `*/_tmp/` | 渲染段中间文件 | **已清理，render 时临时生成** |

## 周发布包（推荐）

```
publish/2026-W26/
├── week.yaml · web_research.yaml · topics_content.yaml
├── D01-美甲撞档/
│   ├── room/ · insights/ · scripts/
│   ├── douyin/   publish.md · video.mp4 · cover.png
│   └── xhs/
└── D02–D07 …
```

```bash
python3 pipeline/week_room.py
python3 pipeline/week_build.py
python3 pipeline/week_build.py --render    # 产出 → .staging/ → 同步到 Dxx/
```

## 单项目（P00x）

大项目或历史案例仍用 `publish/P00x/{douyin,xhs,channels}/`。  
标杆：`P004/`（见 `queue/topics.yaml` T008）。

## 清理约定

- 周项目视频以 **`2026-W26/Dxx-*/`** 为准，不保留根目录 `W26Dxx/` 副本
- 渲染完并同步后，可 `rm -rf publish/.staging/W26D*`
- 不提交 `*.mp4` `*.png`、`**/_tmp/`（见根 `.gitignore`）
