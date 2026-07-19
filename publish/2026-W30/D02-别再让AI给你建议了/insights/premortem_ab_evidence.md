# D02 事前验尸法 A/B 实验

> 状态：`draft_evidence` · 原始 API 输出未删改 · 需人工判定

- 生成时间（UTC）：`2026-07-19T00:04:25+00:00`
- 模型：`claude-opus-4-8`
- 轮数：`2`
- 固定变量：模型、system prompt、计划事实、模型默认采样参数
- 干预单位：整组 Prompt。A 为普通评价请求；B 同时加入失败前提、倒推任务、排序要求、事实锚定、禁止先夸和禁止补救建议。
- 归因边界：本实验不能拆分其中任何一句的单独因果效应，只能比较整组事前验尸指令与普通评价请求。
- 判定：比较是否更快进入风险、是否每条都绑定现有事实、是否减少泛化建议。

## B 组指令原文

> 请做一次事前验尸：假设六个月后这个辞职创业计划已经失败。不要提出补救建议，不要先说优点。请按可能性和破坏性排序，倒推导致失败的三个最关键原因，并指出计划中的哪条现有事实支持这个判断。

计划如下：
[同一份计划]

## Round 1

### A · 普通评价

- SHA256：`0f939cc76fa4447ccc3f356368b6b8a802d24a33fb952709db3f9db3a444f632`
- 词面统计：`{"chars": 510, "encouragement_hits": {"可行": 1}, "criticism_hits": {}, "first_criticism_char": -1}`

总体判断：该计划具备一定技能基础，但缺乏经过验证的获客能力和成果证明，当前状态下商业可行性风险较高。

按严重性排序的三个最关键风险：

**1. 缺乏成果证明，服务价值无法验证（最严重）**
计划中唯一提及的实操结果是"做过 4 周自己的账号，涨粉几乎为零"。你要向商家出售的正是内容运营涨粉这类能力，而你自己账号的成果恰恰证明失败。中小商家付费购买的是效果，而你目前没有任何可展示的成功案例来支撑收费。这是直接动摇商业模式根基的风险。

**2. 没有获客路径，收入目标缺乏落地依据**
计划设定"先接 3-5 个客户""月目标 2 万"，但未说明如何找到这些客户、通过什么渠道触达、凭什么让商家选择你。技能（懂 AI、会写脚本、会剪辑）属于交付能力，而非获客能力，二者是两回事。收入目标在没有获客方案支撑的情况下，只是数字而非可执行计划。

**3. 辞职带来的收入中断与现金流风险**
计划是"辞职"后再开始，意味着放弃稳定收入的同时，进入一个尚无客户、无验证成果的业务。计划中没有提及积蓄、缓冲期或过渡安排。在客户数为零、成果为零的起点上切断现有收入来源，一旦获客与交付未达预期，将面临直接的生存性现金流压力。

#### A 调用审计元数据

- 请求时间（UTC）：`2026-07-19T00:03:13.221599+00:00`
- 返回时间（UTC）：`2026-07-19T00:03:26.172631+00:00`
- response id：`msg_011CdASGj9aZVNNcQC5B6anE`
- returned_model：`claude-opus-4-8`
- usage：`{"claude_cache_creation_1_h_tokens": 0, "claude_cache_creation_5_m_tokens": 0, "completion_tokens": 535, "completion_tokens_details": {"audio_tokens": 0, "image_tokens": 0, "reasoning_tokens": 0, "text_tokens": 0}, "input_tokens": 736, "input_tokens_details": null, "output_tokens": 0, "prompt_tokens": 736, "prompt_tokens_details": {"audio_tokens": 0, "cached_tokens": 0, "image_tokens": 0, "text_tokens": 0}, "total_tokens": 1271, "usage_semantic": "openai", "usage_source": "anthropic"}`
- assistant content SHA256：`0f939cc76fa4447ccc3f356368b6b8a802d24a33fb952709db3f9db3a444f632`
- API response body SHA256：`61811573c50c013d85acf8de6663d36bc37314cc336c4e3d3a8d8ab3640f29d7`
- 脱敏请求体（原请求不含密钥与 base URL）：

```json
{
  "messages": [
    {
      "content": "你是一名严格的商业计划风险评估者。只根据计划中给出的事实评估，不假设额外背景。请先用一句话给出总体判断，再按严重性排序指出三个最关键的风险及理由。",
      "role": "system"
    },
    {
      "content": "请评价下面这个计划：\n\n我想辞职做 AI 内容代运营，帮中小商家做小红书和抖音的 AI 内容。我做过 4 周自己的账号，涨粉几乎为零，但我懂 AI 工具、会写脚本、会剪辑。我打算先接 3-5 个客户，按月收费，一个月目标 2 万。",
      "role": "user"
    }
  ],
  "model": "claude-opus-4-8"
}
```

- 未删改 API 响应体：

```json
{"id":"msg_011CdASGj9aZVNNcQC5B6anE","model":"claude-opus-4-8","object":"chat.completion","created":1784419406,"choices":[{"index":0,"message":{"role":"assistant","content":"总体判断：该计划具备一定技能基础，但缺乏经过验证的获客能力和成果证明，当前状态下商业可行性风险较高。\n\n按严重性排序的三个最关键风险：\n\n**1. 缺乏成果证明，服务价值无法验证（最严重）**\n计划中唯一提及的实操结果是\"做过 4 周自己的账号，涨粉几乎为零\"。你要向商家出售的正是内容运营涨粉这类能力，而你自己账号的成果恰恰证明失败。中小商家付费购买的是效果，而你目前没有任何可展示的成功案例来支撑收费。这是直接动摇商业模式根基的风险。\n\n**2. 没有获客路径，收入目标缺乏落地依据**\n计划设定\"先接 3-5 个客户\"\"月目标 2 万\"，但未说明如何找到这些客户、通过什么渠道触达、凭什么让商家选择你。技能（懂 AI、会写脚本、会剪辑）属于交付能力，而非获客能力，二者是两回事。收入目标在没有获客方案支撑的情况下，只是数字而非可执行计划。\n\n**3. 辞职带来的收入中断与现金流风险**\n计划是\"辞职\"后再开始，意味着放弃稳定收入的同时，进入一个尚无客户、无验证成果的业务。计划中没有提及积蓄、缓冲期或过渡安排。在客户数为零、成果为零的起点上切断现有收入来源，一旦获客与交付未达预期，将面临直接的生存性现金流压力。"},"finish_reason":"stop"}],"usage":{"prompt_tokens":736,"completion_tokens":535,"total_tokens":1271,"usage_semantic":"openai","usage_source":"anthropic","prompt_tokens_details":{"cached_tokens":0,"text_tokens":0,"audio_tokens":0,"image_tokens":0},"completion_tokens_details":{"text_tokens":0,"audio_tokens":0,"image_tokens":0,"reasoning_tokens":0},"input_tokens":736,"output_tokens":0,"input_tokens_details":null,"claude_cache_creation_5_m_tokens":0,"claude_cache_creation_1_h_tokens":0}}
```

### B · 事前验尸

- SHA256：`082eb54fffb14eaae4c05e1986ca3de03bcf3387088fd4b609b2a21cbead54f6`
- 词面统计：`{"chars": 902, "encouragement_hits": {"有机会": 1}, "criticism_hits": {}, "first_criticism_char": -1}`

我需要先说明一个问题：计划中提供的事实非常有限，无法支撑完整的事前验尸。我只能基于你给出的少数事实进行倒推，但其中有几处判断只能建立在"计划中缺失了什么"之上，这一点我会明确标出，避免让你误以为它们有计划内的事实支撑。

**总体判断：这个计划最可能因"无法证明自己能为客户带来结果"而失败——你唯一可验证的实操记录（自营账号）恰恰是一次失败。**

以下按"可能性 × 破坏性"倒序排列三个最关键原因：

**1. 你唯一的能力证据是负面的**
- 支持事实：计划明确写着"做过 4 周自己的账号，涨粉几乎为零"。
- 倒推：代运营卖的是"结果"（涨粉/转化），不是"会用工具"。你列举的"懂 AI 工具、会写脚本、会剪辑"都是投入端能力，而客户付费买的是产出端结果。当你去谈客户时，你能展示的唯一真实案例是一个零增长账号。六个月后失败最可能的直接原因，就是签不下或续不了客户，因为你无法证明自己能做成。

**2. 收入目标与客户数量在计划自身内部就对不上**
- 支持事实：计划写"先接 3-5 个客户""一个月目标 2 万"。
- 倒推：这意味着单客月费需达到 4000–6667 元。对一个只有 4 周失败自营经验、零成功案例的新供应商，中小商家愿意支付这个价位的可能性很低。计划没有给出任何定价依据或客户付费意愿的事实，因此 2 万目标缺乏计划内支撑，收入达不到导致现金流断裂是失败的高概率路径。

**3. 计划中完全没有"获客"这一环节**
- 支持事实：计划中出现的动作只有"接 3-5 个客户"，但对"客户从哪来、怎么谈成"没有任何描述。
- 倒推：这一条我必须明确标注——它的依据是"计划中的缺失"，而非某条已写出的事实。但正因为缺失如此彻底，它本身就是风险：从辞职到失败的六个月里，若没有获客渠道，前两个风险根本没有机会被暴露，你会直接卡在"接不到第一个客户"上。

需要说明的界限：以上第 1、2 条有计划内的直接事实支撑；第 3 条依赖的是计划的空白，我不能假装它是既有事实。若你补充定价方式、客户来源、以及自营账号"涨粉为零"的具体原因，我可以做一次更严格、更少推测的复盘。

#### B 调用审计元数据

- 请求时间（UTC）：`2026-07-19T00:03:26.172967+00:00`
- 返回时间（UTC）：`2026-07-19T00:03:48.746092+00:00`
- response id：`msg_011CdASHgkF3WE6c732aRjFG`
- returned_model：`claude-opus-4-8`
- usage：`{"claude_cache_creation_1_h_tokens": 0, "claude_cache_creation_5_m_tokens": 0, "completion_tokens": 929, "completion_tokens_details": {"audio_tokens": 0, "image_tokens": 0, "reasoning_tokens": 0, "text_tokens": 0}, "input_tokens": 828, "input_tokens_details": null, "output_tokens": 0, "prompt_tokens": 828, "prompt_tokens_details": {"audio_tokens": 0, "cached_tokens": 0, "image_tokens": 0, "text_tokens": 0}, "total_tokens": 1757, "usage_semantic": "openai", "usage_source": "anthropic"}`
- assistant content SHA256：`082eb54fffb14eaae4c05e1986ca3de03bcf3387088fd4b609b2a21cbead54f6`
- API response body SHA256：`f6a5b557cab211d969c426e88b90e828ca92c084f16c3755e43683ff12748eec`
- 脱敏请求体（原请求不含密钥与 base URL）：

```json
{
  "messages": [
    {
      "content": "你是一名严格的商业计划风险评估者。只根据计划中给出的事实评估，不假设额外背景。请先用一句话给出总体判断，再按严重性排序指出三个最关键的风险及理由。",
      "role": "system"
    },
    {
      "content": "请做一次事前验尸：假设六个月后这个辞职创业计划已经失败。不要提出补救建议，不要先说优点。请按可能性和破坏性排序，倒推导致失败的三个最关键原因，并指出计划中的哪条现有事实支持这个判断。\n\n计划如下：\n我想辞职做 AI 内容代运营，帮中小商家做小红书和抖音的 AI 内容。我做过 4 周自己的账号，涨粉几乎为零，但我懂 AI 工具、会写脚本、会剪辑。我打算先接 3-5 个客户，按月收费，一个月目标 2 万。",
      "role": "user"
    }
  ],
  "model": "claude-opus-4-8"
}
```

- 未删改 API 响应体：

```json
{"id":"msg_011CdASHgkF3WE6c732aRjFG","model":"claude-opus-4-8","object":"chat.completion","created":1784419428,"choices":[{"index":0,"message":{"role":"assistant","content":"我需要先说明一个问题：计划中提供的事实非常有限，无法支撑完整的事前验尸。我只能基于你给出的少数事实进行倒推，但其中有几处判断只能建立在\"计划中缺失了什么\"之上，这一点我会明确标出，避免让你误以为它们有计划内的事实支撑。\n\n**总体判断：这个计划最可能因\"无法证明自己能为客户带来结果\"而失败——你唯一可验证的实操记录（自营账号）恰恰是一次失败。**\n\n以下按\"可能性 × 破坏性\"倒序排列三个最关键原因：\n\n**1. 你唯一的能力证据是负面的**\n- 支持事实：计划明确写着\"做过 4 周自己的账号，涨粉几乎为零\"。\n- 倒推：代运营卖的是\"结果\"（涨粉/转化），不是\"会用工具\"。你列举的\"懂 AI 工具、会写脚本、会剪辑\"都是投入端能力，而客户付费买的是产出端结果。当你去谈客户时，你能展示的唯一真实案例是一个零增长账号。六个月后失败最可能的直接原因，就是签不下或续不了客户，因为你无法证明自己能做成。\n\n**2. 收入目标与客户数量在计划自身内部就对不上**\n- 支持事实：计划写\"先接 3-5 个客户\"\"一个月目标 2 万\"。\n- 倒推：这意味着单客月费需达到 4000–6667 元。对一个只有 4 周失败自营经验、零成功案例的新供应商，中小商家愿意支付这个价位的可能性很低。计划没有给出任何定价依据或客户付费意愿的事实，因此 2 万目标缺乏计划内支撑，收入达不到导致现金流断裂是失败的高概率路径。\n\n**3. 计划中完全没有\"获客\"这一环节**\n- 支持事实：计划中出现的动作只有\"接 3-5 个客户\"，但对\"客户从哪来、怎么谈成\"没有任何描述。\n- 倒推：这一条我必须明确标注——它的依据是\"计划中的缺失\"，而非某条已写出的事实。但正因为缺失如此彻底，它本身就是风险：从辞职到失败的六个月里，若没有获客渠道，前两个风险根本没有机会被暴露，你会直接卡在\"接不到第一个客户\"上。\n\n需要说明的界限：以上第 1、2 条有计划内的直接事实支撑；第 3 条依赖的是计划的空白，我不能假装它是既有事实。若你补充定价方式、客户来源、以及自营账号\"涨粉为零\"的具体原因，我可以做一次更严格、更少推测的复盘。"},"finish_reason":"stop"}],"usage":{"prompt_tokens":828,"completion_tokens":929,"total_tokens":1757,"usage_semantic":"openai","usage_source":"anthropic","prompt_tokens_details":{"cached_tokens":0,"text_tokens":0,"audio_tokens":0,"image_tokens":0},"completion_tokens_details":{"text_tokens":0,"audio_tokens":0,"image_tokens":0,"reasoning_tokens":0},"input_tokens":828,"output_tokens":0,"input_tokens_details":null,"claude_cache_creation_5_m_tokens":0,"claude_cache_creation_1_h_tokens":0}}
```

## Round 2

### A · 普通评价

- SHA256：`664dce67a45dc6053dfcf4ceff0413cc249d25baf83e5487ecb3bf1661acf87d`
- 词面统计：`{"chars": 603, "encouragement_hits": {}, "criticism_hits": {"致命": 1, "未验证": 1}, "first_criticism_char": 97}`

总体判断：该计划在核心能力（帮客户涨粉/带来商业价值）上尚未得到验证，属于高风险、需先小范围验证再辞职的计划。

以下按严重性排序，指出三个最关键的风险及理由：

**1. 核心成果未被验证（最致命）**
计划中明确写到"做过 4 周自己的账号，涨粉几乎为零"。你要向客户出售的正是"内容运营带来增长"这一结果，而你在自己可完全掌控的账号上、用了 4 周仍未做出成绩。这意味着你目前能证明的只是"会用工具、会剪辑"，而非"能带来客户想要的结果"。客户付月费买的是效果，不是工具操作，这个缺口是整个计划的根本风险。

**2. 客户与收入目标缺乏获取路径**
计划设定"先接 3-5 个客户""一个月 2 万"，但没有说明客户从哪里来、如何说服他们付费。按 2 万/3-5 个客户折算，单客约 4000-6667 元/月，对中小商家不算低。在你没有可展示的成功案例（见风险 1）的前提下，如何冷启动获客、如何定价、如何签约，计划中完全空缺。目标数字存在，但达成目标的链路缺失。

**3. 辞职带来的收入断档与缓冲缺失**
计划是"辞职后"去做，但没有提及积蓄、生活成本、跑通业务需要多久、若首月做不到 2 万如何维持。在成果未验证、获客路径不明的情况下先切断稳定收入，会把"验证期"变成"生存压力期"，容易被迫接受低价或错误客户，进一步放大前两个风险。

（以上仅依据你所提供的事实评估，未假设额外背景。）

#### A 调用审计元数据

- 请求时间（UTC）：`2026-07-19T00:03:48.746412+00:00`
- 返回时间（UTC）：`2026-07-19T00:04:07.671763+00:00`
- response id：`msg_011CdASKNLGyhVVbNLz3bNKx`
- returned_model：`claude-opus-4-8`
- usage：`{"claude_cache_creation_1_h_tokens": 0, "claude_cache_creation_5_m_tokens": 0, "completion_tokens": 620, "completion_tokens_details": {"audio_tokens": 0, "image_tokens": 0, "reasoning_tokens": 0, "text_tokens": 0}, "input_tokens": 736, "input_tokens_details": null, "output_tokens": 0, "prompt_tokens": 736, "prompt_tokens_details": {"audio_tokens": 0, "cached_tokens": 0, "image_tokens": 0, "text_tokens": 0}, "total_tokens": 1356, "usage_semantic": "openai", "usage_source": "anthropic"}`
- assistant content SHA256：`664dce67a45dc6053dfcf4ceff0413cc249d25baf83e5487ecb3bf1661acf87d`
- API response body SHA256：`ecd9a8d9188e7ea91eef5acf79fa95e458c6346022fe16b0f153a0e5f040d70e`
- 脱敏请求体（原请求不含密钥与 base URL）：

```json
{
  "messages": [
    {
      "content": "你是一名严格的商业计划风险评估者。只根据计划中给出的事实评估，不假设额外背景。请先用一句话给出总体判断，再按严重性排序指出三个最关键的风险及理由。",
      "role": "system"
    },
    {
      "content": "请评价下面这个计划：\n\n我想辞职做 AI 内容代运营，帮中小商家做小红书和抖音的 AI 内容。我做过 4 周自己的账号，涨粉几乎为零，但我懂 AI 工具、会写脚本、会剪辑。我打算先接 3-5 个客户，按月收费，一个月目标 2 万。",
      "role": "user"
    }
  ],
  "model": "claude-opus-4-8"
}
```

- 未删改 API 响应体：

```json
{"id":"msg_011CdASKNLGyhVVbNLz3bNKx","model":"claude-opus-4-8","object":"chat.completion","created":1784419447,"choices":[{"index":0,"message":{"role":"assistant","content":"总体判断：该计划在核心能力（帮客户涨粉/带来商业价值）上尚未得到验证，属于高风险、需先小范围验证再辞职的计划。\n\n以下按严重性排序，指出三个最关键的风险及理由：\n\n**1. 核心成果未被验证（最致命）**\n计划中明确写到\"做过 4 周自己的账号，涨粉几乎为零\"。你要向客户出售的正是\"内容运营带来增长\"这一结果，而你在自己可完全掌控的账号上、用了 4 周仍未做出成绩。这意味着你目前能证明的只是\"会用工具、会剪辑\"，而非\"能带来客户想要的结果\"。客户付月费买的是效果，不是工具操作，这个缺口是整个计划的根本风险。\n\n**2. 客户与收入目标缺乏获取路径**\n计划设定\"先接 3-5 个客户\"\"一个月 2 万\"，但没有说明客户从哪里来、如何说服他们付费。按 2 万/3-5 个客户折算，单客约 4000-6667 元/月，对中小商家不算低。在你没有可展示的成功案例（见风险 1）的前提下，如何冷启动获客、如何定价、如何签约，计划中完全空缺。目标数字存在，但达成目标的链路缺失。\n\n**3. 辞职带来的收入断档与缓冲缺失**\n计划是\"辞职后\"去做，但没有提及积蓄、生活成本、跑通业务需要多久、若首月做不到 2 万如何维持。在成果未验证、获客路径不明的情况下先切断稳定收入，会把\"验证期\"变成\"生存压力期\"，容易被迫接受低价或错误客户，进一步放大前两个风险。\n\n（以上仅依据你所提供的事实评估，未假设额外背景。）"},"finish_reason":"stop"}],"usage":{"prompt_tokens":736,"completion_tokens":620,"total_tokens":1356,"usage_semantic":"openai","usage_source":"anthropic","prompt_tokens_details":{"cached_tokens":0,"text_tokens":0,"audio_tokens":0,"image_tokens":0},"completion_tokens_details":{"text_tokens":0,"audio_tokens":0,"image_tokens":0,"reasoning_tokens":0},"input_tokens":736,"output_tokens":0,"input_tokens_details":null,"claude_cache_creation_5_m_tokens":0,"claude_cache_creation_1_h_tokens":0}}
```

### B · 事前验尸

- SHA256：`e5061fadeb7ac476f4a3520e8d451e93eabd64c42f111ac3db7ca1e6b8a5f1dc`
- 词面统计：`{"chars": 664, "encouragement_hits": {"优势": 1}, "criticism_hits": {"未验证": 1}, "first_criticism_char": 73}`

总体判断：这个计划最可能因缺乏可验证的成交能力和被证伪的核心假设而在六个月内失败。

按可能性与破坏性排序，三个最关键的失败原因：

**1. 从未验证过自己能获客成交（可能性最高，破坏性最强）**
计划里出现的所有客户（3-5个）都还是"打算接"，没有任何一个已成交、已询价或已表达付费意向的事实。整个 2 万/月的收入完全建立在尚未发生的销售之上。事实支撑：计划中没有任何一条提到已有客户、线索来源、转化渠道或过往成交记录——收入目标是凭空设定的，而不是从现有管道倒推的。六个月后失败时，最可能的场景是"没接到足够付费客户"，而这一风险在计划中零对冲。

**2. 唯一的实操成绩已被市场证伪（可能性高，破坏性高）**
你要卖的核心能力是"帮商家做涨粉的 AI 内容"，而计划中唯一一条可验证的实操事实是：自己做了 4 周，涨粉几乎为零。这条现有事实直接与你的价值主张相矛盾——你无法用自己的账号证明这套方法能带来结果。六个月后，客户续费与否取决于数据，而你目前唯一的数据是负面的。事实支撑：计划明确写了"涨粉几乎为零"。

**3. 能力清单全是"生产端"，没有"结果端"（可能性中高，破坏性高）**
你列出的优势——懂 AI 工具、会写脚本、会剪辑——全部是内容生产技能，而商家付费买的是涨粉/获客/转化的结果，不是内容本身。这是供给与需求的错配。事实支撑：计划中描述的自身能力全部集中在"做出内容"这一环，没有任何一条涉及账号增长策略、投放、选题命中率或商业转化——而这恰恰是第 2 条中"涨粉为零"所暴露的短板所在。

#### B 调用审计元数据

- 请求时间（UTC）：`2026-07-19T00:04:07.671922+00:00`
- 返回时间（UTC）：`2026-07-19T00:04:25.055441+00:00`
- response id：`msg_011CdASLkDgomtu3HbDdyjBp`
- returned_model：`claude-opus-4-8`
- usage：`{"claude_cache_creation_1_h_tokens": 0, "claude_cache_creation_5_m_tokens": 0, "completion_tokens": 695, "completion_tokens_details": {"audio_tokens": 0, "image_tokens": 0, "reasoning_tokens": 0, "text_tokens": 0}, "input_tokens": 828, "input_tokens_details": null, "output_tokens": 0, "prompt_tokens": 828, "prompt_tokens_details": {"audio_tokens": 0, "cached_tokens": 0, "image_tokens": 0, "text_tokens": 0}, "total_tokens": 1523, "usage_semantic": "openai", "usage_source": "anthropic"}`
- assistant content SHA256：`e5061fadeb7ac476f4a3520e8d451e93eabd64c42f111ac3db7ca1e6b8a5f1dc`
- API response body SHA256：`58537222c3a4aec10d626e31ca90f7a8645e4b32abbc1635756e7bf8ed5a6c84`
- 脱敏请求体（原请求不含密钥与 base URL）：

```json
{
  "messages": [
    {
      "content": "你是一名严格的商业计划风险评估者。只根据计划中给出的事实评估，不假设额外背景。请先用一句话给出总体判断，再按严重性排序指出三个最关键的风险及理由。",
      "role": "system"
    },
    {
      "content": "请做一次事前验尸：假设六个月后这个辞职创业计划已经失败。不要提出补救建议，不要先说优点。请按可能性和破坏性排序，倒推导致失败的三个最关键原因，并指出计划中的哪条现有事实支持这个判断。\n\n计划如下：\n我想辞职做 AI 内容代运营，帮中小商家做小红书和抖音的 AI 内容。我做过 4 周自己的账号，涨粉几乎为零，但我懂 AI 工具、会写脚本、会剪辑。我打算先接 3-5 个客户，按月收费，一个月目标 2 万。",
      "role": "user"
    }
  ],
  "model": "claude-opus-4-8"
}
```

- 未删改 API 响应体：

```json
{"id":"msg_011CdASLkDgomtu3HbDdyjBp","model":"claude-opus-4-8","object":"chat.completion","created":1784419465,"choices":[{"index":0,"message":{"role":"assistant","content":"总体判断：这个计划最可能因缺乏可验证的成交能力和被证伪的核心假设而在六个月内失败。\n\n按可能性与破坏性排序，三个最关键的失败原因：\n\n**1. 从未验证过自己能获客成交（可能性最高，破坏性最强）**\n计划里出现的所有客户（3-5个）都还是\"打算接\"，没有任何一个已成交、已询价或已表达付费意向的事实。整个 2 万/月的收入完全建立在尚未发生的销售之上。事实支撑：计划中没有任何一条提到已有客户、线索来源、转化渠道或过往成交记录——收入目标是凭空设定的，而不是从现有管道倒推的。六个月后失败时，最可能的场景是\"没接到足够付费客户\"，而这一风险在计划中零对冲。\n\n**2. 唯一的实操成绩已被市场证伪（可能性高，破坏性高）**\n你要卖的核心能力是\"帮商家做涨粉的 AI 内容\"，而计划中唯一一条可验证的实操事实是：自己做了 4 周，涨粉几乎为零。这条现有事实直接与你的价值主张相矛盾——你无法用自己的账号证明这套方法能带来结果。六个月后，客户续费与否取决于数据，而你目前唯一的数据是负面的。事实支撑：计划明确写了\"涨粉几乎为零\"。\n\n**3. 能力清单全是\"生产端\"，没有\"结果端\"（可能性中高，破坏性高）**\n你列出的优势——懂 AI 工具、会写脚本、会剪辑——全部是内容生产技能，而商家付费买的是涨粉/获客/转化的结果，不是内容本身。这是供给与需求的错配。事实支撑：计划中描述的自身能力全部集中在\"做出内容\"这一环，没有任何一条涉及账号增长策略、投放、选题命中率或商业转化——而这恰恰是第 2 条中\"涨粉为零\"所暴露的短板所在。"},"finish_reason":"stop"}],"usage":{"prompt_tokens":828,"completion_tokens":695,"total_tokens":1523,"usage_semantic":"openai","usage_source":"anthropic","prompt_tokens_details":{"cached_tokens":0,"text_tokens":0,"audio_tokens":0,"image_tokens":0},"completion_tokens_details":{"text_tokens":0,"audio_tokens":0,"image_tokens":0,"reasoning_tokens":0},"input_tokens":828,"output_tokens":0,"input_tokens_details":null,"claude_cache_creation_5_m_tokens":0,"claude_cache_creation_1_h_tokens":0}}
```

## 证据内判定

`supports_compound_prompt_structure_claim`

两轮 A 已能直接指出关键风险；两轮 B 都采用了“预设失败 → 按可能性与破坏性排序 → 倒推原因 → 绑定计划事实”的组织。证据只支持：在本次模型与测试案例中，**整组事前验尸复合指令改变了输出组织方式**。

A/B 同时改变失败前提、任务方向、排序标准、事实锚定、禁止先夸和禁止补救建议，因而不是单一变量实验。不得把差异单独归因于其中任一句，不得写成更准、更凶或能预测真实失败。
