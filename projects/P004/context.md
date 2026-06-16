# 项目原料投喂包 · P004

## 作者一句话定位
Pinterest 类图片瀑布流项目

## 来源
- GitHub: git@github.com:steven-3352/Pinterest.git
- Demo: (无)

## README
(无 README)

## 依赖清单 / 技术栈
### package.json
```
{
  "name": "tonbird-site",
  "private": true,
  "description": "Tonbird landing + Netlify functions (welcome email, drip)",
  "dependencies": {
    "@netlify/blobs": "*"
  }
}

```

## 文件树（35 个，已过滤依赖/构建目录）
```
.gitignore
PLANNING.md
PROGRESS.md
assets/avatar/tonbird_avatar_v1.png
assets/emails/nurture-sequence.md
assets/lead-magnet-wealth-phoenix-guide.md
netlify.toml
netlify/functions/drip.mjs
netlify/functions/submission-created.js
package.json
pins/POSTING.md
pins/final/b2_01_pyrite.png
pins/final/b2_02_colors.png
pins/final/b2_03_newmoon.png
pins/final/b2_04_wallet.png
pins/final/b2_05_flows.png
pins/final/b2_06_pixiu.png
pins/final/b2_07_jade.png
pins/final/b2_08_magnet.png
pins/final/b2_09_fullmoon.png
pins/final/b2_10_aventurine.png
pins/final/pin01_wealth_corner.png
pins/final/pin02_citrine.png
pins/final/pin03_declutter.png
pins/final/pin04_affirmation.png
pins/final/pin05_door.png
scripts/build_guide_pdf.py
scripts/compose_pin.py
scripts/gen_image.py
site/blueprint.html
site/index.html
site/phoenix-hero.png
site/success.html
site/unsubscribe.html
site/wealth-phoenix-guide.pdf
```

## 关键源码片段
### scripts/gen_image.py
```
#!/usr/bin/env python3
"""Tonbird image generator — OpenAI-compatible /images/generations endpoint.

Usage:
  python3 scripts/gen_image.py "PROMPT" [--size 1024x1536] [--out pins/generated/foo.png]
"""
import os, sys, base64, json, argparse, urllib.request, urllib.error, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent

def load_env(path=ROOT / ".env"):
    env = {}
    if path.exists():
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("prompt")
    ap.add_argument("--size", default="1024x1536")  # vertical, closest to Pinterest 2:3
    ap.add_argument("--out", default=str(ROOT / "pins/generated/test.png"))
    ap.add_argument("--quality", default="high")
    args = ap.parse_args()

    env = load_env()
    base = env.get("OPENAI_BASE_URL", "").rstrip("/")
    key = env.get("OPENAI_API_KEY", "")
    model = env.get("OPENAI_IMAGE_MODEL", "gpt-image-2")
    if not base or not key:
        sys.exit("ERROR: OPENAI_BASE_URL / OPENAI_API_KEY missing in .env")

    url = f"{base}/images/generations"
    payload = {"model": model, "prompt": args.prompt, "size": args.size, "n": 1}
    # gpt-image models support quality; harmless if ignored
    payload["quality"] = args.quality

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    print(f"-> POST {url}  model={model} size={args.size}")
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            data = json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        sys.exit(f"HTTP {e.code}: {e.read().decode()[:800]}")
    except Exception as e:
        sys.exit(f"REQUEST FAILED: {e}")

    item = data.get("data", [{}])[0]
    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    if item.get("b64_json"):
        out.write_bytes(base64.b64decode(item["b64_json"]))
    elif item.get("url"):
        with urllib.request.urlopen(item["url"], timeout=180) as ir:
            out.write_bytes(ir.read())
    else:
 
```
### scripts/compose_pin.py
```
#!/usr/bin/env python3
"""Tonbird pin composer — overlay crisp typographic text on an AI background.

Anti-AI-slop workflow: AI makes the *background only* (no text); we typeset the
words with real fonts via headless Chrome. 1000x1500 (Pinterest 2:3), rendered
at 2x for crispness.

Usage:
  python3 scripts/compose_pin.py --bg pins/generated/foo_bg.png \
      --kicker "FENG SHUI · SECRET 01" \
      --title "Awaken Your<br>Wealth Corner" \
      --subtitle "The far corner from your door holds your money luck..." \
      --cta "Free guide — The Wealth Phoenix Guide" \
      --out pins/final/pin01.png
"""
import argparse, base64, pathlib, subprocess, sys, tempfile, mimetypes

ROOT = pathlib.Path(__file__).resolve().parent.parent
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

HTML = """<!DOCTYPE html><html><head><meta charset="utf-8"><style>
  *{{margin:0;padding:0;box-sizing:border-box;}}
  html,body{{width:1000px;height:1500px;}}
  .pin{{
    position:relative;width:1000px;height:1500px;overflow:hidden;
    font-family:"Helvetica Neue",Arial,sans-serif;
  }}
  .bg{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;}}
  /* legibility scrims: darken top (title) and bottom (cta) */
  .scrim{{position:absolute;inset:0;background:
     linear-gradient(180deg, rgba(8,6,5,.78) 0%, rgba(8,6,5,.30) 34%, rgba(8,6,5,0) 52%,
                     rgba(8,6,5,.12) 72%, rgba(8,6,5,.86) 100%);}}
  .frame{{position:absolute;inset:26px;border:1.5px solid rgba(201,162,75,.42);border-radius:6px;
     pointer-events:none;}}
  .top{{position:absolute;top:92px;left:78px;right:78px;}}
  .kicker{{font-size:23px;letter-spacing:.40em;text-transform:uppercase;
     color:#e8c879;font-weight:600;margin-bottom:30px;}}
  .rule{{width:54px;height:2px;background:#c9a24b;margin-bottom:28px;}}
  .title{{font-family:"Didot","Baskerville",Georgia,serif;color:#fdf8ee;
     font-size:96px;line-height:1.02;font-weight:400;letter-spacing:.005em;
     text-shadow:0 2px 30px rgba(0,0,0,.55);}}
  .title em{{color:#e8c879;font-style:italic;}}
  .subtitle{{margin-top:34px;font-size:30px;line-height:1.5;color:#ece3d2;
     font-weight:300;max-width:74%;text-shadow:0 2px 16px rgba(0,0,0,.6);}}
  .bottom{{position:absolute;bottom:92px;left:78px;right:78px;display:flex;
     align-items:center;justify-content:space-between;gap:20px;}}
  .cta{{font-size:27px;color:#fdf
```
### scripts/build_guide_pdf.py
```
#!/usr/bin/env python3
"""Build the branded lead-magnet PDF (The Wealth Phoenix Guide) via headless Chrome.

Dark full-bleed cover + light readable interior. Gold/ink quiet-luxury palette,
Didot/Georgia serif. Source content mirrors assets/lead-magnet-wealth-phoenix-guide.md.

Usage: python3 scripts/build_guide_pdf.py
Output: site/wealth-phoenix-guide.pdf
"""
import base64, pathlib, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
AVATAR = ROOT / "assets/avatar/tonbird_avatar_v1.png"
OUT = ROOT / "site/wealth-phoenix-guide.pdf"

SECRETS = [
    ("01", "Awaken Your Wealth Corner",
     "In classical feng shui, the far-left corner from your front door (the southeast in "
     "many traditions) is your home's <b>wealth corner</b> (財位). Keep it clean, lit, and "
     "alive. Place something that grows — a healthy plant, a bowl of coins, or a touch of "
     "gold. This is where your abundance story begins."),
    ("02", "Let the Qi Flow — Clear the Clutter",
     "Stuck stuff, stuck money. Clutter blocks <b>qi</b> (氣), the life energy that carries "
     "wealth into your home. Choose one drawer, one corner, one shelf this week. As you clear "
     "the old, you make space for the new to arrive."),
    ("03", "Carry Citrine, the Merchant's Stone",
     "For centuries, golden <b>citrine</b> has been called the stone of wealth and confidence, "
     "while glittering <b>pyrite</b> is known as the “money magnet.” Keep one near where you "
     "work or where money moves through your home. Let its warm color remind you, daily, that "
     "abundance is your natural state."),
    ("04", "The Flowing Bowl",
     "Moving water has always symbolized flowing wealth. A small fountain — or simply a "
     "beautiful bowl of clear water refreshed often — near your entrance invites prosperity to "
     "circulate rather than stagnate. Still, stale water does the opposite, so keep it fresh."),
    ("05", "Honor the Mouth of Qi",
     "Your <b>front door</b> is the “mouth of qi” — where all energy, including opportunity, "
     "enters. Keep it clean, unobstructed, and welcoming. A door that opens fully and freely "
     "is a life that opens fully and freely."),
    ("06", "The Daily Abundance Ritual",
     "Each morning, place a hand over your heart and speak one line alou
```
### netlify/functions/submission-created.js
```
// Netlify automatically invokes this function whenever a form submission is
// created (function name must be "submission-created"). It sends the Tonbird
// welcome email via Resend. Env var EMAIL_API_KEY must be set in Netlify.
//
// Docs: https://docs.netlify.com/functions/trigger-on-events/

const FROM = "Tonbird <hello@tonbirds.com>";
const GUIDE_URL = "https://fengshui.tonbirds.com/wealth-phoenix-guide.pdf";

function welcomeHtml(firstName) {
  const name = firstName && firstName.trim() ? firstName.trim() : "there";
  return `<!DOCTYPE html><html><body style="margin:0;background:#faf6ee;font-family:Georgia,'Times New Roman',serif;color:#211b16;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#faf6ee;padding:32px 16px;">
    <tr><td align="center">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:520px;background:#ffffff;border:1px solid #ecdfc4;border-radius:14px;overflow:hidden;">
        <tr><td style="background:#0e0b0a;padding:34px 28px;text-align:center;">
          <div style="letter-spacing:.4em;text-transform:uppercase;font-size:12px;color:#c9a24b;font-family:Arial,sans-serif;">Tonbird</div>
          <div style="font-size:30px;color:#fdf8ee;margin-top:10px;">Your phoenix is rising <span style="color:#e8c879;">🔥</span></div>
        </td></tr>
        <tr><td style="padding:30px 30px 8px;">
          <p style="font-size:16px;line-height:1.7;margin:0 0 16px;">Hi ${name},</p>
          <p style="font-size:16px;line-height:1.7;margin:0 0 16px;">Welcome to Tonbird. Here is your free guide, as promised:</p>
          <p style="text-align:center;margin:24px 0;">
            <a href="${GUIDE_URL}" style="display:inline-block;background:#c9a24b;color:#1a1206;text-decoration:none;font-family:Arial,sans-serif;font-weight:bold;font-size:15px;padding:14px 26px;border-radius:9px;">↓ Download The Wealth Phoenix Guide</a>
          </p>
          <p style="font-size:16px;line-height:1.7;margin:0 0 16px;">Inside are seven feng shui secrets, drawn from over 5,000 years of Eastern wisdom, for inviting wealth energy (財氣) to flow more freely through your home and your days.</p>
          <p style="font-size:16px;line-height:1.7;margin:0 0 16px;">A gentle suggestion: don't try all seven at once. Choose <em>one</em> that speaks to you and begin there this week. Small, beautif
```

## 近期提交
```
2c27498 docs: PROGRESS — drip live (full nurture sequence automated)
```

## Demo 页面文本（去标签）
(未提供 demo URL)
