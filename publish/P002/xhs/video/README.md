# 把 HTML 动画录成小红书视频 · 操作指南

## 一、本地预览动画

```bash
# 启动本地静态服务（任选其一）
cd /Users/wmzuo/Documents/project/case-study/publish/P002/xhs/video
python3 -m http.server 8765
# 或
npx serve .
```

浏览器打开 `http://localhost:8765/index.html`，点 `▶ Play` 按钮看动画（35 秒）。

> 调试用 `?autoplay=1` 或直接打开把 `index.html` 最后一行 `// master.play();` 取消注释。

---

## 二、录屏方案三选一

### 方案 A · Playwright 无头录屏（**推荐**，可复现）

最干净、最自动化、画质最稳定。

```bash
# 安装
pip install playwright
playwright install chromium

# 录制脚本
cat > record.py << 'EOF'
import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            args=["--disable-web-security", "--allow-file-access-from-files"]
        )
        context = await browser.new_context(
            viewport={"width": 1080, "height": 1920},
            device_scale_factor=1,
            record_video_dir="./recording",
            record_video_size={"width": 1080, "height": 1920},
        )
        page = await context.new_page()
        await page.goto("http://localhost:8765/index.html")
        # 等待字体和 GSAP 加载
        await page.wait_for_timeout(1500)
        # 触发播放
        await page.evaluate("master.play()")
        # 等动画完成（35s + 缓冲）
        await page.wait_for_timeout(36000)
        await context.close()
        await browser.close()

asyncio.run(main())
EOF

python3 record.py
# 输出在 ./recording/*.webm
```

转 MP4：

```bash
ffmpeg -i recording/*.webm \
  -c:v libx264 -preset slow -crf 18 \
  -pix_fmt yuv420p -r 30 \
  -movflags +faststart \
  P002_xhs_raw.mp4
```

---

### 方案 B · macOS 自带 QuickTime 录屏

手动但简单。

1. 浏览器全屏打开 `index.html`，进入演示模式
2. `QuickTime Player → 文件 → 新建屏幕录制 → 选择窗口`
3. 点 `▶ Play` 按钮，等动画跑完按停止
4. 导出为 1080p MP4

> 缺点：分辨率受屏幕物理像素影响，需要后期裁切为 1080×1920。

---

### 方案 C · OBS Studio 录屏

适合需要边录边监看的场景。

1. OBS → 来源 → 浏览器源 → 输入 `http://localhost:8765/index.html`，宽 1080 高 1920
2. 输出设置：
   - 编码 x264
   - CBR 8000 Kbps
   - 关键帧 60
   - 帧率 30
3. 点开始录制，浏览器点 `▶ Play`，35 秒后停止

---

## 三、合 BGM + 音效（FFmpeg）

```bash
# 假设：
#   P002_xhs_raw.mp4   ← 录屏出来的视频（无声）
#   bgm.mp3            ← 选好的背景音乐
#   sfx_stamp.wav      ← 印章砸落音效
#   sfx_page.wav       ← 翻页音效
#   sfx_coin.wav       ← 金币音效

# 1) BGM 调音量到 -8dB + 淡入淡出
ffmpeg -i bgm.mp3 -af "volume=-8dB,afade=in:st=0:d=1,afade=out:st=33:d=2" -t 35 bgm_mixed.wav

# 2) 合成视频 + BGM
ffmpeg -i P002_xhs_raw.mp4 -i bgm_mixed.wav \
  -map 0:v -map 1:a \
  -c:v copy -c:a aac -b:a 192k \
  -shortest P002_xhs_with_bgm.mp4

# 3)（可选）叠加音效到指定时间点
ffmpeg -i P002_xhs_with_bgm.mp4 \
  -i sfx_stamp.wav -i sfx_page.wav -i sfx_coin.wav \
  -filter_complex "\
    [1:a]adelay=5000|5000,volume=-3dB[stamp1]; \
    [2:a]adelay=5500|5500,volume=-6dB[page1]; \
    [2:a]adelay=10600|10600,volume=-6dB[page2]; \
    [2:a]adelay=16600|16600,volume=-6dB[page3]; \
    [2:a]adelay=22600|22600,volume=-6dB[page4]; \
    [2:a]adelay=27600|27600,volume=-6dB[page5]; \
    [3:a]adelay=12000|12000,volume=-6dB[coin]; \
    [0:a][stamp1][page1][page2][page3][page4][page5][coin]amix=inputs=8:duration=longest" \
  -c:v copy P002_xhs_final.mp4
```

---

## 四、最终成片规格（小红书发布）

| 参数 | 值 |
|---|---|
| 分辨率 | 1080 × 1920 |
| 帧率 | 30 fps |
| 编码 | H.264 yuv420p |
| 比特率 | 8 Mbps（视频）/ 192 kbps（音频） |
| 时长 | 35 秒 |
| 容器 | MP4 |
| 文件名 | `P002_xhs_final.mp4` |

**验证命令**：
```bash
ffprobe -v error -show_entries stream=width,height,r_frame_rate,duration P002_xhs_final.mp4
```

---

## 五、音效素材推荐来源

| 音效 | 关键词 | 推荐站 |
|---|---|---|
| 报纸翻页 | newspaper turn page swoosh | freesound.org |
| 印章砸落 | rubber stamp impact thud | zapsplat.com |
| 金币掉落 | coin drop cha ching | pixabay sounds |
| 机械键盘 | mechanical keyboard typing | freesound.org |
| 倒计时滴答 | clock tick countdown | pixabay sounds |
| 微信消息提示 | notification ding | zapsplat.com |

全部用 CC0 协议素材，规避版权风险。

---

## 六、BGM 推荐（实操可用）

**无版权风险方案**（推荐用于小红书）：

1. **小红书音乐库**：发布时直接挂"欢快电子""复古迪斯科"分类下的官方曲库
2. **YouTube Audio Library**：搜索 "funky disco" / "upbeat retro" 分类
3. **抖音曲库联动**：发布时若同步抖音，挂热门 BGM 流量更好

**有版权但匹配气质的曲目**（仅供参考，需评估风险）：
- Daft Punk - One More Time
- Lipps Inc - Funkytown
- Anggun - Snow on the Sahara (Remix)
- Black Eyed Peas - Pump It

---

## 七、发布前自检清单

- [ ] 视频时长 30-40 秒（小红书甜区）
- [ ] 首帧 0.5 秒能看清标题（决定停留率）
- [ ] 字幕条始终可读，字号 ≥48px
- [ ] 无任何"AI / 工具 / IDE / 编辑器"等真名字眼
- [ ] BGM 音量 -8dB，不盖过字幕情绪
- [ ] 末帧 CTA 停留 ≥1 秒
- [ ] 文件 ≤500MB（小红书上限）
- [ ] 上传后预览 16:9 缩略图也能看清主标题

---

## 八、一键脚本（可选）

把上面 Playwright + FFmpeg 包成单脚本：

```bash
#!/usr/bin/env bash
# build_video.sh
set -e
cd "$(dirname "$0")"

echo "▶ 1. 启动本地服务"
python3 -m http.server 8765 &
SERVER_PID=$!
sleep 2

echo "▶ 2. Playwright 录屏"
python3 record.py

echo "▶ 3. 转 MP4"
ffmpeg -y -i recording/*.webm \
  -c:v libx264 -preset slow -crf 18 \
  -pix_fmt yuv420p -r 30 \
  -movflags +faststart \
  P002_xhs_raw.mp4

echo "▶ 4. 合 BGM"
ffmpeg -y -i P002_xhs_raw.mp4 -i ../assets/bgm.mp3 \
  -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest \
  P002_xhs_final.mp4

kill $SERVER_PID
echo "✓ 完成 → P002_xhs_final.mp4"
```

赋权 + 执行：
```bash
chmod +x build_video.sh
./build_video.sh
```
