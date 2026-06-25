# P002 · 视觉脚本（6 张分镜 · 9:16 报纸风）

> 画布：1080 × 1920
> 主色：底 `#F5F0E6` · 油墨黑 `#1A1A1A` · 警示红 `#D03028` · 高亮黄 `#F4D35E`
> 字体：标题 思源宋体 Heavy · 正文 方正报宋 · 报头英文 Playfair Display
> 印章字体：方正魏碑（红 `#D03028`，旋转 -12°）
> 报纸纹理：米黄底 + 5% 噪点 + 仿网点印刷 halftone

---

## 通用元素

每张图固定模块（沿用 1f18fcf 基线）：

```
┌──────────────────────────────────┐
│ THE OVERTIME TIMES               │ ← 报头条（顶部 96px）
│ 2026/06/18 · 第 4748 期           │
├──────────────────────────────────┤
│ [栏目条 · 红底白字 64px]            │ ← 不同分镜不同
├──────────────────────────────────┤
│                                  │
│  [主标题]                         │ ← 黑色衬线大字
│  [副标题]                         │
│                                  │
│  ┌──────────┐  ┌──────────┐      │ ← 主图 + 道具 双栏
│  │ 人物插画  │  │ 道具截图  │      │
│  └──────────┘  └──────────┘      │
│                                  │
│  [狗仔正文 · 报宋 36px]            │
│                                  │
├──────────────────────────────────┤
│ [底部钩子条 · 黄底黑字]            │ ← 最后 120px
└──────────────────────────────────┘
                              [印章] ← 右下角红章 -12°
```

---

## P1 · 封面 头版头条

**画面构图**：
- 顶部 1/4：报头 + 主标题（标题字号 120px 占满宽度）
- 中部 1/2：**五人合影插画**（横排站位，每人手举名牌 NO.1 - NO.5）
- 底部 1/4：副标题红字 + 导语 + 底部钩子条
- 装饰：右上角叠 3 枚印章「独家」「头版」「号外」

**主图 prompt**（合影）：
```
tabloid newspaper illustration, five characters lined up like a police lineup,
each holding a name placard with red number 1 to 5,
left to right: shy nerdy man in white shirt and round glasses,
sophisticated woman in black tailored suit with luxury bag,
mysterious man in black hoodie and cap with hidden face,
woman in cheap copy version of the suit looking embarrassed,
young silicon valley guy in grey hoodie and airpods,
vintage halftone print, ink stipple shading,
slightly desaturated, 1990s gossip magazine cover, group portrait
```

**右下角印章**：「号外」红印 -12°

---

## P2 · 第1任 柯学长（GitHub Copilot）

**画面构图**：
- 栏目条：黑底白字 `情感专栏 · 第 1 任前任 · 2021.10 - 2023.03`
- 标题：黑色衬线 96px
- 左 2/3：柯学长半身插画 + 头顶对话气泡「你是不是想写...这个？」
- 右 1/3：仿 VSCode 灰底截图（小 C 写一半 + 灰字补全）
- 正文：双栏报宋 36px
- 右下角分手原因栏 + 已分手印章

**主图 prompt**：
```
tabloid illustration of a shy young man in his early 20s,
white button-up shirt, round wire-rimmed glasses, slight stoop,
standing slightly behind a desk looking down at a laptop keyboard,
gentle but passive expression, sad puppy eyes,
vintage halftone print, ink stipple shading, slightly desaturated,
1990s gossip magazine portrait, full body 3/4 view
```

**道具图（伪 VSCode 截图）**：
```
深灰底 #1E1E1E
行号灰字
function getUserName() {
  return user.| ← 光标
            name  ← 灰色补全
}
```

**对话气泡**（黄底黑字）：
> 你是不是想写...这个？

**右下角印章**：「已分手」血红 -12°

---

## P3 · 第2任 顾小姐（Cursor）

**画面构图**：
- 栏目条：红底白字 `金融版 · 第 2 任前任 · 2023.03 - 2025.02`
- 左 1/2：顾小姐全身插画（黑高定，端美式，挎香奈儿）
- 右 1/2：账单墙——6 张伪造的 Cursor Pro Bill 收据斜贴，金额从 $20 → $200
- 正文：单栏报宋 38px
- 右下角分手原因栏 + 钱包警告印章

**主图 prompt**：
```
tabloid illustration of a sophisticated career woman in her late 20s,
black tailored business suit, designer handbag draped on arm,
holding americano coffee cup, confident smirk, slight head tilt,
sleek bob haircut, gold earrings, expensive watch,
vintage halftone print, ink stipple shading, slightly desaturated,
1990s gossip magazine glamour shot, full body portrait
```

**道具图（账单墙）**：
- 6 张白色账单（带红色 "PAID" 印章）斜贴堆叠
- 金额递增：$20 → $40 → $60 → $100 → $150 → $200
- 标题 "Pro Subscription · 顾氏家族会所"

**右下角印章**：「钱包警告」血红 -12°

---

## P4 · 第3任 K 先生（Claude Code）

**画面构图**：
- 栏目条：黑底白字 `社会版 · 第 3 任（出轨对象） · 2025.02 至今 · 仍在交往`
- 左 1/2：K 先生侧影插画（黑卫衣鸭舌帽，只见手在键盘上，脸隐于阴影）
- 右 1/2：**巨大终端截图**（黑底）显示 `> 让我想想...（thinking 47s）`
- 正文：单栏报宋 38px
- 右下角恋爱亮点栏 + 深夜密会印章

**主图 prompt**：
```
tabloid illustration of a mysterious man in dark hoodie and baseball cap,
only side silhouette visible, face hidden in deep shadow,
muscular hands typing on mechanical keyboard,
single warm desk lamp lighting from the side,
vintage halftone print, ink stipple shading,
noir film aesthetic, paparazzi candid shot from behind,
1990s gossip magazine, dark moody atmosphere
```

**道具图（终端截图）**：
```
黑底 #0A0A0A
绿字 monospace #6BFF6B
$ claude
> Analyzing your codebase...
> Found 47 issues
> 让我想想... (thinking 47s)
                                    ▌ ← 光标闪烁
$ ▌
```

**右下角印章**：「深夜密会」血红 -12°

---

## P5 · 第4任 温小妹（Windsurf）

**画面构图**：
- 栏目条：粉底白字 `娱乐版 · 第 4 任前任 · 2025.03 - 2025.04`
- 上 1/2：温小妹和顾小姐**并排站立撞衫**插画（左姐姐右妹妹，明显是高仿）
- 下 1/2：网友锐评弹幕墙（5-6 条仿微博热评截图）
- 右下角分手原因栏 + 山寨预警印章

**主图 prompt**：
```
tabloid illustration of two women standing awkwardly side by side,
both wearing nearly identical black business suits but one is cheaper looking,
left woman is the original elegant version with designer accessories,
right woman is a cheap knockoff version looking embarrassed,
side by side comparison shot, both turning toward each other,
vintage halftone print, ink stipple shading,
paparazzi caught moment, 1990s gossip magazine,
embarrassed and awkward expressions
```

**弹幕墙文案**（仿微博热评卡片）：
- 「姐妹？分明是高仿包啊」
- 「买不起顾姐才选她吧（doge）」
- 「前 7 天免费，第 8 天破防」
- 「同款穿搭笑死，灵魂是义乌的吗」
- 「撞脸不可怕，撞性格还便宜🤣」
- 「她妈是 Cursor 他爸是 VSCode？」

**右下角印章**：「山寨预警」血红 -12°

---

## P6 · 第5任 C 少爷 + 开放结局

**画面构图**：
- 栏目条：红底白字 `头版连载 · 最新进展 · 2025.04 至今 · 关系待定`
- 上 1/3：C 少爷 + 小 C 牵手剪影（C 少爷正脸笑容，小 C 眼神飘走）
- 中 1/3：**4 张通缉令排队墙**（G 公子 / 崔少 / 灵码姐 / K 小哥）每张盖红章 NEXT?
- 下 1/3：评论员锐评 + 互动话题 + CTA 黄色条

**主图 prompt（C 少爷牵手）**：
```
tabloid illustration of a young silicon valley tech bro in grey zip hoodie,
white airpods pro, holding hands with a tired exhausted programmer,
the programmer's eyes wandering toward the distance with conflicted look,
the silicon valley guy smiling proudly facing forward,
vintage halftone print, ink stipple shading,
paparazzi candid shot, 1990s gossip magazine, awkward couple
```

**通缉令墙**（4 张并排，仿西部通缉令风格）：
- 海报标题：`WANTED · 下一任候选人`
- 每张配剪影 + 名字 + "BOUNTY ¥??"
- 全部盖红章「NEXT?」

**底部黄色 CTA 条**（高 160px）：
```
👇 点赞 + 收藏 + 评论你最爱的一任 · 本报记者抽 3 位送神秘小礼物
```

**右下角印章**：「海王无敌」血红 -12°

---

## 印章库（统一规格）

| 印章文字 | 用途 | 颜色 | 旋转 |
|---|---|---|---|
| 独家 | P1 右上 | 红 | -10° |
| 头版 | P1 右上 | 红 | +8° |
| 号外 | P1 右下 | 红 | -12° |
| 已分手 | P2 右下 | 血红 | -12° |
| 钱包警告 | P3 右下 | 血红 | -8° |
| 深夜密会 | P4 右下 | 血红 | -15° |
| 山寨预警 | P5 右下 | 血红 | -10° |
| 海王无敌 | P6 右下 | 血红 | -12° |
| NEXT? | P6 通缉令 ×4 | 红 | 各异 |

---

## 待补素材清单

- [ ] 5 个角色定妆插画（按上面 prompts 用 Midjourney / Flux 生成）
- [ ] 仿 VSCode 灰底代码截图
- [ ] 6 张账单墙（Photoshop 拼贴或代码生成）
- [ ] 终端 thinking 截图
- [ ] 弹幕墙 6 条
- [ ] 通缉令 4 张
- [ ] 印章 PNG（透明底）
