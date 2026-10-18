import pdfplumber
import pandas as pd
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
pdf_path = ROOT_DIR / "input" / "pdfs" / "20_pdf_haushaltsplan 2025_2026_web.pdf"
out_csv = ROOT_DIR / "data" / "gesamtergebnishaushalt_2025_2026.csv"
print(f"Analyzing {pdf_path}...")

data = []

with pdfplumber.open(pdf_path) as pdf:
    # We will search the first 50 pages for the Gesamtergebnishaushalt
    for i in range(min(50, len(pdf.pages))):
        page = pdf.pages[i]
        text = page.extract_text()
        if text and "Gesamtergebnishaushalt" in text:
            print(f"Found 'Gesamtergebnishaushalt' on page {i+1}")
            tables = page.extract_tables()
            if tables:
                for table in tables:
                    for row in table:
                        # Clean up row
                        row_cleaned = [str(x).replace('\n', ' ') if x else '' for x in row]
                        data.append(row_cleaned)
            else:
                print(f"No table found on page {i+1}")
            break

if data:
    df = pd.DataFrame(data)
    df.to_csv(out_csv, index=False)
    print(f"Extracted to {out_csv}")
else:
    print("Could not extract any tabular data for Gesamtergebnishaushalt.")
