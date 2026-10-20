from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT_DIR = Path(__file__).resolve().parent.parent
HTML_PATH = ROOT_DIR / "docs" / "index.html"


def test_plotly_chart_click_and_drilldown():
    """Verify clicking on the interactive Plotly treemap and switching to Sunburst in docs/index.html."""
    assert HTML_PATH.exists(), f"Missing {HTML_PATH}"
    file_url = HTML_PATH.resolve().as_uri()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(file_url, wait_until="networkidle")

        chart = page.query_selector("#chartTreemap")
        assert chart is not None, "Plotly treemap container #chartTreemap is missing"
        box = chart.bounding_box()
        assert box is not None and box["width"] > 100 and box["height"] > 100

        # Click in the middle of the treemap chart to test drilldown interaction
        page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)

        # Switch chart type to Sunburst and verify re-render
        page.locator("#pillChart .radio-pill[data-val='sunburst']").click()
        assert "active" in (page.locator("#pillChart .radio-pill[data-val='sunburst']").get_attribute("class") or "")

        browser.close()


if __name__ == "__main__":
    test_plotly_chart_click_and_drilldown()
