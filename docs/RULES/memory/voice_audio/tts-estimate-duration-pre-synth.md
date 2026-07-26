---
name: tts-estimate-duration-pre-synth
description: TTS 合成前必跑 estimate_duration.py，捕获 target_dur 溢出；D03 s2 8.55s vs 5s 溢出 68% 若前置就能避免 M7 挤压
metadata: 
  node_type: memory
  type: reference
  originSessionId: 3f745456-49f1-429e-9665-8b9c342c2ce6
---

# TTS 时长前置估算（2026-07-04 P3 完成）

**位置：** `pipeline/tts/estimate_duration.py`

**触发时机：** audio_plan.yaml 写完 / pipeline_config.yaml segments 写完之后、跑 gen_vo 之前

## 用法

```bash
# 单条文本
python3 pipeline/tts/estimate_duration.py --text "…" --speed 0.95 --emotion neutral --target 5.0

# 整个 pipeline_config
python3 pipeline/tts/estimate_duration.py --config publish/2026-WXX/DYY-*/pipeline_config.yaml
```

## 判据

- **OK**：|Δ| < 15%（tail_pad 或 pad 自然吸收）
- **WARN**：15-30% 溢出（关注 · 可能挤后段）
- **FAIL**：≥30% 溢出（必改稿或降 speed）
- **UNDER**（负 Δ）永远 OK（tail_pad 补静音）

## 拟合参数（MiniMax 男声·精英精品 · D03 8 段拟合）

- `BASELINE_CHAR_RATE = 5.0` 字/秒 at speed 1.0
- emotion mult：neutral 1.0 / sad 0.85 / gentle 0.95 / happy 1.05
- 英文单词按音节数（len/2.5，min 1）
- 短段（<3s）加 0.3s head/tail overhead

## D03 验证结果

估算捕获了 D03 实际发生的 s2（+68%）和 s10（+33%）溢出。若前置跑，M7 不会被挤到 1.7s。

## D04 反向修正（2026-07-05）

**MiniMax 实际 vs estimate 比：D04 8 段 = 1.068（慢 6.8%，不是快 5%）**

之前一句"MiniMax 实发常 5% 快"是 D03 单条噪音观察，D04 反向证实中速段（speed 1.08-1.10）实发更慢：
- estimate 62.35s · actual 66.59s
- 每段普遍慢 5-10%
- 高频段（1.10）慢得更明显

**修正判据：**
- 若 estimate ≥ target_douyin_cap 60s → 必须再缩 -3~-5%（bump speed 或删字）
- Estimate + 10% buffer 应作为 render 门槛 · 不是 estimate 通过就能 render
- Render 一次后必读 seg_timing.json total · 若 >target 立即回改 speed

## D05 二次证实（2026-07-05）

**speed 1.08 · MiniMax 慢 26.3% 于 estimator baseline · 更极端**

- estimate 47.68s（79.5% 利用率）· actual 60.22s
- Δ = +12.54s · 慢 26.3%

**规律拟合（3 数据点）：**
| base_speed | 实测 vs estimator |
|---|---|
| 0.95-0.98 | actual ≈ +7% |
| 1.08 | actual ≈ +26% |
| 1.10 | actual ≈ 更慢 |

**最终判据（2026-07-05 覆盖）：**
- base_speed 0.95-1.00 → estimate + 10% buffer
- base_speed 1.05-1.10 → **estimate + 30% buffer**（D05 观测）
- 若 estimate 已跑到 ≥ 45s at speed 1.08 · 上限就已到 · 必须缩稿

## 反例

- 溢出 fail 但不改稿直接 render → M7 挤压重演（D03 教训）
- 只看总长不看逐段 → 总长 58s 达标但 s2 单段就溢 3.4s
- estimate 通过就 render → D04 教训 · MiniMax 实发 +6.8% CTA 完全被裁
- 高 base_speed（1.08+）用 +10% buffer → D05 教训 · 需 +30% buffer
