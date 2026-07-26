---
name: feedback-yishuzi-term
description: "paperdoll 海报排版层的正确术语是「艺术字」,不是「美术字」;且艺术字不含 AI 味/廉价贬义"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: c1075b53-4425-4e4d-ab2a-ebd66cd0f73e
---

paperdoll-mv-packaging 里那套「为标题/主视觉设计过的字形 + 海报级层级排版」层,正确叫**艺术字**,不是「美术字」。

**Why:** 用户在一轮对话里连续纠正三次。我起初用「美术字」,被纠正后又反过来给用户讲「美术字 vs 艺术字」的定义表、还把「艺术字」污名化成 Office WordArt 廉价特效——这是错的。用户明确说「艺术字跟 AI 味没有关系」。艺术字就是这套系统该用的中性术语,不承载任何廉价/反 AI 味的贬义。

**How to apply:**
- 涉及 `pipeline/paperdoll/poster.py` 这套 display-typography / 海报排版层时,一律写「艺术字」。
- 不要再给这个词加「≠ WordArt」「会显廉价」一类价值判断的旁注。
- 更一般的:用户明确指定术语时直接采用,不要用定义表把术语「argue back」给用户。相关 [[feedback-gate-floor-not-target]] 之外,这是纯术语口径。
- 反廉价特效的立论(渐变+外发光+投影+描边四件套显廉价)仍然成立,但那是**对特效手法**的判断,不要挂到「艺术字」这个词上。
