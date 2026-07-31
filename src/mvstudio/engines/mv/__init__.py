"""跨片累积的 MV 渲染引擎。

**分层**:

    atoms/    与内容无关的原子件(scan_bar / paper_fold / crease...)
    config    引擎级几何常量(W/H/PAD/景别表)
    ease      纯标量缓动
    camera    Cam · View · sample_plane · tilt · w2s · quad_of
    track     解析 bbox 预测器 —— R9 冻结门从渲后 3 分钟 → 渲前 72 ms

**per-project 的东西不在这**:调色板、素材路径、时间轴、分镜表和字体路径，
全部由用户项目合同声明并通过显式 Session 注入。
"""
