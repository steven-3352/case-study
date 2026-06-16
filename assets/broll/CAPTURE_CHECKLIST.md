# P001 · 素材来源说明

## 无补拍时

运行 `python3 pipeline/gen_evidence.py`，输出到 `assets/broll/generated/`：

| 文件 | 体裁 | 用途 |
|------|------|------|
| MEMO01_background.png | iOS 备忘录 | story 02 |
| MEMO02_cta.png | iOS 备忘录 | story 07 |
| BR001_safari_landing.png | Safari + 真实 landing 截屏 | story 03 |
| BR003_welcome_mail.png | iOS 收件箱 | stack 下半 |
| STACK_submit_welcome.png | 双截屏竖拼 | story 04 |
| BR004_analytics_day5.png | 移动端 Analytics | story 05 底图 |
| BR004_analytics_annotated.png | 后台 + 红圈标注 | story 01 封面 |
| BR004_day5_tagged.png | 后台 + Day5 标签 | story 05 |
| BR006_ai_vs_manual.png | 相册对比 | story 06 |

数据数字为 **B 级叙事区间**（Q4），非真实后台导出。

## 有实拍后

同名文件放入 `assets/broll/screenshot/` 或 `memo/`，改 `render_xhs_story.py` 的 `SLIDES` 路径优先读实拍目录即可替换。

## 渲染

```bash
python3 pipeline/render_xhs_story.py      # 仅 story 图文
python3 pipeline/render_p001.py --video xhs # story 视频（用 generated 画面）
```
