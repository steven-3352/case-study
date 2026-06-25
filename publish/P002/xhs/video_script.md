# P002 · 小红书视频脚本（35 秒）

> 输出：1080 × 1920 · 30fps · MP4 H.264
> 实现：HTML + GSAP timeline → Playwright 录屏 → FFmpeg 合 BGM
> 文件：`video/index.html`（动画源）· `video/README.md`（录屏指南）
> 风格：纯字幕 + 音效，无旁白；BGM 卡每场切换节奏点

---

## 总时长结构（35 秒）

| 段落 | 时间 | 时长 | 内容 | 转场出 |
|---|---|---|---|---|
| 开场 stinger | 00:00 - 00:01 | 1s | 报头闪现 + 标题打字 | 报纸翻页 |
| P1 封面 | 00:01 - 00:06 | 5s | 五人列队 + 红章砸落 | 翻页 |
| P2 柯学长 | 00:06 - 00:11 | 5s | 滑入 + 对话气泡 + 印章 | 翻页 |
| P3 顾小姐 | 00:11 - 00:17 | 6s | 账单堆叠跳数字 + 印章 | 翻页 |
| P4 K 先生 | 00:17 - 00:23 | 6s | thinking 倒计时 + 终端打字 | 翻页 |
| P5 温小妹 | 00:23 - 00:28 | 5s | 撞衫 zoom + 弹幕飘 + 印章 | 翻页 |
| P6 收尾 | 00:28 - 00:35 | 7s | 4 张通缉令排队 + CTA 钩子定格 | 卡停 1s |

---

## BGM 选择

**推荐**（按情绪强度排序）：
1. **Daft Punk - One More Time**（开场强节拍，120 BPM）
2. **Lipps Inc - Funkytown**（迪斯科欢快，108 BPM）
3. **Anggun - Snow on the Sahara Remix**（异域电子）
4. **Pump It - Black Eyed Peas**（高能 ×）适合中段加速
5. 抖音热门《Cha Cha》Remix 版（卡点神器）

**节奏点对齐**：每张图切换对应 BGM 的 downbeat（鼓点），用 Audacity 看波形定位精确帧。

**音量曲线**：
- 00:00 入场淡入到 -8dB
- 00:28 收尾段落降到 -14dB 突出 CTA 字幕
- 00:34 最后一帧 1s 内淡出至 -∞

---

## 音效清单（点缀）

| 时间 | 音效 | 用途 |
|---|---|---|
| 00:00 | 报纸翻页 "swoosh" | 开场 |
| 00:05 | 印章砸落 "thud" | P1 红章砸落 |
| 00:06 / 00:11 / 00:17 / 00:23 / 00:28 | 翻页 "page-turn" | 每场转场 |
| 00:14 | 钱袋掉金币 "coin-drop" | P3 账单出现 |
| 00:19 | 机械键盘 "click clack" | P4 thinking |
| 00:22 | 倒计时滴答 "tick" ×3 | P4 thinking 47s |
| 00:25 | 微博通知 "ding" ×3 | P5 弹幕飞入 |
| 00:34 | 报纸合上 "thunk" | 结尾定格 |

**音效来源**：freesound.org / zapsplat.com / pixabay sounds（CC0）

---

## 详细分镜动画时间线

### 00:00 - 00:01 ｜ 开场 stinger

```
gsap.timeline()
  .from(".paper-edge", { x: -1080, duration: 0.4, ease: "power3.out" })
  .from(".headline-char", { y: 200, opacity: 0, stagger: 0.02, duration: 0.4 })
  .to(".paper-bg", { filter: "brightness(1)", duration: 0.2 });
```

**音效**：报纸翻页 swoosh
**视觉**：报头从左滑入 → 主标题打字机入场（SplitText 拆字）

---

### 00:01 - 00:06 ｜ P1 封面

**入场顺序**（0.6s 内完成）：
1. 报头已在位
2. 主标题"惊！" `scale(0) → scale(1.2) → scale(1)` 弹性回弹 0.3s
3. 主标题剩余文字打字机入场 0.4s
4. 五人剪影从底部依次升起 `stagger 0.1s`
5. 每人胸前印章 NO.1-5 `rotate(-30°) → rotate(0°)` 砸落
6. 副标题红字"码农情感档案"从左滑入
7. 右上角「独家」「头版」印章砸落（音效 thud ×2）

**停留**：3.5s
**出场**：整页 `x: -1080, duration: 0.4`（翻页效果）

```javascript
const tl_p1 = gsap.timeline({ defaults: { ease: "power3.out" } });
tl_p1
  .from(".p1-headline", { scale: 0, duration: 0.3, ease: "back.out(1.7)" })
  .from(".p1-character", { y: 1200, opacity: 0, stagger: 0.1, duration: 0.5 })
  .from(".p1-stamp", { scale: 3, rotation: -90, opacity: 0,
                        stagger: 0.1, duration: 0.3, ease: "back.out(2)" })
  .from(".p1-subtitle", { x: -200, opacity: 0, duration: 0.4 })
  .from(".p1-corner-stamp", { scale: 5, opacity: 0,
                                stagger: 0.15, duration: 0.3, ease: "back.out(2.5)" });
```

**字幕条**（底部）："5 年 · 5 个对象 · 5 颗破碎的心"

---

### 00:06 - 00:11 ｜ P2 柯学长

**入场**：
1. 旧页面 `x: -1080` 滑出（0.3s）
2. 新页面 `x: 1080 → 0` 滑入
3. 柯学长插画从右滑入并轻微抖动（紧张感）
4. 头顶对话气泡"你是不是想写...这个？" 0.6s 后冒出（弹性）
5. 仿 VSCode 截图从右淡入，灰字补全部分用 SplitText 逐字打出
6. 正文逐段淡入
7. 右下「已分手」红章砸落（音效 thud）

```javascript
tl_p2
  .from(".p2-character", { x: 800, duration: 0.5, ease: "back.out(1.2)" })
  .from(".p2-bubble", { scale: 0, duration: 0.4, ease: "elastic.out(1, 0.5)" }, "-=0.2")
  .from(".p2-vscode", { opacity: 0, y: 50, duration: 0.4 })
  .from(".p2-vscode-completion", { opacity: 0, duration: 0.5, ease: "none" })  // 打字效果
  .from(".p2-stamp", { scale: 4, rotation: -180, opacity: 0,
                        duration: 0.4, ease: "back.out(2)" });
```

**字幕条**："初恋 · 柯学长 · 三年暧昧没说过一句完整的话"

---

### 00:11 - 00:17 ｜ P3 顾小姐

**入场**：
1. 翻页转场（0.3s）
2. 顾小姐插画从左滑入（优雅 ease）
3. **金额跳数字动画**：右侧账单墙 6 张依次浮现，每张金额从 $0 跳到目标数（GSAP `endRollupNumber`）
4. 6 张账单最后堆成一摞，红色"PAID"印章砸落每张
5. 累计金额 `$4,840` 大字跳出（音效：coin-drop ×6）
6. 右下「钱包警告」红章砸落

```javascript
tl_p3
  .from(".p3-character", { x: -800, duration: 0.5, ease: "power2.out" })
  .from(".p3-bill", { y: 200, opacity: 0, stagger: 0.15, duration: 0.3 })
  .to(".p3-bill-amount", {
    textContent: (i) => `$${[20, 40, 60, 100, 150, 200][i]}`,
    duration: 0.4, snap: { textContent: 1 },
    stagger: 0.15, ease: "power1.out"
  })
  .from(".p3-total", { scale: 0, duration: 0.4, ease: "back.out(2)" })
  .from(".p3-stamp", { scale: 4, rotation: -180, opacity: 0,
                        duration: 0.4, ease: "back.out(2)" });
```

**字幕条**："正牌 · 顾小姐 · 22 个月榨干 $4,840"

---

### 00:17 - 00:23 ｜ P4 K 先生

**入场**：
1. 翻页转场（0.3s）
2. 整页变深色（背景从米黄过渡到深灰）—— 营造深夜密会感
3. K 先生侧影从右淡入（鸭舌帽下脸隐于阴影）
4. 终端黑屏从左占据右半边
5. **核心动画**：`> 让我想想...` 打字机入场，然后 `(thinking ` + 数字从 0 跳到 47 + `s)` 完成
6. 47 秒倒计时期间，键盘音效 click clack 循环 1s
7. `重构完成` 绿字闪烁
8. 右下「深夜密会」血红章砸落

```javascript
tl_p4
  .to(".paper-bg", { backgroundColor: "#2A2620", duration: 0.4 })
  .from(".p4-character", { x: 800, opacity: 0, duration: 0.5 })
  .from(".p4-terminal", { x: -400, opacity: 0, duration: 0.4 })
  .to(".p4-thinking-text", { text: "> 让我想想...", duration: 0.6, ease: "none" })
  .to(".p4-thinking-counter", {
    textContent: 47, duration: 1.0,
    snap: { textContent: 1 }, ease: "power1.in"
  })
  .from(".p4-done", { opacity: 0, duration: 0.3,
                       repeat: 3, yoyo: true })
  .from(".p4-stamp", { scale: 4, rotation: -180, opacity: 0,
                        duration: 0.4, ease: "back.out(2)" });
```

**字幕条**："出轨对象 · K 先生 · 47 秒重构半年烂代码"

---

### 00:23 - 00:28 ｜ P5 温小妹

**入场**：
1. 翻页转场（背景恢复米黄）
2. 顾小姐 + 温小妹**并排剪影**先以 `scale 0` 弹入
3. 撞衫尴尬画面 zoom in，左右两人之间画对比红框（"撞衫"高亮）
4. 6 条网友锐评弹幕从右往左飘过（stagger）
5. 右下「山寨预警」红章砸落

```javascript
tl_p5
  .to(".paper-bg", { backgroundColor: "#F5F0E6", duration: 0.3 })
  .from(".p5-duo", { scale: 0, duration: 0.5, ease: "back.out(1.5)" })
  .from(".p5-compare-frame", { opacity: 0, scale: 1.5, duration: 0.4 })
  .from(".p5-danmaku", {
    x: 1080, opacity: 0,
    stagger: 0.12, duration: 0.4, ease: "power2.out"
  })
  .from(".p5-stamp", { scale: 4, rotation: -180, opacity: 0,
                        duration: 0.4, ease: "back.out(2)" });
```

**字幕条**："山寨备胎 · 温小妹 · 撞脸还撞性格，灵魂义乌批发"

---

### 00:28 - 00:35 ｜ P6 收尾

**入场**（最华彩段落 7s）：
1. 翻页转场
2. 上部 C 少爷+小 C 牵手画面淡入
3. 小 C 眼神**慢速向左飘**（GSAP 控制眼球 SVG `cx` 偏移）—— 关键搞笑点
4. 中部 4 张通缉令**依次从底部冒出**（NEXT? 印章砸落每张）
5. 评论员锐评打字机入场："海王不是病，是这届打工人的求生本能。"
6. 互动话题 "你的初恋是谁？" 红字闪烁
7. 底部黄色 CTA 条从底部弹出
8. 最后 1 秒卡停，所有元素微微呼吸（pulse）

```javascript
tl_p6
  .from(".p6-couple", { opacity: 0, duration: 0.4 })
  .to(".p6-xc-eye", { cx: "-=30", duration: 0.6, ease: "power1.inOut",
                       repeat: -1, yoyo: true })  // 眼神飘
  .from(".p6-wanted", {
    y: 400, opacity: 0,
    stagger: 0.18, duration: 0.4, ease: "back.out(1.5)"
  })
  .from(".p6-next-stamp", {
    scale: 4, rotation: -180, opacity: 0,
    stagger: 0.18, duration: 0.3, ease: "back.out(2)"
  }, "<")  // 与 wanted 同时
  .to(".p6-comment", { text: "海王不是病，是这届打工人的求生本能。",
                        duration: 1.2, ease: "none" })
  .from(".p6-cta", { y: 200, duration: 0.4, ease: "back.out(1.5)" })
  .to(".p6-hook", { opacity: 0.3, duration: 0.4,
                     repeat: 3, yoyo: true });  // 钩子闪烁
```

**字幕条**：（无新字幕，让画面说话）

**最后一帧定格**：所有元素停留，CTA 黄色条 + "你的初恋是谁？" + 4 张通缉令

---

## 字幕条样式（统一）

```css
.subtitle-bar {
  position: absolute;
  bottom: 80px;
  left: 0; right: 0;
  height: 120px;
  background: rgba(244, 211, 94, 0.95);  /* 高亮黄 */
  color: #1A1A1A;
  font-family: "方正报宋", serif;
  font-size: 56px;
  font-weight: 900;
  text-align: center;
  line-height: 120px;
  border-top: 4px solid #1A1A1A;
  border-bottom: 4px solid #1A1A1A;
}
```

每段字幕 fade in 0.3s + 停留 + fade out 0.3s。

---

## 录制参数

| 参数 | 值 |
|---|---|
| 分辨率 | 1080 × 1920 |
| 帧率 | 30 fps |
| 编码 | H.264 (libx264) |
| 比特率 | 8 Mbps |
| 音频 | AAC 192 kbps 立体声 |
| 容器 | MP4 |
| 文件名 | `P002_xhs_video.mp4` |

详见 `video/README.md` 录制操作步骤。
