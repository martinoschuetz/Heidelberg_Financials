"""Root entry-point wrapper for the Stadt Heidelberg Haushalt Explorer (`src/app.py`)."""
from pathlib import Path
import runpy

runpy.run_path(str(Path(__file__).resolve().parent / "src" / "app.py"), run_name="__main__")
