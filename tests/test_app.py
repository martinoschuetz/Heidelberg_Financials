from playwright.sync_api import sync_playwright
import time
import sys

def test_streamlit():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("http://localhost:8502")
        
        # Wait for streamlit to load the app (usually 2-3 seconds)
        print("Waiting for Streamlit app to load...")
        time.sleep(5)
        
        # Check for error elements
        errors = page.query_selector_all(".stException, .stExceptionContent, .stAlert")
        if errors:
            print("Found errors in the UI:")
            for err in errors:
                print(err.inner_text())
        else:
            print("No visible error boxes found.")
            
        # Check for the plotly chart
        chart = page.query_selector(".stPlotlyChart")
        if chart:
            print("Plotly chart element is present in the DOM.")
        else:
            print("Plotly chart element is MISSING.")
        
        # Take a screenshot just in case
        page.screenshot(path="screenshot.png")
        print("Saved screenshot.png")
        
        browser.close()

if __name__ == "__main__":
    test_streamlit()
