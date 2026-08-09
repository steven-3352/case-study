# ad2-agent 工作流契约

> 产品 SSOT：`../docs/ad2-agent/带货视频原创翻拍与模板化生产_PRD_最终版.md`。

## 入口

所有命令在 `ad2-agent/` 下执行：

```bash
./ad2 <command> ...
```

`projects/_registry.json` 只登记 ad2 项目，不与 `ad-agent/projects/_registry.json` 共用。

## 当前执行骨架

| 执行步骤 | 当前职责 | PRD 范围 |
|---|---|---|
| `00_intake` | 参考视频、商品图、文本、权利声明预检 | N00-N01 |
| `01_analysis` | 需求结构化；当前尚不等于完整视频语义解析 | N02-N05 的基础层 |
| `02_storyboard` | 原创故事与逐镜生产描述 | N06-N09 的基础层 |
| `03_keyframes` | 商品保真展示帧与生成镜首帧 | N10 |
| `04_shots` | Seedance 或本地路径逐镜生成 | N11 |
| `05_delivery` | 合成与交付 | N13 的基础层 |

N12 单镜诊断、N14 全片验收、N15 用户拍板、N16 模板固化、N17 批量复用后续必须显式补节点，不能隐含在 `05_delivery` 中。

## 拍板与恢复

- `ok` 只批准当前 `awaiting_approval` 步骤。
- `reject` 写入反馈并只失效相关下游。
- `retry` 用于修复阻塞后的显式重试。
- `resume` 从第一个合法未完成节点继续。
- 任一失败必须落 `_meta/recommendations.yaml`，禁止静默死局。
- Seedance 任务使用 `.adfilm/jobs/` 幂等记录；未知费用先确认，预算触顶后暂停。

## 外部边界

- 去身份化骨架视频的 HTTPS/nginx 发布器尚未实现；本地工具只产骨架文件与托管需求标记。
- 当前测试不调用真实付费模型。
- 其他视频模型与 RunningHub 不在 MVP 范围。
