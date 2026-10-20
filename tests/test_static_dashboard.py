from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT_DIR = Path(__file__).resolve().parent.parent
HTML_PATH = ROOT_DIR / "docs" / "index.html"


def test_static_dashboard_e2e_and_reconciliation():
    """Headless browser E2E test for docs/index.html:
    - Verifies 0 JS console errors and 0 uncaught page errors
    - Verifies all 6 tabs render their Plotly charts and tables
    - Verifies client-side filtering speed (< 50 ms)
    - Verifies the live Reconciliation Matrix (#tblReconcil) reports 100% consistency on all 5 rules
    """
    assert HTML_PATH.exists(), f"Missing {HTML_PATH}"
    file_url = HTML_PATH.resolve().as_uri()

    console_errors = []
    page_errors = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        page.on("pageerror", lambda err: page_errors.append(str(err)))

        page.goto(file_url, wait_until="networkidle")

        # 1. Verify default 2025 KPI cards
        assert page.locator("#kpi1Val").inner_text() == "907.753.195 €"
        assert page.locator("#kpi2Val").inner_text() == "808.911.010 €"
        assert page.locator("#kpi3Val").inner_text() == "-98.842.185 €"
        assert page.locator("#tabBar .tab-btn").count() == 6

        # 2. Benchmark JS filterRowsForYear speed in browser
        elapsed_ms = page.evaluate(
            """() => {
                const t0 = performance.now();
                for (let y = 2013; y <= 2026; y++) {
                    filterRowsForYear(y);
                }
                return performance.now() - t0;
            }"""
        )
        assert elapsed_ms < 50.0, f"Client-side JS filtering too slow: {elapsed_ms:.2f} ms"

        # 3. Click through all 6 tabs and verify charts/tables
        for tab_id in ["tab2", "tab3", "tab4", "tab5", "tab6", "tab1"]:
            page.locator(f"#tabBar .tab-btn[data-tab='{tab_id}']").click()
            assert page.locator(f"#{tab_id}").is_visible()

        # 4. Switch to Tab 6 and verify Reconciliation Matrix (#tblReconcil)
        page.locator("#tabBar .tab-btn[data-tab='tab6']").click()
        reconcil_rows = page.locator("#tblReconcil tbody tr")
        assert reconcil_rows.count() == 5
        for i in range(5):
            row_txt = reconcil_rows.nth(i).inner_text()
            assert "✅ 100% Konsistent" in row_txt, f"Reconciliation failure in row {i}: {row_txt}"

        #Verify Investitionen & Gemeinderat tables are populated
        assert page.locator("#tblInvest tbody tr").count() == 29
        assert page.locator("#tblAntraege tbody tr").count() > 300

        # 5. Test year change to 2026
        page.locator("#selYear").select_option("2026")
        assert page.locator("#kpi1Val").inner_text() == "925.905.937 €"
        assert page.locator("#kpi2Val").inner_text() == "843.260.280 €"

        browser.close()

    assert len(console_errors) == 0, f"Console errors: {console_errors}"
    assert len(page_errors) == 0, f"Page errors: {page_errors}"
