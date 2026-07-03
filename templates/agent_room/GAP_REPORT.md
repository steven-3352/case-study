# GAP_REPORT · 新选题开工缺口报告

> 新选题第一步必填。目的不是补文件，而是先阻止假完成。  
> `blocking` 未清空前，禁止写 `pass / approved / score >=90`，禁止 TTS / gpt-image / render。

```yaml
content_id:
status: blocked_before_content_gate
review_source: draft_self_generated
allowed_next_step:
  - 补真实调研
  - 补同平台 hook benchmark
  - 补真实互评
not_allowed:
  - TTS
  - gpt-image
  - render
  - approved
```

## 当前阶段

- [ ] 立项已完成
- [ ] 真实网络调研已完成
- [ ] 同平台视频 benchmark 已完成
- [ ] 洞察包已完成
- [ ] 真实多 Agent 互评已完成
- [ ] 视觉原创门已完成

## Blocking

| 阻塞项 | 当前证据 | 需要补什么 | 完成后谁复核 |
|--------|----------|------------|--------------|
| | | | |

## 允许做

- 

## 禁止做

- 

## 降级/升级规则

- 有任一 blocking → `status: blocked_before_*`
- 单模型生成 → `review_source: draft_self_generated`
- 真实互评通过 → `review_source: pass_agent_reviewed`
- 人类复核通过 → `review_source: pass_human_reviewed`
- gate_check 通过 → `review_source: pass_gate_checked`
