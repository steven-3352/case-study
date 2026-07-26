---
name: gpt-image-2-api
description: case-study 项目通过 .env 配的 gpt-image-2 中转 API（tonbirds），整版报纸/海报式 prompt 一次性出图效果极好
metadata: 
  node_type: memory
  type: reference
  originSessionId: f1b4db04-bd80-4cbb-af1c-2c67824821ce
---

# GPT-image-2 中转 API 配置（case-study 项目）

**位置**：`/Users/wmzuo/Documents/project/case-study/.env`

```
GPT_IMAGE_API_KEY=sk-xxx
GPT_IMAGE_BASE_URL=https://us.tonbirds.com/v1
GPT_IMAGE_MODEL=gpt-image-2
```

**用法**：`openai.OpenAI(api_key=key, base_url=url, timeout=300, max_retries=2)` + `client.images.generate(model=..., prompt=..., size="1024x1536", n=1)`

## 已验证的关键行为

- **单张耗时**：60-130 秒
- **稳定尺寸**：`1024x1024` / `1024x1536`（2:3 竖版）
- **稳定性**：中转节点会偶发 `APIConnectionError`，需要 4 次重试+5s 间隔退避
- **中文渲染质量**：标题/侧栏/印章/栏目条几乎 100% 准确；正文长段落会有少量乱码字（约 5%），手机上看像"报纸纹理"，不影响观感
- **整版渲染优势明显**：与"角色立绘 + HTML 拼版面"相比，模型一锁出整版（masthead + 主标题 + 插图 + 道具 + 侧栏 + 红章）的质量和速度都更好——前提是 prompt 写得结构化（参考 [[p002-prompt-template]]）

## 适合什么任务

- 90 年代八卦杂志/狗仔报纸风轮播图（已验证）
- 类似的"复古印刷 + 大标题 + 人物插画 + 多元素"版面
- 不适合：需要精确文字排版/品牌一致性 logo/对特定字体有要求的项目

## 不该用它做什么

- 纯文字字卡（HTML+CSS 更可控）
- 真实截图复用类内容（参考 P001 的 `gen_evidence.py` 路线）
- 需要后期编辑文字的版面（一旦生成无法修改内文）

## 成本

每张 ~$0.04，18 张 < $1（gpt-image-2 medium 质量）
