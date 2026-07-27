"""跨片累积的 MV 渲染引擎。

**分层**:

    atoms/    与内容无关的原子件(scan_bar / paper_fold / crease...)
    config    引擎级几何常量(W/H/PAD/景别表)
    ease      纯标量缓动
    camera    Cam · View · sample_plane · tilt · w2s · quad_of
    track     解析 bbox 预测器 —— R9 冻结门从渲后 3 分钟 → 渲前 72 ms

**per-film 的东西不在这**:调色板、素材路径、SEG 时间轴、分镜表、字体路径,
由每片自己的 `pipeline/voice_room/<film>/` 声明。

原子库来源见 `atoms/__init__.py`。第一支片《明月天涯》从 `mingyue_render.py`
逐步搬入,函数体逐字未改 —— 438 帧 sha256 逐帧一致是 Phase 1a 的验收线。
"""
