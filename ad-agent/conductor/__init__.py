"""ad-agent · 广告/视频创作控制器包

目录结构
  conductor/
    contracts.py  — 数据结构 + 状态机常量（复用 mv-agent，纯编排）
    state.py      — state.json 读写 + 级联失效（复用）
    layout.py     — 文件夹脚手架 + _input/ 交接（复用）
    render.py     — 执行透明化「跑前/跑后」渲染（复用）
    conductor.py  — 控制器主逻辑（复用）
    media.py      — 图像/配置助手（ad 版：画幅映射 + PIL 合成 + ffmpeg）
    tools.py      — 工具层（六步 ad 实现，调用 mvstudio provider）
    pipeline.py   — 六步声明式定义（ad 产物）
    cli.py        — 命令行驱动
"""
