# P002 · 角色生图 Prompt 集

> 用于 Midjourney / Flux / DALL-E 3 / Stable Diffusion XL
> 统一风格基线：1990 年代八卦报纸插画 + 仿网点印刷 halftone + 微脱色
> 所有角色横构图 portrait，背景留白便于后期抠图叠加报纸版面

---

## 风格统一前缀（所有 prompt 必带）

```
tabloid newspaper illustration, vintage halftone print,
ink stipple shading, slightly desaturated, sepia tone,
1990s gossip magazine aesthetic, character portrait,
white background, --ar 3:4 --style raw
```

---

## 1. 柯学长（GitHub Copilot 拟人）

**人设关键词**：温柔学长 · 文静理工男 · 被动 · 永远在背后

```
tabloid newspaper illustration of a shy young asian man, age 22,
white button-up shirt slightly oversized, round wire-rimmed glasses,
soft sad puppy eyes, gentle smile, slight stoop posture,
standing slightly behind looking down at a laptop keyboard,
short black hair side-parted neatly, no confidence in his eyes,
vintage halftone print, ink stipple shading, slightly desaturated,
1990s gossip magazine portrait, full body 3/4 view, white background
--ar 3:4 --style raw
```

**Negative**：bold confident expression, muscular, dark clothing

---

## 2. 顾小姐（Cursor 拟人）

**人设关键词**：全能女友 · 金融街精英 · 越用越贵

```
tabloid newspaper illustration of a sophisticated career woman, age 28,
black tailored business suit, designer luxury handbag draped on arm,
holding americano coffee cup, confident smirk, slight head tilt,
sleek bob haircut, gold earrings, expensive watch, red lipstick,
vintage halftone print, ink stipple shading, slightly desaturated,
1990s gossip magazine glamour shot, full body portrait, white background
--ar 3:4 --style raw
```

**Negative**：cheap clothing, casual, smiling sweetly

---

## 3. K 先生（Claude Code 拟人）

**人设关键词**：终端老炮 · 黑客 · 不露脸 · 硬核

```
tabloid newspaper illustration of a mysterious man, age 30s,
dark hoodie and black baseball cap pulled low,
only side silhouette visible, face completely hidden in deep shadow,
muscular forearms exposed, hands typing on mechanical keyboard,
single warm desk lamp lighting from the side casting dramatic shadows,
vintage halftone print, ink stipple shading,
noir film aesthetic, paparazzi candid shot from behind,
1990s gossip magazine, dark moody atmosphere, white background
--ar 3:4 --style raw
```

**Negative**：face visible, bright lighting, smiling

---

## 4. 温小妹（Windsurf 拟人）

**人设关键词**：山寨备胎 · 平价复刻 · 撞衫尴尬

```
tabloid newspaper illustration of a young woman, age 24,
wearing nearly identical black business suit to Cursor woman,
but visibly cheaper looking version, fast-fashion knockoff quality,
generic plastic handbag instead of designer, drugstore lipstick,
embarrassed awkward smile, eyes glancing sideways nervously,
trying to look sophisticated but obviously trying too hard,
vintage halftone print, ink stipple shading, slightly desaturated,
1990s gossip magazine portrait, full body, white background
--ar 3:4 --style raw
```

**Negative**：confident, expensive luxury, original

---

## 5. C 少爷（Codex CLI 拟人）

**人设关键词**：硅谷归来 · 嫡子 · 英文混杂 · 自信

```
tabloid newspaper illustration of a young silicon valley tech bro, age 26,
grey zip-up hoodie over a startup t-shirt, white airpods pro in ears,
slightly tan from california sun, smug confident smile,
holding a sleek laptop under one arm, gesturing with the other hand,
short curly hair, casual but expensive sneakers visible,
vintage halftone print, ink stipple shading, slightly desaturated,
1990s gossip magazine portrait, full body 3/4 view, white background
--ar 3:4 --style raw
```

**Negative**：formal suit, traditional, asian features dominant

---

## 6. 小 C（主角 · 苦逼码农 · 第一人称视角）

**人设关键词**：35 岁码农 · 黑眼圈 · 加班永动机 · 当事人

```
tabloid newspaper illustration of a tired exhausted male programmer, age 35,
dark circles under eyes, messy hair, faded company hoodie,
slumped on the curb of a sidewalk outside a tech office building,
empty coffee cup beside him, defeated expression,
laptop on his lap glowing with code, mid-night urban scene,
vintage halftone print, ink stipple shading, slightly desaturated,
1990s gossip magazine paparazzi candid shot, full body, white background
--ar 3:4 --style raw
```

---

## 合影（P1 封面用）

```
tabloid newspaper group illustration, five characters lined up
like a police lineup against a height chart wall,
each holding a numbered placard from 1 to 5,
order left to right:
1) shy nerdy young man in white shirt and round glasses,
2) sophisticated woman in black tailored suit holding coffee,
3) mysterious tall man in black hoodie with hidden face,
4) younger woman in cheap copycat version of the suit,
5) silicon valley tech bro in grey hoodie and airpods,
vintage halftone print, ink stipple shading, slightly desaturated,
1990s gossip magazine cover, wide group shot, slight perspective,
police mugshot lighting from above
--ar 9:16 --style raw
```

---

## 牵手图（P6 用）

```
tabloid newspaper illustration of a tech bro in grey hoodie and airpods
holding hands with an exhausted programmer in faded company hoodie,
the tech bro smiles proudly facing the camera,
the programmer's tired eyes wander to the distance with conflicted longing look,
side by side standing pose, hands clearly visible holding,
vintage halftone print, ink stipple shading, slightly desaturated,
paparazzi candid shot, 1990s gossip magazine, awkward couple
--ar 3:4 --style raw
```

---

## 通缉令剪影（P6 ×4）

每张独立生成，统一构图：

```
old west wanted poster style, full body silhouette,
"WANTED · DEAD OR ALIVE · 下一任候选人" header,
black silhouette of [character] on weathered cream paper,
red wax stamp "NEXT?" overlaid at angle,
parchment texture, slightly torn edges, ink stains,
--ar 3:4 --style raw
```

替换 `[character]` 为：
1. 高大端庄商务男（Google · G 公子）
2. 中国年轻 hipster 男（字节 · 崔少）
3. 中国职场御姐（阿里 · 灵码姐）
4. 极简主义开源极客（K 小哥）

---

## 道具生图

**仿 VSCode 截图**（P2）：用 Carbon (carbon.now.sh) 直接代码截图
**仿账单墙**（P3）：用 Figma 拼 6 张账单，PSD 斜叠
**仿终端 thinking**（P4）：直接录屏 Claude Code 真实输出 / 用 asciinema
**仿微博弹幕墙**（P5）：用 sharerec / pictext 生成评论卡片
**通缉令**（P6）：上述 prompt 生成 4 张

---

## 印章 PNG（统一规格 800×800 透明底）

每枚印章 prompt：

```
red wax stamp impression on white background,
chinese calligraphy "[文字]" in 方正魏碑 style,
slightly faded ink texture, rotated -12 degrees,
transparent PNG, no shadow, isolated object
--ar 1:1 --style raw
```

替换 `[文字]`：独家 / 头版 / 号外 / 已分手 / 钱包警告 / 深夜密会 / 山寨预警 / 海王无敌 / NEXT?
