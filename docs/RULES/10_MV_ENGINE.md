# 10 · MV 引擎规范

> **来源**：从 `motion_tech_plan.md` §5, §7.1-7.3 · `design_language.md` §0, §3.1, §3.2, §4.2, §4.4, §6 · `storyboard_jimeng.md` §0.2, §0.3, §3.1-3.3, §6 提炼。引擎级知识只有一份，不在各片目录重复。

---

## 1 · 确定性渲染器的设计约束

纸片人 MV 的渲染器是**确定性 motion-graphics**：静态切图 PNG + 参数化相机 + 程序化屏幕层 FX，逐帧 PIL 合成，ffmpeg 混流。

**核心约束**（违反任何一条都会引发不可预期的画面漂移）：

1. **无随机数** —— 任何使用 `random`/`np.random` 的地方必须换成确定性替代（哈希/arange/常量）。
2. **spawn 不 fork** —— macOS Accelerate（numpy 底层 BLAS）在 fork 后的子进程里调用会挂死。多进程一律 `mp.get_context("spawn")`。
3. **原子写入** —— PNG 写目标文件前先写临时名（`<name>.tmp.<pid>`），写完再 `os.replace`。任何并发读者不会读到写了一半的文件。
4. **float → uint8 再哈希** —— 不同 BLAS 后端的 float 尾数可能差最低位，而那一位在画面上不存在。sha256 校验先 `clip(arr, 0, 255).astype(uint8)` 再计算。

---

## 2 · 相机模型

世界是一张平面（扫描仪台面 / 木桌），相机有 5 个自由度：

```
(cx, cy) 世界坐标中心 · s 缩放 · r 滚转 · elev 俯仰
```

**俯仰单独做一次透视变形**，不对每个元素分别做——平面上所有东西共享同一个平面，一次变形就够了。`elev=90` 正俯视，`elev<0` 仰拍（近端变宽）。

**缩放是解出来的，不是抄分镜的**：
- 分镜声明的景别（极端全景/大特写）→ `FRAMING` 表 → 目标画面占比
- 只在镜首和镜末按主体真实世界尺寸反解 `s`，镜内做对数插值
- **不逐帧解** —— 逐帧解会让占比恒等于目标，主体自己的尺寸台阶被相机完全抵消（B 段「折了跟没折一样」）

**`FRAMING` 表**（景别 → 主体 bbox 面积 / 画幅面积）：

| 景别 | 占比 |
|------|------|
| 极端全景 | 0.05 |
| 全景 | 0.13 |
| 中景 | 0.30 |
| 近景 | 0.48 |
| 特写 | 0.72 |
| 大特写 | 1.15 |

---

## 3 · R9 冻结门（gate_check_motion）

**判据**：滑窗扫全片，任取一个 2s 窗口。若窗口内发生切镜 → 直接过。否则窗口落在同一连续镜内，比对主体 bbox：
- 中心位移峰值 ≥ 画面宽 4%，**或**
- 面积变化峰值 ≥ 8%

两条任一成立 = 画面在动 = 过。两条都不成立 = 冻结 = **FAIL**。

**门是地板不是目标**（`gate-floor-not-target` 铁律）：
- 不得改 motion-track 的记录方式来迎合门
- 「空拍 bbox=None」是反模式——门读不到主体不等于画面在动（裁定 2 已结案）
- 任何"让验收器测不到"的提案默认驳回

**Phase 0 的关键突破**：bbox 轨迹可以在**不渲染**的情况下解析预测——整条链路（`shot_scales → Cam.at → View → warp/place → tilt`）是纯几何。预测器在 `src/mvstudio/engines/mv/track.py`，精度 p95 = 0.041%W，gate 判定与真实轨迹**逐字节一致**。冻结门从渲后 3 分钟变成渲前 72 ms。

---

## 4 · 原子库准入契约（`mv_engine/atoms/`）

四条，客观可判，不靠人工感觉：

1. **不带默认颜色** —— 颜色一律由调用方按该片 design_language §1 传入
2. **纯函数** —— 无 I/O、无模块级全局、`(arr | Image, **纯标量) -> 同类型`（`crease`/`stack_edge` 就地画是显式例外，返回 None）
3. **必须声明 `touches_alpha: bool`** —— 不动 alpha 的原子（`banding/lid_flare/grain/bloom`）整个跳过预测器几何链；动 alpha 的（`paper_fold/tilt/_feather`）才进几何链。声明错了不会报错，只会让预测器安静地算错
4. **必须能被 `lock.py` 摘要覆盖** —— 固定输入 × 固定参数 → sha256 锁死的输出。`lock.json` 里有 15 个 case，每次改原子必须重跑 `--check`

---

## 5 · 帧缓存设计（`src/mvstudio/engines/mv/cache.py`）

**cache key = blake2b**(规范化 JSON，包含):
- `version`, `t`(1μs精度), `sid`
- `cam` kwargs, `items(t,k)` 序列化, `subject`, `bg`, `fx`（**不含 `note`**）
- `code` = src/mvstudio/engines/mv/*.py + 本片包 *.py 的 sha256 合并摘要
- `render_cfg` = W/H/FPS/PAD_W/PAD_H

**存储布局**：
```
<cache_root>/<key[:2]>/<key>.png  — 内容寻址，跨版本共享
<out>/<version>/_frames/f%05d.png — hardlink 到缓存
<out>/<version>/index.json        — 帧号 → key 映射
```

**流程**：父进程算全部 N 个 key → 分 hit/miss → miss 塞给 spawn worker pool → 全量 hardlink → **motion.json 由 `track.predict_track` 直出**（100% 命中时 worker 不跑，motion 仍然有）。

---

## 6 · 分镜 YAML 结构（`mv_engine/solver/`）

每片 `shots_{a,b}.yaml` 格式：

```yaml
shots:
  - sid: A02
    t: [23.394, 24.323]
    cam: {size0: 大特写, zoom: 1.22, dx: 0.16, ease: ease_out_quad}
    layout:
      base: bed           # chassis_plastic + glass_platen 两层底
      items:
        - fn: doll
          name: cy
          world_h: 2600
          crop: EYE
          scan_split: true
    subject: [2]
    bg: [glass_platen, A_SHADOW, 0.62, 1400.0]
    fx: {scan: [0.86, 0.62, 0.66, 0.66]}
    note: ...
```

**pin 机制（H7）**：yaml 里任何非空的 `cam`/`layout`/`pin` 字段即 pin，求解器不改。

**求解器产出**：`shots.solved.yaml`（每个求解字段带 `solver_note`）+ `solver_report.md`（多样性表格）。

---

## 7 · 硬约束 H1-H7

| 约束 | 内容 |
|------|------|
| H1 | 每镜内 2s 窗在**预测轨迹**上过 gate_check_motion |
| H2 | 相邻镜不共享 (move family, size0) |
| H3 | 任一 move family 或 trans 占比 ≤ 50% |
| H4 | `|{m}| ≥ 6`，`|{x}| ≥ 5`（多样性下限） |
| H5 | 每段落 ≥3 种景别，且至少 1 处相邻镜面积比 ≥ 8× |
| H6 | 硬切两侧 elev 不得变号，除非转场是 flip/flash_white |
| H7 | yaml 里任何非空字段即 pin（人工覆盖入口） |

**软目标**（优先级依次）：move family Shannon 熵 · trans 熵 · 相邻景别对比 · 4 镜窗口 bigram 重复惩罚（所有分量有饱和上限）。

---

## 8 · 性能基准（《明月天涯》22.465-29.780s, 1920×1080）

| 操作 | 当前耗时 | 说明 |
|------|---------|------|
| 冷渲染（438 帧，jobs=4） | ~320s | 全 miss，spawn 4 进程 |
| 热渲染（438 帧，100% 命中） | ~9s | 仅 key 计算 + hardlink |
| bbox 预测（219 帧） | 72 ms | hulls 已缓存 |
| gate_check_motion | <1s | 读 motion.json |
| 求解器（21 镜，beam=16） | <1s | 约 10K 次评估 |

内存上限：单进程 RSS 约 1-1.3 GB。超过 4 个并发 worker 会造成内存带宽瓶颈（实测 jobs=6 比 jobs=4 慢 3%，jobs=8 慢 13%）。
