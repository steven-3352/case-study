---
name: gpt-image-model-fallback
description: tonbirds 中转多参考图(3+ ref)易超时/400/503；根因是并发过高耗尽 distributor 池，不是模型名问题；降并发(2线程)+长 timeout 是真正解法
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 1b8bd492-69a9-47ed-95a9-32ed78edf3ed
---

tonbirds 中转 `/v1/images/edits` 在 multi-reference 多参考图（2-4 张 `image` field）+ 5 线程并发场景下，大概率出现：300s Read timeout、400 invalid_value、503 "分组 X 下模型 gpt-image-2 无可用渠道（distributor）"。

**根因排查过程（2026-07-18 D07 客户武侠 MV 出图）：**
1. 最初怀疑是 `gpt-image-2-1k` 模型本身对多参考图支持差 → 用户在 `.env` 加 `GPT_IMAGE_MODEL2=gpt-image-2-count` 做 fallback
2. 单独探路 `gpt-image-2-count` 先报 400 `model_price_error`（tonbirds 后台该模型未配价）→ 用户去后台配好价格后单 shot 测试成功（4-ref, ~5min）
3. 但把 6 张多参考图 shot 以 **5 线程并发**同时提交给 `gpt-image-2-1k`+`gpt-image-2-count` fallback 时，两个模型都开始报 503 `无可用渠道（distributor）`——这是并发把 tonbirds 后端渠道池打满，跟模型名无关
4. **最终解法**：用户把 `.env` 换回单一模型名 `GPT_IMAGE_MODEL=gpt-image-2`（去掉 -1k/-count 后缀，`GPT_IMAGE_MODEL2` 也删了），脚本改用 `GPT_IMAGE_WORKERS=2`（2 线程而非 5）重跑 → 6/6 全部一次成功，单张 60s-8min 不等

**How to apply（下次遇到同类报错时的正确顺序）：**
1. 先看 400/503 body 原文（脚本已加 `_post_once` 里的 body snip 日志），不要只看 status code 猜
2. `model_price_error` → 是 tonbirds 后台没给这个模型配价，需要人去后台开自用模式/配价，代码侧无法绕过
3. `无可用渠道（distributor）` → 是并发过高，把 `ThreadPoolExecutor(max_workers=...)` 调低到 2（脚本已支持 `GPT_IMAGE_WORKERS` 环境变量覆盖默认 5），不要急着切模型名
4. 多参考图（3+ ref）比单参考图慢很多也更容易撞上游限流，5 线程对多参考图 batch 偏激进，2 线程更稳
5. 模型名以 `.env` 当前值为准，不要假设 `-1k`/`-count` 后缀还存在——这两个是探路阶段的临时产物，最终收敛回了不带后缀的 `gpt-image-2`

**关联：** [[gpt-image-2-api]] · [[read-env-example-first]]
