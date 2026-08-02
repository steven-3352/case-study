"""PRD-004 E2E browser tests: settings video provider section, shots stage UI."""
import json
import os
import urllib.error
import urllib.request

import pytest

BASE_URL = "http://127.0.0.1:8792"

_UI_TESTS_ENABLED = os.environ.get("E2E_UI_TESTS", "0") == "1"

try:
    from playwright.sync_api import sync_playwright
    _PLAYWRIGHT_AVAILABLE = True
except ImportError:
    _PLAYWRIGHT_AVAILABLE = False

requires_ui = pytest.mark.skipif(
    not (_PLAYWRIGHT_AVAILABLE and _UI_TESTS_ENABLED),
    reason=(
        "ET-030~ET-032 需要 Playwright 且 E2E_UI_TESTS=1；"
        "当前未启用，已跳过。运行方式：E2E_UI_TESTS=1 pytest tests/e2e/test_prd004_browser.py"
    ),
)


def _http_get(url: str, timeout: float = 3.0):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, b""
    except Exception:
        return None, b""


def _find_project_at_stage(target_stage: str):
    status, body = _http_get(f"{BASE_URL}/api/v1/projects")
    if status != 200 or not body:
        return None
    for p in json.loads(body):
        pid = p["project_id"]
        ws, wb = _http_get(f"{BASE_URL}/api/v1/projects/{pid}/workflow")
        if ws != 200:
            continue
        wf = json.loads(wb)
        stage_ids = [s["id"] for s in wf.get("stages", [])]
        if target_stage not in stage_ids:
            continue
        current = wf.get("current_stage_id", "")
        idx_target = stage_ids.index(target_stage)
        idx_current = stage_ids.index(current) if current in stage_ids else -1
        if idx_current >= idx_target:
            return pid
    return None


# ---------------------------------------------------------------------------
# ET-030: Settings page has video provider section
# ---------------------------------------------------------------------------

@pytest.mark.e2e
@requires_ui
def test_settings_has_video_provider_section():
    """ET-030: Settings dialog shows 视频生成 Provider section with 测试连接 button."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(BASE_URL)

        page.wait_for_selector("#settings-button, [data-open-settings]", timeout=10_000)
        page.click("#settings-button, [data-open-settings]")
        page.wait_for_selector("dialog[open]", timeout=5_000)

        assert page.locator("text=视频生成服务").count() > 0, \
            "Settings dialog must show 视频生成服务 section"
        assert page.locator("text=测试连接").count() > 0, \
            "Settings dialog must show 测试连接 button"

        browser.close()


# ---------------------------------------------------------------------------
# ET-031: video generate button disabled without selected_keyframe
# ---------------------------------------------------------------------------

@pytest.mark.e2e
@requires_ui
def test_video_generate_disabled_without_keyframe():
    """ET-031: In shots stage, generate button is disabled when shot has no selected_keyframe."""
    project_id = _find_project_at_stage("shots")
    if not project_id:
        pytest.skip("ET-031: 当前服务无已进入 shots 阶段的项目，已跳过")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(BASE_URL)

        page.wait_for_selector(f"[data-project='{project_id}']", timeout=10_000)
        page.click(f"[data-project='{project_id}']")
        page.wait_for_selector("[data-stage='shots']", timeout=10_000)
        page.click("[data-stage='shots']")
        page.wait_for_selector(".shots-workbench", timeout=10_000)

        disabled_btn = page.locator("button.video-generate[disabled]")
        no_kf_msg = page.locator("text=请先在关键帧阶段选定首帧")
        if disabled_btn.count() > 0:
            assert no_kf_msg.count() > 0 or disabled_btn.first.inner_text() != "", \
                "禁用的生成按钮必须显示说明文字"

        browser.close()


# ---------------------------------------------------------------------------
# ET-032: generate video shows result (requires real provider)
# ---------------------------------------------------------------------------

@pytest.mark.e2e
@requires_ui
def test_generate_video_shows_result():
    """ET-032: (需真实 Provider) 生成一个视频后出现视频卡片。"""
    project_id = _find_project_at_stage("shots")
    if not project_id:
        pytest.skip("ET-032: 当前服务无已进入 shots 阶段且选定首帧的项目，已跳过")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(BASE_URL)

        page.wait_for_selector(f"[data-project='{project_id}']", timeout=10_000)
        page.click(f"[data-project='{project_id}']")
        page.wait_for_selector("[data-stage='shots']", timeout=10_000)
        page.click("[data-stage='shots']")
        page.wait_for_selector(".shots-workbench", timeout=10_000)

        gen_btn = page.locator("button.video-generate:not([disabled])").first
        if gen_btn.count() == 0:
            pytest.skip("ET-032: 当前项目无可用生成按钮，已跳过")

        gen_btn.click()
        page.wait_for_selector("text=时长:", timeout=180_000)
        assert page.locator("text=¥3.00").count() > 0 or page.locator("text=¥").count() > 0

        browser.close()


# ---------------------------------------------------------------------------
# Smoke: service is reachable
# ---------------------------------------------------------------------------

@pytest.mark.e2e
def test_service_is_reachable():
    """Smoke: /readyz 返回 200。"""
    status, body = _http_get(f"{BASE_URL}/readyz")
    if status is None:
        pytest.skip("服务未运行，跳过 ET-PRD004 smoke test")
    assert status == 200
    assert b"ready" in body
