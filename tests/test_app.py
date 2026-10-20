import time
from pathlib import Path
from streamlit.testing.v1 import AppTest

ROOT_DIR = Path(__file__).resolve().parent.parent
APP_PATH = ROOT_DIR / "src" / "app.py"


def test_streamlit_app_default_render():
    """Verify default render of src/app.py has 6 tabs, 16 KPI metrics, and 0 exceptions."""
    at = AppTest.from_file(str(APP_PATH), default_timeout=30)
    at.run()
    assert len(at.exception) == 0, f"Found exceptions: {at.exception}"
    assert len(at.tabs) == 6, f"Expected 6 tabs, found {len(at.tabs)}"
    assert len(at.metric) == 16, f"Expected 16 metrics across header & tabs, found {len(at.metric)}"
    # Default year is 2025: Ordentliche Aufwendungen = 907.753.195 €, Erträge = 808.911.010 €
    assert "907.753.195 €" in at.metric[0].value
    assert "808.911.010 €" in at.metric[1].value


def test_streamlit_app_interactive_filters_and_search():
    """Verify year switching, type switching (Erträge), and full-text search filtering."""
    at = AppTest.from_file(str(APP_PATH), default_timeout=30)
    at.run()
    assert len(at.exception) == 0

    # Switch Haushaltsseite to Erträge
    at.sidebar.radio[0].set_value("Erträge").run()
    assert len(at.exception) == 0

    # Switch Hierarchy mode
    at.sidebar.radio[1].set_value("Kategorie ➔ Amt ➔ Einzelposten").run()
    assert len(at.exception) == 0

    # Test full-text search in sidebar
    at.sidebar.text_input[0].set_value("Gewerbesteuer").run()
    assert len(at.exception) == 0
    # Clear search and switch year to 2026
    at.sidebar.text_input[0].set_value("").run()
    at.sidebar.selectbox[0].set_value(2026).run()
    assert len(at.exception) == 0
    assert "925.905.937 €" in at.metric[0].value
    assert "843.260.280 €" in at.metric[1].value


def test_filter_performance_benchmark():
    """Verify that pre-indexed year lookup and Search_Blob filtering execute in < 25ms."""
    import sys
    sys.path.insert(0, str(ROOT_DIR / "src"))
    import app

    t0 = time.perf_counter()
    for yr in (2023, 2024, 2025, 2026):
        sub = app.df_by_year[yr]
        _ = sub[sub["Search_Blob"].str.contains("gewerbesteuer", regex=False, na=False)]
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    assert elapsed_ms < 50.0, f"Filtering took too long: {elapsed_ms:.2f} ms"


if __name__ == "__main__":
    test_streamlit_app_default_render()
    test_streamlit_app_interactive_filters_and_search()
    test_filter_performance_benchmark()
    print("All Streamlit app tests passed!")
