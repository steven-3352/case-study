# VIDEO_ITERATE_LOG

## office-selfie-dance · iteration 2 · 2026-08-06

- Route: `ad-agent` -> `SeedancePort` -> `doubao-seedance-2-0-260128`
- Source: `tmp/office_lookbook_reference/office-selfie-back-turn-dance-v2.mp4`
- Category: 3 · 动作不自然
- Observations:
  - 参考片前 1 秒由脸部近景快速拉到大腿景，生成片从远距离全身固定景别开始。
  - 参考片有抬手理发、双肘展开、手臂低位交叉的连续动作，生成片主要是转身与单手摸发。
  - 参考片腰胯在左右方向产生肉眼明显位移并以侧压 S 形结束，生成片腰胯横向位移接近不可见。
- Root cause: 首帧景别与参考动作的起始状态冲突；prompt 将核心动作弱化为“小幅摆动”，同时加入转身，导致模型把动作预算消耗在转身上。
- Minimal edit variables:
  - `first_frame_composition`: 远距离全身背影 -> 头发遮脸的近距离自拍开场；无脸全身背影作为服装与体型参考帧。
  - `motion_choreography`: 背身转正 + 泛化轻摆 -> 按 0.0-8.0 秒明确抬手、肘部、手腕、腰胯横向位移与结束姿态。
- Prompt: `tmp/office_lookbook_reference/seedance-selfie-choreo-v3-prompt.txt`
