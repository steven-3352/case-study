"""Playwright · 创作者中心 Cookie 会话拉数."""
from __future__ import annotations

import pathlib
import re
import subprocess
import time
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[3]

LOGIN_MARKERS = ("扫码登录", "登录/注册", "请登录", "手机号登录", "验证码登录")
LOGGED_IN_MARKERS = ("作品管理", "内容管理", "数据中心", "创作中心", "发布作品", "笔记管理")


class SessionExpiredError(Exception):
    """Cookie 失效 · 需重新扫码."""

    def __init__(self, platform: str, reason: str = ""):
        self.platform = platform
        self.reason = reason
        super().__init__(f"{platform} 会话过期: {reason or '未登录'}")


def notify_mac(title: str, message: str) -> None:
    safe_t = title.replace('"', "'")
    safe_m = message.replace('"', "'")
    subprocess.run(
        [
            "osascript", "-e",
            f'display notification "{safe_m}" with title "{safe_t}" sound name "Glass"',
        ],
        check=False,
    )


def dialog_mac(title: str, message: str, button: str = "已完成登录") -> None:
    safe_t = title.replace('"', "'")
    safe_m = message.replace('"', "'")
    subprocess.run(
        [
            "osascript", "-e",
            f'display dialog "{safe_m}" buttons {{"{button}"}} '
            f'default button 1 with title "{safe_t}" giving up after 600',
        ],
        check=False,
    )


def _parse_number(text: str) -> float | None:
    text = text.strip().replace(",", "").replace("，", "")
    if not text or text in ("-", "—", "--"):
        return None
    m = re.search(r"([\d.]+)\s*(万|w|W)?", text)
    if not m:
        return None
    val = float(m.group(1))
    if m.group(2) in ("万", "w", "W"):
        val *= 10000
    if "%" in text:
        if val > 1:
            return val / 100.0
    return val


def _is_login_page(url: str, body: str) -> bool:
    u = url.lower()
    if "login" in u or "passport" in u:
        return True
    if any(m in body for m in LOGIN_MARKERS) and not any(m in body for m in LOGGED_IN_MARKERS):
        return True
    return False


def _page_text_metrics(page_text: str, field_map: dict[str, list[str]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, labels in field_map.items():
        for label in labels:
            pat = rf"{re.escape(label)}[^\d]*([\d.]+\s*%?)"
            m = re.search(pat, page_text)
            if m:
                v = _parse_number(m.group(1))
                if v is not None:
                    out[key] = v
                    break
    for label in ("播放量", "播放", "观看量", "浏览"):
        m = re.search(rf"{re.escape(label)}[^\d]*([\d.]+\s*[万wW]?)", page_text)
        if m:
            out["views"] = int(_parse_number(m.group(1)) or 0)
            break
    for label in ("点赞", "评论", "收藏", "分享"):
        m = re.search(rf"{re.escape(label)}[^\d]*([\d.]+\s*[万wW]?)", page_text)
        if m:
            k = {"点赞": "likes", "评论": "comments", "收藏": "collects", "分享": "shares"}.get(label)
            if k:
                out[k] = int(_parse_number(m.group(1)) or 0)
    return out


def probe_session(platform: str, config: dict) -> bool:
    """探测 Cookie 是否仍有效（不拉具体作品数据）."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return False

    acct = config["accounts"][platform]
    session_path = ROOT / acct["session_file"]
    if not session_path.exists():
        return False

    fetch_cfg = config.get("fetch", {})
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state=str(session_path))
        page = context.new_page()
        page.set_default_timeout(fetch_cfg.get("timeout_ms", 30000))
        page.goto(acct["content_url"], wait_until="domcontentloaded")
        time.sleep(1.5)
        ok = not _is_login_page(page.url, page.inner_text("body"))
        if ok:
            context.storage_state(path=str(session_path))
        browser.close()
    return ok


def fetch_with_playwright(
    platform: str,
    keywords: list[str],
    config: dict,
) -> dict[str, Any]:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as e:
        raise RuntimeError(
            "缺少 playwright · 运行: .venv/bin/pip install playwright && .venv/bin/playwright install chromium"
        ) from e

    acct = config["accounts"][platform]
    session_path = ROOT / acct["session_file"]
    if not session_path.exists():
        raise SessionExpiredError(platform, "无 session 文件")

    field_map = config.get("field_map", {}).get(platform, {})
    content_url = acct["content_url"]
    fetch_cfg = config.get("fetch", {})

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=fetch_cfg.get("headless", True))
        context = browser.new_context(storage_state=str(session_path))
        page = context.new_page()
        page.set_default_timeout(fetch_cfg.get("timeout_ms", 30000))

        page.goto(content_url, wait_until="domcontentloaded")
        time.sleep(fetch_cfg.get("wait_after_nav_ms", 2000) / 1000)

        body = page.inner_text("body")
        if _is_login_page(page.url, body):
            browser.close()
            raise SessionExpiredError(platform, "跳转登录页")

        matched_kw = None
        row_text = body
        for kw in keywords:
            if not kw:
                continue
            try:
                loc = page.get_by_text(kw, exact=False)
                if loc.count() > 0:
                    matched_kw = kw
                    el = loc.first
                    # 尽量只取含关键词的行/卡片文本，避免整页汇总数字
                    try:
                        row = el.locator("xpath=ancestor::*[self::tr or contains(@class,'card') or contains(@class,'item')][1]")
                        if row.count() > 0:
                            row_text = row.first.inner_text()
                        else:
                            row_text = el.inner_text()
                    except Exception:
                        row_text = el.inner_text()
                    el.click(timeout=3000)
                    time.sleep(1.5)
                    detail = page.inner_text("body")
                    if len(detail) > len(row_text) + 50:
                        row_text = detail
                    else:
                        row_text = row_text + "\n" + detail
                    break
            except Exception:
                continue

        metrics = _page_text_metrics(row_text, field_map)
        metrics["_source"] = f"playwright:{platform}"
        metrics["_matched_keyword"] = matched_kw

        context.storage_state(path=str(session_path))
        browser.close()

    if not metrics.get("views") and not metrics.get("completion_rate"):
        raise RuntimeError(
            f"页面未解析到数据（关键词 {keywords}）· 可能作品未发布或标题不匹配"
        )
    return metrics


def login_and_save_session(
    platform: str,
    config: dict,
    *,
    wait: str = "dialog",
) -> pathlib.Path:
    """扫码登录 · wait=dialog 弹 macOS 对话框（适合定时任务/无终端）."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as e:
        raise RuntimeError("pip install playwright && playwright install chromium") from e

    acct = config["accounts"][platform]
    session_path = ROOT / acct["session_file"]
    session_path.parent.mkdir(parents=True, exist_ok=True)

    notify_mac("平台数据同步", f"请扫码登录 · {acct['label']}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto(acct["login_url"])
        page.bring_to_front()

        label = acct["label"]
        if wait == "dialog":
            dialog_mac(
                "平台数据 · 扫码登录",
                f"已在浏览器打开 {label}。\n\n请完成扫码/手机登录，成功后点击「已完成登录」。",
            )
        else:
            print(f"\n请在浏览器中登录 {label}（扫码/手机）")
            print("登录成功后回到终端按 Enter…")
            input()

        context.storage_state(path=str(session_path))
        browser.close()

    notify_mac("平台数据同步", f"{label} 登录成功，会话已保存")
    print(f"✓ 会话已保存: {session_path}")
    return session_path


def ensure_session(platform: str, config: dict) -> None:
    """无 session 或已过期 → 弹浏览器扫码."""
    session_path = ROOT / config["accounts"][platform]["session_file"]
    if session_path.exists() and probe_session(platform, config):
        return
    login_and_save_session(platform, config, wait="dialog")
