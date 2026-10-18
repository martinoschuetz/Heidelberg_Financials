from playwright.sync_api import sync_playwright
import time

def test_streamlit():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("http://localhost:8501")
        
        # Wait for streamlit to load the app
        time.sleep(5)
        
        # Look for the plotly chart
        chart = page.query_selector(".stPlotlyChart")
        if chart:
            # Click in the middle of the chart
            box = chart.bounding_box()
            page.mouse.click(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2)
            print("Clicked on the chart")
            time.sleep(3)
            # Dump the page text to see what the debug event says
            print(page.inner_text("body"))
        else:
            print("Plotly chart element is MISSING.")
        
        browser.close()

if __name__ == "__main__":
    test_streamlit()
