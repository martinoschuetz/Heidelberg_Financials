import pymupdf as fitz
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

ertraege_cats = [
    "Steuern und", "Zuweisungen,", "Aufgelöste Investitions",
    "Sonstige Transfer", "Entgelte für", "Sonstige Privatrechtliche",
    "Kostenerstattungen", "Zinsen und ähnliche Erträge", "Aktivierte Eigenleistungen",
    "Sonstige ordentliche Erträge"
]

aufwendungen_cats = [
    "Personalaufwendungen", "Versorgungsaufwendungen",
    "Aufwendungen für Sach-", "Abschreibungen",
    "Zinsen und ähnliche Aufwendungen", "Transferaufwendungen",
    "Sonstige ordentliche Aufwendungen"
]

def clean_amount(val):
    if not val or val.strip() == '': return 0.0
    val = str(val).replace('.', '').replace(',', '.').strip()
    try:
        return float(val)
    except:
        return 0.0

for pdf_path in pdfs:
    print(f"Processing {pdf_path}...")
    
    # Get TOC using PyMuPDF to map pages to Ämter
    doc = fitz.open(pdf_path)
    toc = doc.get_toc()
    
    # Build list of (start_page, title) for Teilhaushalte (Ämter)
    amt_ranges = []
    for item in toc:
        level, title, page = item
        if "Amt " in title or "Dezernat" in title or "Teilhaushalt" in title:
            amt_ranges.append((page, title))
    
    amt_ranges.sort(key=lambda x: x[0])
    
    def get_amt_for_page(page_num):
        # find the last amt_range that starts before or at page_num
        current_amt = "Gesamthaushalt"
        for start_page, title in amt_ranges:
            if page_num >= start_page:
                current_amt = title
            else:
                break
        return current_amt

    try:
        with pdfplumber.open(pdf_path) as pdf:
            # We skip the first 100 pages as they usually contain the Gesamthaushalt, 
            # but actually we can just process all pages and check for "Teilergebnishaushalt"
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text and "Teilergebnishaushalt" in text:
                    amt_name = get_amt_for_page(i + 1) # 1-indexed for TOC
                    tables = page.extract_tables()
                    if tables:
                        for table in tables:
                            if len(table) < 5: continue
                            
                            headers = table[0]
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
                                                "Amt": amt_name,
                                                "Kategorie": category,
                                                "Typ": typ,
                                                "Betrag": val
                                            })
    except Exception as e:
        print(f"Error on {pdf_path}: {e}")

df = pd.DataFrame(all_data)

# Aggregate across categories per Amt/Year
df = df.groupby(["Jahr", "Amt", "Typ", "Kategorie"], as_index=False).agg({"Betrag": "sum"})

df.to_csv(DATA_DIR / "haushalt_heidelberg_aemter.csv", index=False)
print(f"Extracted detailed Amts-level data to {DATA_DIR / 'haushalt_heidelberg_aemter.csv'}")
