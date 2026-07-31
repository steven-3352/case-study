"""一镜 —— 时间区间 + 相机轨迹 + 每帧构造 items 的回调。

`items` 目前是 callable `(t, k) -> tuple[Item, ...]` —— 分镜参数 yaml 化(Phase 1b)
会把它换成注册表 + 声明式叶子,现在保持 callable 是为了让 Phase 1a 一行内容不改。

`shot_scales` 只解镜首/镜末两个占比,中间做对数插值 —— 逐帧解会让每帧占比恒等于
目标值,物体自己的尺寸变化在画面上被完全抵消(B 段每半拍面积减半 → 折了跟没折一样)。
`hold_size` 是这条规则的显式 opt-out(B 段某几镜相机不跟主体)。

`_SCALES` 缓存按 `sh.sid` 索引 —— A/B 版分别用 A01-A11 / B01-B10,不重名。
Phase 1a 保持原样;Phase 3 帧缓存重构时会把 key 收到 `(video, version, sid)` 做防御。
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .camera import Cam, solve_scale
from .ease import _clamp


@dataclass(frozen=True)
class MShot:
    sid: str
    t0: float
    t1: float
    cam: Cam
    items: object                    # (t, k) -> tuple[Item, ...]
    subject: tuple = (0,)            # 哪些 item 计入 R9 的主体 bbox
    bg: tuple = ()                   # (纹理名, 上色, 对比, 世界瓷砖边长)
    fx: dict = field(default_factory=dict)
    note: str = ""

    def k(self, t: float) -> float:
        return _clamp((t - self.t0) / max(1e-6, self.t1 - self.t0))


def active(shots: list, t: float) -> MShot:
    cur = shots[0]
    for s in shots:
        if t >= s.t0:
            cur = s
    return cur


_SCALES: dict = {}


def shot_scales(sh: MShot) -> tuple[float, float, tuple]:
    """镜首/镜末各解一次缩放,外加相机该看向哪儿。

    返回 `(s0, s1, look)`。`look` 是镜首主体包围盒的世界中心 —— 相机默认盯着主体,
    `Cam.look` 在此之上作偏移。物件不一定摆在世界原点(A01 的机器整个在原点上方),
    盯原点会把主体挤出画。
    """
    if sh.sid in _SCALES:
        return _SCALES[sh.sid]
    out, look = [], (0.0, 0.0)
    for k, share in ((0.0, sh.cam.share0), (1.0, sh.cam.share1)):
        its = sh.items(sh.t0 + k * (sh.t1 - sh.t0), k)
        xs = [its[i].rect for i in sh.subject]
        x0, y0 = min(r[0] for r in xs), min(r[1] for r in xs)
        x1 = max(r[0] + r[2] for r in xs)
        y1 = max(r[1] + r[3] for r in xs)
        if k == 0.0:
            look = (sh.cam.look[0] + (x0 + x1) / 2, sh.cam.look[1] + (y0 + y1) / 2)
        out.append(solve_scale(share, x1 - x0, y1 - y0))
    if sh.cam.hold_size:
        # 镜末不重解:主体自己在镜内缩小的那部分,就该让观众看见。
        # 反解占比的前提是"主体尺寸不变,靠相机决定它多大";B 段的纸每半拍面积减半,
        # 镜末再解一次等于相机同步推近,四折之后纸在屏幕上还是那么大 —— 折了跟没折一样。
        out[1] = out[0] * sh.cam.zoom
    _SCALES[sh.sid] = (out[0], out[1], look)
    return _SCALES[sh.sid]
