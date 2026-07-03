# 素材策略 · asset_strategy

> 工种：素材制片 + 事实校验员 + 形式策略官  
> 位置：`design/asset_strategy.md`  
> 原则：**事实可以生成，但来源不能伪造。**  
> `generated_fact` 是合法素材来源；但不能冒充真实客户事实。

## 0. 结论

```yaml
status: draft | pass | fail
content_id:
review_source: draft_self_generated | pass_agent_reviewed | pass_human_reviewed
asset_policy: generated_fact_allowed
needs_asset_log: true
```

## 1. 素材来源类型

| source_type | 含义 | 本条是否使用 |
|-------------|------|--------------|
| real_private | 真实私域素材 | |
| public_reference | 公开来源素材/评论/视频/报告 | |
| generated_fact | AI 生成事实型素材 | |
| synthetic_visual | AI/代码生成解释性视觉 | |
| hybrid | 真实结构 + 生成内容 | |

## 2. 镜头素材计划

| 镜头/页 | 需要什么素材 | source_type | 如何获得 | 是否标示意 | 禁止误读 |
|---------|--------------|-------------|----------|------------|----------|
| | | | | | |

## 3. 允许 AI 生成的事实

| generated_fact | 生成目的 | 合理性依据 | 不得声称 |
|----------------|----------|------------|----------|
| | | | |

## 4. 需要 Agent 采集的素材

| 素材 | 用途 | 来源范围 | 验收 |
|------|------|----------|------|
| | | | |

## 5. 必须标记 / 必须禁止

### 必须内部标记

- 

### 画面必要时标“示意”

- 

### 禁止

- 不把 generated_fact 写成真实客户案例。
- 不把 synthetic_visual 写成真实后台。
- 不伪造品牌、平台、客户身份。

## 6. asset_log 要求

实际制作后必须补：

```text
assets/asset_log.md
```

至少记录：

- 文件名
- source_type
- 来源 URL 或生成 provider
- prompt / 参数（如 AI 生成）
- 授权 / 备注
- 服务镜头
