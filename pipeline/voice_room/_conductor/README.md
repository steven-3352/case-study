# _conductor · 对话式 MV 流水线 · M1 空转骨架

设计文档:`docs/design/CONVERSATIONAL_PIPELINE_DESIGN.md`

## 这是什么

「纯控制器 + 纯工具 + 文件夹交接」的最小可跑骨架。
**stub 工具只写占位产物,不接真模型、不花钱** —— 先看流程,后接实现(M2+)。

## 三层

- `conductor.py` 控制器:读 state 选下一步 → 备齐输入 → 调工具 → 写产物 → 更新 state。不含业务判断。
- `tools.py` 工具:签名统一 `run(inputs, out_dir, params, prompt_file) -> ToolResult`。M1 全是 stub。
- 文件夹交接:每步一个文件夹,`_input/`(上游产物拷贝)+ `_meta/`(提示词副本/日志/state 片段)+ 产物。

其余:`contracts.py` 契约、`state.py` state.json、`layout.py` 文件夹脚手架、`pipeline.py` 六步声明式定义、`cli.py` 驱动。

## 跑一遍看流程

```bash
cd pipeline/voice_room
PY=../../.venv/bin/python   # 或你的 python

$PY -m _conductor.cli init   我的片子      # 建骨架
$PY -m _conductor.cli run    我的片子      # 一路跑到第一个拍板门停下
$PY -m _conductor.cli ok     我的片子 00_intake     # 拍板:过
$PY -m _conductor.cli reject 我的片子 02_storyboard "副歌情绪不对"  # 打回(级联失效下游)
$PY -m _conductor.cli status 我的片子      # 看全局进度
```

## 已验证

- 六步顺序执行 + 每步拍板门(`awaiting_approval` 停下等确认)
- 文件夹交接:上游产物拷进下游 `_input/`,提示词副本留档 `_meta/prompt_used/`
- 打回:写 `feedback.md` + revision+1 + **级联失效下游**(下游标回 pending)
- 幂等跳过:产物齐 + status=done 直接跳过

## 下一步(M2+)

逐个把 stub 换成真实现,复用 `src/mvstudio`、`pipeline/mv_engine` 的确定性能力(只调用不修改)。
接入顺序见设计文档 §7.6 里程碑。
