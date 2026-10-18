from pathlib import Path
from streamlit.testing.v1 import AppTest

ROOT_DIR = Path(__file__).resolve().parent.parent
APP_PATH = ROOT_DIR / "src" / "app.py"


def run_test():
    at = AppTest.from_file(str(APP_PATH), default_timeout=30)
    at.run()
    assert len(at.exception) == 0, f"Found exceptions: {at.exception}"
    assert len(at.tabs) == 5, f"Expected 5 tabs, found {len(at.tabs)}"
    print(f"Verified {len(at.tabs)} tabs and {len(at.metric)} KPI metrics with 0 exceptions!")


if __name__ == "__main__":
    run_test()
