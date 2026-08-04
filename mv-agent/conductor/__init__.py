"""MV 导演助手 · 控制器包

目录结构
  conductor/
    contracts.py  — 数据结构 + 状态机常量
    state.py      — state.json 读写 + 级联失效
    layout.py     — 文件夹脚手架 + _input/ 交接
    tools.py      — 工具层（调用 mv_platform 公共库）
    pipeline.py   — 六步声明式定义
    conductor.py  — 控制器主逻辑
    cli.py        — 命令行驱动
"""
