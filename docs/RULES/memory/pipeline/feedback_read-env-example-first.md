---
name: feedback_read-env-example-first
description: 接手项目第一动作:读 .env.example 而不是猜凭证;基础服务调用要先抄已跑通的姊妹产线作业
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 9454e7a7-84bb-426d-88ad-0485259de3b7
---

W27D04 配音用 Edge 兜底,被用户质问"为什么没用 MiniMax"。诊断后发现根因不是没公共脚本(`pipeline/tts/gen_speech.py` + `minimax_client.py` 是齐的)，是我**没读项目的入口契约**:

1. `.env.example` 第 2 行明文写「云雾中转:`MINIMAX_BASE_URL=https://yunwu.ai/minimax`」—— 我把 `TTS_BASE_URL=https://yunwu.ai`(图像通道地址) 直接套用,丢了 `/minimax` 前缀,所有调用 404
2. D03 海外获客 4 天前刚跑通过 MiniMax via yunwu,我没去 `git log` / `cat _d03_tts_config.yaml` 抄作业

**Why:** 调通用基础服务(TTS、做图、LLM、向量等)前没读现成的`.env.example` + 同源已跑通的姊妹脚本,等于关键约定全靠猜。一次猜错(/minimax 前缀漏写)就直接降级 fallback,白白付出代价。

**How to apply:**
- 任何 D0X 新选题接手第一动作: `cat .env.example` 看每条服务的中转地址范例,对照 `.env` 看是否填齐
- 调通用基础服务(MiniMax/Edge/Volc TTS、GPT-image、Claude 等)前先 `git log -- pipeline/tts/` 或 `grep -r "minimax\|tts\|gpt-image" publish/2026-W*/` 找最近一条跑通的产线,直接抄它的 `_dNN_*_config.yaml`
- 一次 4xx/5xx 不能直接降级 fallback,要查根因 —— "中转可能会出错多试几次"是有效战术,但前提是 URL 拼写本身先核对正确
- 公共脚本是齐的(`pipeline/tts/gen_speech.py` 的 `synthesize_text` 统一封装 provider 路由),凭证缺失才会掉到 Edge — 看到 fallback 警告先查 `.env` 而不是改代码
