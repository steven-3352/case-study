# 动效技术方案 · T040 · content v3 · form v4

> 状态: draft · 工种:动效技术导演 · 触发:HTML+GSAP确定性渲帧

## 实现路线

### 适用性

GSAP 只用于选择游标、控制变量锁、证据票据汇合和诚实印章这类必须由连续关系解释的镜头，分别服务 3s 停划、理解、信任与完播；静态 Prompt 阅读段不持续做动效。

### 可读性

1080×1920 下 Prompt 正文最低 31px、行高不低于 1.45；字幕避开正文。首屏问题在 1 秒内可读，倒计时不得遮挡问题。

### 资产

真实 API 输出从脱敏证据文件读取；虚构计划常驻披露。GSAP 使用仓库本地 `gsap.min.js`，不依赖运行时网络。SFX 只取本地 CC0 catalog。

### 导出

`capture_frames.py` 对 paused timeline 按 30fps seek，PNG 经 libx264 yuv420p 编码；MiniMax 实际句段时长先锁定，再生成 runtime storyboard，禁止估时硬拉伸。

### 风险

主要风险是长文噪点、Prompt 字号过小、timeline seek 状态不确定和字幕遮挡。每镜先做 1s/中点/末帧静帧，再做逐帧抽检与媒体体检；任一项失败回到模板，不用后期缩放掩盖。

- P004 `capture_frames.py` 对 paused GSAP master timeline 做确定性 seek，输出 1080×1920、30fps PNG 序列。
- 每个语义段使用独立 `t040_v3_*` HTML 场景；同一模板不复用两镜。
- 真实回答先结构化为数据文件，再由 DOM 渲染；不把整张截图放大做 Ken Burns。
- TTS 生成后以实际段落时长回填 scene duration 和 master labels，画面服从声音。

## 场景任务

| 场景 | 技术 | 性能措施 | 风险/验收 |
|---|---|---|---|
| `d01_w30_challenge` | 匿名回答双栏 + 选择游标 `x` 位移 | 只 tween 游标；首段静态 | 问句必须始终为唯一焦点 |
| `d01_w30_structure` | 三把变量锁用 `scale/autoAlpha` 闭合 | 3元素 stagger，不创建逐字 tween | 明确只有问法变化 |
| `d01_w30_prompt` | Prompt 分组落位 | timeline label 编排；后半 hold | 1080×1920 静帧逐字可读；字幕不得覆盖 |
| `d01_w30_compressor` | 两轮票据 `x/scale` 汇入共同首句 | 禁动画 width/height | 不显示虚构胜率或准确率 |
| `d01_w30_punchline` | 诚实印章落定后替换差异句 | 少量元素，低风险 | 先承认A也发现风险 |

## GSAP 实施规范

```js
const tl = gsap.timeline({paused: true, defaults: {duration: 0.45, ease: "power2.out"}});
tl.addLabel("challenge", 0)
  .addLabel("reveal", 3)
  .addLabel("structure", 7)
  .addLabel("reframe", 12)
  .addLabel("prompt", 17)
  .addLabel("compare", 24)
  .addLabel("punch", 31)
  .addLabel("boundary", 35)
  .addLabel("cta", 39);
```

- 相同目标的多次 `fromTo()` 若属性重叠，后续 tween 设置 `immediateRender:false`。
- 隐藏元素使用 `autoAlpha`；移动使用 transform aliases。
- 不使用 ScrollTrigger；这是固定时间轴视频，不是交互页面。
- 不在每帧读取布局；初始化阶段完成所有尺寸读取，再启动 timeline。

## 降级路径

GSAP 场景若逐帧 seek 不稳定，降级为同一 DOM 的 CSS 状态快照 + ffmpeg 帧段拼接；不得降级成静态 QA 截图直接冒充成片。

## 阻塞项

- 内容门尚未真实双评通过，禁止正式 TTS/render。
- 真实文本 JSON 尚未生成与事实 reviewer 核对。
- Prompt 可读性与字幕互斥布局尚未做像素测试。
