"""Real Chromium verification for the user-facing MV production workspace."""

from __future__ import annotations

import json
from pathlib import Path

from playwright.sync_api import sync_playwright


URL = "http://127.0.0.1:8792"
PROJECT_ID = "project-2f570b21031eacb51056823acad1af3a"
OUTPUT = Path("tmp/browser-workflow")


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        console_errors = []
        page.on(
            "console",
            lambda message: console_errors.append(message.text)
            if message.type == "error" else None,
        )
        page.goto(URL, wait_until="networkidle", timeout=30_000)
        page.locator(f'button[data-project="{PROJECT_ID}"]').wait_for(
            state="visible", timeout=20_000,
        )
        page.locator("#stage-rail .rail-step").first.wait_for(state="visible")

        assert page.locator("#stage-rail .rail-step").count() == 8
        assert page.locator("#project-name").inner_text() == "青衣"
        assert page.locator("#current-stage-label").inner_text() == "当前：故事框架"
        assert "正式制作门禁" in page.locator(".approval-gate").inner_text()
        page.screenshot(path=str(OUTPUT / "01-story-gate.png"), full_page=True)

        page.locator('button[data-stage="intake"]').click()
        assert page.locator("[data-remove-asset]").count() == 4
        page.locator("[data-remove-asset]").first.click()
        page.locator("#asset-remove-dialog").wait_for(state="visible")
        assert "故事和分镜将标记为需要重新生成" in page.locator(
            "#asset-remove-dialog"
        ).inner_text()
        page.screenshot(path=str(OUTPUT / "02-asset-remove-confirm.png"), full_page=False)
        page.get_by_role("button", name="取消", exact=True).click()

        page.locator('button[data-stage="storyboard"]').click()
        page.locator(".shot-card").first.wait_for(state="visible")
        assert page.locator(".shot-card").count() == 6
        assert page.locator("[data-content-field]").count() == 36
        assert "结构测试" in page.locator("[data-content-field]").first.input_value()
        assert "自动测试流程" in page.locator(".truth-banner").inner_text()
        page.wait_for_function(
            """() => [...document.querySelectorAll('.shot-cast img')]
            .every((image) => image.complete && image.naturalWidth > 0)""",
            timeout=30_000,
        )
        assert page.locator(".animatic-preview video").count() == 1
        page.screenshot(path=str(OUTPUT / "03-storyboard.png"), full_page=True)

        page.locator(".prompt-settings > summary").click()
        prompt_status = page.locator(".prompt-use").inner_text()
        assert "未调用" in prompt_status
        assert "你是音乐视频动画导演与分镜设计师" in page.locator(
            "[data-prompt-system]"
        ).input_value()
        assert "逐镜视觉总谱" in page.locator(
            "[data-prompt-task]"
        ).input_value()
        page.locator(".translation-settings > summary").click()
        assert "影视制作系统的提示词翻译器" in page.locator(
            "[data-translation-system]"
        ).input_value()
        page.wait_for_timeout(2_500)
        assert page.locator(".prompt-settings").get_attribute("open") is not None
        page.screenshot(path=str(OUTPUT / "04-stage-prompts.png"), full_page=False)

        page.locator('button[data-stage="composite"]').click()
        page.locator(".video-gallery video").first.wait_for(state="visible")
        assert page.locator(".video-gallery video").count() == 2
        assert "没有调用图片或视频生成服务" in page.locator(".truth-banner").inner_text()
        assert "本步骤不调用生成模型" in page.locator(".prompt-none").inner_text()
        page.screenshot(path=str(OUTPUT / "05-composite.png"), full_page=True)

        page.set_viewport_size({"width": 390, "height": 844})
        page.locator('button[data-stage="storyboard"]').click()
        page.locator(".shot-card").first.wait_for(state="visible")
        page.screenshot(path=str(OUTPUT / "06-mobile-storyboard.png"), full_page=True)
        horizontal_overflow = page.evaluate(
            "document.documentElement.scrollWidth > window.innerWidth + 1"
        )
        result = {
            "url": page.url,
            "project_id": PROJECT_ID,
            "stage_count": 8,
            "shot_count": 6,
            "loaded_character_images": page.locator(".shot-cast img").count(),
            "composite_video_count": 2,
            "cost_total": page.locator("#cost-total").inner_text(),
            "horizontal_overflow_mobile": horizontal_overflow,
            "console_errors": console_errors,
        }
        assert not horizontal_overflow
        assert not console_errors
        (OUTPUT / "result.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8",
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        browser.close()


if __name__ == "__main__":
    main()
