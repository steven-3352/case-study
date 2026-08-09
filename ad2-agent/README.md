# 参考视频商品翻拍助手（ad2-agent）

`ad2-agent` 是独立于 `ad-agent` 的第二个产品入口。

- `ad-agent`：商品图片 + 文本，从零制作普通广告视频。
- `ad2-agent`：参考视频 + 商品图片 + 商品特点 + 新视频要求，完成内容理解、商品替换或广告植入、原创翻拍与后续模板化。

两者共享 `src/mvstudio/` 的模型和媒体能力，但项目注册表、状态、提示词、测试和用户入口相互隔离。

## 物料目录

```text
<项目目录>/
├── reference/              # 至少一段参考视频
├── product/                # 商品正面/侧面/背面图片
├── brief/                  # 商品特点与新视频要求（.md/.txt）
└── 00_intake/request.yaml  # init 后生成；填写权利声明等结构化字段
```

参考视频仅用于分析内容、故事、节奏和镜头关系。新成片默认重新生成，不把原片直接当成最终画面底片。

## CLI 入口

所有模型凭证只从仓库根目录 `.env` 读取。

```bash
cd /Users/wmzuo/Documents/project/case-study/ad2-agent

./ad2 init 纸巾翻拍01 /path/to/project
./ad2 run 纸巾翻拍01
./ad2 status 纸巾翻拍01
```

常用控制命令：

```bash
./ad2 ok 纸巾翻拍01 00_intake
./ad2 reject 纸巾翻拍01 02_storyboard "第3镜改成桌面展示"
./ad2 shot 纸巾翻拍01 03_keyframes SH003
./ad2 shot 纸巾翻拍01 04_shots SH003
./ad2 retry 纸巾翻拍01 04_shots
./ad2 resume 纸巾翻拍01
```

成本控制：

```bash
./ad2 budget 纸巾翻拍01 100 CNY
./ad2 cost 纸巾翻拍01 --json
./ad2 confirm-cost 纸巾翻拍01 job-xxxxxxxx batch
```

## Codex 入口

在仓库根目录进入 Codex 后说：

```text
请使用 ad2-agent 制作参考视频原创翻拍。
项目名称：纸巾翻拍01
物料目录：/path/to/project
先做物料预检；每个拍板点停下来；阻塞时给建议，不要使用 ad-agent。
```

Codex 应读取本目录的 `AGENTS.md` 和 `WORKFLOW.md`，并在 `ad2-agent/` 下调用 CLI。

## 当前实现边界

当前入口已具备物料预检、参考视频登记、姿态去身份化、关键帧/逐镜生成、状态恢复、建议包与成本保护。参考视频的深度语义解析、替换对象时间码确认、原创性评估及模板固化仍需继续按 PRD 的 N00-N17 拆成独立节点；不能把现有六个执行步骤描述成完整产品已经交付。

完整产品契约见：`../docs/ad2-agent/带货视频原创翻拍与模板化生产_PRD_最终版.md`。
