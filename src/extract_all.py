import pdfplumber
import pandas as pd
import re
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
PDF_DIR = ROOT_DIR / "input" / "pdfs"
DATA_DIR = ROOT_DIR / "data"

pdfs = [
    PDF_DIR / "20_pdf_hh_2019_2020_Haushaltsplan.pdf",
    PDF_DIR / "20_pdf_hh_2021_2022_Haushaltsplan.pdf",
    PDF_DIR / "20_pdf_hh_2023_2024_Haushaltsplan.pdf",
    PDF_DIR / "20_pdf_haushaltsplan 2025_2026_web.pdf",
]

all_data = []

# List of income and expense categories (simplified)
ertraege_cats = [
    "Steuern und",
    "Zuweisungen,",
    "Aufgelöste Investitions",
    "Sonstige Transfer",
    "Entgelte für",
    "Sonstige Privatrechtliche",
    "Kostenerstattungen",
    "Zinsen und ähnliche Erträge",
    "Aktivierte Eigenleistungen",
    "Sonstige ordentliche Erträge"
]

aufwendungen_cats = [
    "Personalaufwendungen",
    "Versorgungsaufwendungen",
    "Aufwendungen für Sach-",
    "Abschreibungen",
    "Zinsen und ähnliche Aufwendungen",
    "Transferaufwendungen",
    "Sonstige ordentliche Aufwendungen"
]

def clean_amount(val):
    if not val or val.strip() == '':
        return 0.0
    val = str(val).replace('.', '').replace(',', '.').strip()
    try:
        return float(val)
    except:
        return 0.0

for pdf_path in pdfs:
    print(f"Processing {pdf_path}...")
    try:
        with pdfplumber.open(pdf_path) as pdf:
            found = False
            for i in range(min(100, len(pdf.pages))):
                page = pdf.pages[i]
                text = page.extract_text()
                if text and "Gesamtergebnishaushalt" in text:
                    tables = page.extract_tables()
                    if tables:
                        for table in tables:
                            if len(table) < 5: continue
                            
                            headers = table[0]
                            # Identify years from headers
                            years_cols = {}
                            for col_idx, h in enumerate(headers):
                                if h:
                                    m = re.search(r'20\d\d', str(h))
                                    if m:
                                        years_cols[col_idx] = int(m.group(0))
                            
                            if not years_cols:
                                continue
                                
                            for row in table[1:]:
                                category = str(row[0]).replace('\n', ' ').strip()
                                if not category: continue
                                
                                typ = None
                                if any(c.lower() in category.lower() for c in aufwendungen_cats):
                                    typ = "Aufwendungen"
                                elif any(c.lower() in category.lower() for c in ertraege_cats):
                                    typ = "Erträge"
                                
                                if typ:
                                    for col_idx, year in years_cols.items():
                                        if col_idx < len(row):
                                            val = clean_amount(row[col_idx])
                                            all_data.append({
                                                "Jahr": year,
                                                "Kategorie": category,
                                                "Typ": typ,
                                                "Betrag": val
                                            })
                        found = True
                        break
            if not found:
                print(f"Could not find table in {pdf_path}")
    except Exception as e:
        print(f"Error on {pdf_path}: {e}")

df = pd.DataFrame(all_data)
# Aggregate because sometimes Plan/Ergebnis for same year appear in multiple PDFs
df = df.groupby(["Jahr", "Typ", "Kategorie"], as_index=False).agg({"Betrag": "last"}) # taking latest available

df.to_csv(DATA_DIR / "haushalt_heidelberg_real.csv", index=False)
print(f"Extracted real data to {DATA_DIR / 'haushalt_heidelberg_real.csv'}")
