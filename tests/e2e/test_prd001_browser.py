"""PRD-001 E2E tests: progress UI, retry button, service restart recovery."""
import json
import os
import time
import urllib.error
import urllib.request

import pytest

BASE_URL = "http://127.0.0.1:8792"

# ---------------------------------------------------------------------------
# Environment guard
# ET-001/ET-002 require an interactive browser session with a pre-configured
# project in storyboard state.  Set E2E_UI_TESTS=1 to run them.
# ---------------------------------------------------------------------------

_UI_TESTS_ENABLED = os.environ.get("E2E_UI_TESTS", "0") == "1"

try:
    from playwright.sync_api import sync_playwright
    _PLAYWRIGHT_AVAILABLE = True
except ImportError:
    _PLAYWRIGHT_AVAILABLE = False

requires_ui = pytest.mark.skipif(
    not (_PLAYWRIGHT_AVAILABLE and _UI_TESTS_ENABLED),
    reason=(
        "ET-001/ET-002 需要 Playwright 且 E2E_UI_TESTS=1；"
        "当前未启用，已跳过。运行方式：E2E_UI_TESTS=1 pytest tests/e2e/test_prd001_browser.py"
    ),
)


# ---------------------------------------------------------------------------
# Helpers shared by ET-001/ET-002
# ---------------------------------------------------------------------------

def _http_get(url: str, timeout: float = 3.0):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, b""
    except Exception:
        return None, b""


def _http_post(url: str, timeout: float = 5.0):
    req = urllib.request.Request(
        url, data=b"{}", method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status
    except urllib.error.HTTPError as exc:
        return exc.code
    except Exception:
        return None


def _find_storyboard_project():
    """Return project_id of first project that has a storyboard stage, or None."""
    status, body = _http_get(f"{BASE_URL}/api/v1/projects")
    if status != 200 or not body:
        return None
    for p in json.loads(body):
        pid = p["project_id"]
        ws, wb = _http_get(f"{BASE_URL}/api/v1/projects/{pid}/workflow")
        if ws != 200:
            continue
        wf = json.loads(wb)
        for stage in wf.get("stages", []):
            if stage.get("id") == "storyboard" and stage.get("data", {}).get("shots"):
                return pid
    return None


# ---------------------------------------------------------------------------
# ET-001: clicking generate background shows four-phase progress UI
# ---------------------------------------------------------------------------

@pytest.mark.e2e
@requires_ui
def test_background_generate_shows_progress():
    """ET-001: 点击生成背景后按钮区域替换为四阶段进度容器。"""
    project_id = _find_storyboard_project()
    if not project_id:
        pytest.skip("ET-001: 当前服务无分镜数据，已跳过")

    def _hang(route):
        # Fulfill after a small delay so the JS progress div stays visible
        time.sleep(0.3)
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps({"stages": []}),
        )

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(BASE_URL)

        page.wait_for_selector(f"[data-project='{project_id}']", timeout=10_000)
        page.click(f"[data-project='{project_id}']")
        page.wait_for_selector("button[data-generate-background]:not([disabled])", timeout=10_000)

        page.route("**/background/generate", _hang)
        page.click("button[data-generate-background]:not([disabled])")

        page.wait_for_selector(".generation-progress", timeout=5_000)
        content = page.inner_text(".generation-progress")
        assert "翻译执行稿" in content or "整理中文指令" in content

        browser.close()


# ---------------------------------------------------------------------------
# ET-002: translate failure shows failed phase + retry button
# ---------------------------------------------------------------------------

@pytest.mark.e2e
@requires_ui
def test_background_generate_shows_retry_on_fail():
    """ET-002: 翻译失败时显示失败阶段和重试按钮。"""
    project_id = _find_storyboard_project()
    if not project_id:
        pytest.skip("ET-002: 当前服务无分镜数据，已跳过")

    def _mock_fail(route):
        route.fulfill(
            status=423,
            content_type="application/json",
            body=json.dumps({
                "detail": "图片提示词翻译失败，请查看错误日志后重试",
                "error_stage": "translate_prompt",
                "error_category": "timeout",
            }),
        )

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.route("**/background/generate", _mock_fail)
        page.goto(BASE_URL)

        page.wait_for_selector(f"[data-project='{project_id}']", timeout=10_000)
        page.click(f"[data-project='{project_id}']")
        page.wait_for_selector("button[data-generate-background]:not([disabled])", timeout=10_000)
        page.click("button[data-generate-background]:not([disabled])")

        page.wait_for_selector(".progress-phase.failed", timeout=5_000)
        page.wait_for_selector("button.retry-generate", timeout=5_000)
        assert page.is_visible("button.retry-generate")

        browser.close()


# ---------------------------------------------------------------------------
# ET-003: service restart recovers /readyz within 15 seconds (3×)
# ---------------------------------------------------------------------------

def _wait_ready(deadline: float) -> bool:
    while time.time() < deadline:
        status, body = _http_get(f"{BASE_URL}/readyz")
        if status == 200 and b"ready" in body:
            return True
        time.sleep(0.5)
    return False


@pytest.mark.e2e
@pytest.mark.parametrize("run", [1, 2, 3])
def test_service_restart_recovers(run):
    """ET-003: POST /system/restart 后 /readyz 在 15 秒内恢复，重复三次。"""
    status_before, _ = _http_get(f"{BASE_URL}/readyz")
    assert status_before == 200, f"服务在重启前未就绪 (run={run})"

    _http_post(f"{BASE_URL}/api/v1/system/restart")

    time.sleep(1.5)

    deadline = time.time() + 15.0
    assert _wait_ready(deadline), f"服务在 15 秒内未恢复 (run={run})"

    status_projects, _ = _http_get(f"{BASE_URL}/api/v1/projects")
    assert status_projects == 200, f"/api/v1/projects 重启后不可用 (run={run})"
