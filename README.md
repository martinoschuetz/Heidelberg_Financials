# 🏛️ Haushalt & Finanzen der Stadt Heidelberg — Interaktiver Explorer & PDF-Analyse-Pipeline (2013–2029)

[![🌐 Live Interactive Report (GitHub Pages)](https://img.shields.io/badge/%F0%9F%8C%90_Live_Interactive_Report-GitHub_Pages_(Zero--Install)-1d4ed8?style=for-the-badge)](https://martinoschuetz.github.io/Heidelberg_Financials/)
[![📂 GitHub Repository](https://img.shields.io/badge/GitHub-martinoschuetz%2FHeidelberg__Financials-0f172a?style=for-the-badge&logo=github)](https://github.com/martinoschuetz/Heidelberg_Financials)

> **🌐 Direkt im Browser öffnen (ohne Python-Installation):**  
> 👉 **[https://martinoschuetz.github.io/Heidelberg_Financials/](https://martinoschuetz.github.io/Heidelberg_Financials/)**  
> *(Vollständiges interaktives HTML/Plotly-Dashboard mit allen 5 Analyse-Tabs, Jahres-/Amts-Filtern, Volltextsuche und CSV-Export)*

Interaktive Datenanalyse-Plattform (Streamlit + Plotly + AgGrid sowie eigenständiges GitHub-Pages-Web-Dashboard) und automatisierte PDF-Extraktions-Pipeline für die offiziellen Doppelhaushaltspläne, Nachtragshaushalte, Jahresabschlüsse, Schlussbilanzen, Stellenpläne und Beteiligungsberichte der **Stadt Heidelberg** über den Zeitraum **2013 bis 2029**.

Die Pipeline extrahiert und rekonsiliiert:
1. **Alle 41 Ämter / Teilhaushalte (2013–2026)** (`TH 01 Referat des Oberbürgermeisters` bis `TH FW Allgemeine Finanzwirtschaft`) inklusive aller untergeordneten **Erläuterungs-Einzelposten** (**`8.539` Einzelpositionen**).
2. Den am **18. Dezember 2025** beschlossenen **1. Nachtragshaushalt 2026** (`20_pdf_nachtragshaushalt_2026.pdf`, 238 Seiten) mit allen **249 konkreten Konsolidierungsmaßnahmen & 5%-Zuschusskürzungen** (`+42,04 Mio. €` Ergebnisverbesserung von `-82,65 Mio. €` auf `-40,62 Mio. €`; Cashflow-Drehung auf `+11,19 Mio. €`) sowie die **Mittelfristige Finanzplanung bis 2029**.
3. Die geprüften **Jahresabschlüsse 2023 & 2024** (`958` bzw. `966` Seiten) inklusive der **10-Jahres-Schlussbilanz (`2015–2024`, Bilanzsumme `1,780 Mrd. €`)**, der **außerbilanziellen Vorbelastungen (`1,221 Mrd. €`)**, des **Plan-Ist-Vergleichs 2024 je Amt**, des **Stellenplans (`2.658 Planstellen`)** sowie der **städtischen Gesellschaften & Eigenbetriebe (`Konzernverschuldung 719,4 Mio. €`)**.

![Screenshot des Interaktiven Haushalts-Explorers](assets/screenshot.png)

---

## 📥 Offizielle Datenquellen & Download-Links (Stadt Heidelberg)

Sämtliche **15 PDF-Quelldokumente** (~192 MB, über 9.000 Seiten) in [`input/pdfs/`](input/pdfs/) wurden von den offiziellen Finanz-Portalseiten der **Stadt Heidelberg** (`https://www.heidelberg.de`) über das Skript [`src/download_all.py`](src/download_all.py) heruntergeladen:

### 1. Übersicht der Portalseiten (Rathaus ➔ Finanzen ➔ Haushalt)

| Finanz-Portal / Zeitraum | Offizielle Webseite der Stadt Heidelberg |
| :--- | :--- |
| **Haushalt Überblick & Jahresabschlüsse** | [https://www.heidelberg.de/HD/Rathaus/haushalt.html](https://www.heidelberg.de/HD/Rathaus/haushalt.html) |
| **1. Nachtragshaushalt 2026 (Neu)** | [https://www.heidelberg.de/HD/Rathaus/nachtragshaushalt+2026.html](https://www.heidelberg.de/HD/Rathaus/nachtragshaushalt+2026.html) |
| **Doppelhaushalt 2025/2026 & Analysen** | [https://www.heidelberg.de/HD/Rathaus/haushalt+2025_2026.html](https://www.heidelberg.de/HD/Rathaus/haushalt+2025_2026.html) |
| **Archiv Vorherige Haushaltspläne** | [https://www.heidelberg.de/HD/Rathaus/vorherige+haushaltsplaene.html](https://www.heidelberg.de/HD/Rathaus/vorherige+haushaltsplaene.html) |
| **Doppelhaushalt 2023/2024** | [https://www.heidelberg.de/HD/Rathaus/doppelhaushalt+2023_2024.html](https://www.heidelberg.de/HD/Rathaus/doppelhaushalt+2023_2024.html) |
| **Doppelhaushalt 2021/2022** | [https://www.heidelberg.de/HD/Rathaus/doppelhaushalt+2021_2022.html](https://www.heidelberg.de/HD/Rathaus/doppelhaushalt+2021_2022.html) |
| **Doppelhaushalt 2019/2020** | [https://www.heidelberg.de/HD/Rathaus/doppelhaushalt+2019_2020.html](https://www.heidelberg.de/HD/Rathaus/doppelhaushalt+2019_2020.html) |
| **Doppelhaushalt 2017/2018** | [https://www.heidelberg.de/HD/Rathaus/doppelhaushalt+2017_2018.html](https://www.heidelberg.de/HD/Rathaus/doppelhaushalt+2017_2018.html) |
| **Doppelhaushalt 2015/2016** | [https://www.heidelberg.de/HD/Rathaus/doppelhaushalt+2015_2016.html](https://www.heidelberg.de/HD/Rathaus/doppelhaushalt+2015_2016.html) |

### 2. Heruntergeladene PDF-Dokumente (`input/pdfs/`) & Direkt-URLs

| Lokale Datei in `input/pdfs/` | Umfang / Größe | Abgedeckte Inhalte & Jahre in der Pipeline | Direkter Download-Link (`heidelberg.de`) |
| :--- | :--- | :--- | :--- |
| **`20_pdf_nachtragshaushalt_2026.pdf`** *(Neu)* | 238 Seiten (5,6 MB) | **1. Nachtragshaushalt 2026** (Bisher vs. Änderung vs. Neu für alle 38 TH + 249 Einzelmaßnahmen) & **Mittelfristige Finanzplanung 2025–2029** | [PDF-Direktlink (Nachtrag 2026)](https://www.heidelberg.de/site/Heidelberg2021/get/documents_E1400664606/heidelberg/Objektdatenbank/20/PDF/Haushalt%202025%202026/20_pdf_nachtragshaushalt_2026.pdf) |
| **`20_pdf_haushaltsplan 2025_2026_web.pdf`** | 1.402 Seiten (18,8 MB) | **2026** (Plan), **2025** (Plan), **2024** (Ansatz), **2023** (Ist) sowie **Stellenplan 2025/26** (S. 1129–1142) & **Wirtschaftspläne Beteiligungen** (S. 1197–1402) | [PDF-Direktlink (HH 2025/2026)](https://www.heidelberg.de/site/Heidelberg2021/get/documents_E-177182658/heidelberg/Objektdatenbank/20/PDF/Haushalt%202025%202026/20_pdf_haushaltsplan%202025_2026_web.pdf) |
| **`20_pdf_haushalt_2023_24_jahresabschluss_2024.pdf`** *(Neu)* | 966 Seiten (14,5 MB) | Geprüfter **Jahresabschluss 2024** (Plan vs. Ist aller Ämter, Personal-Ist 2023/2024, **10-Jahres-Zeitreihen 2015–2024** für Ergebnis-, Finanzrechnung & **Schlussbilanz**, **Vorbelastungen 1,22 Mrd. €**) | [PDF-Direktlink (JA 2024)](https://www.heidelberg.de/site/Heidelberg2021/get/documents_E703536380/heidelberg/Objektdatenbank/20/PDF/Haushalt%202023%202024/20_pdf_haushalt_2023_24_jahresabschluss_2024.pdf) |
| **`20_pdf_hh_2023_2024_jahresabschluss_2023.pdf`** *(Neu)* | 958 Seiten (13,3 MB) | Geprüfter **Jahresabschluss 2023** (Ergebnisrechnung, Finanzrechnung, Bilanz & Vorbelastungen 2023) | [PDF-Direktlink (JA 2023)](https://www.heidelberg.de/site/Heidelberg2021/get/documents_E-323802164/heidelberg/Objektdatenbank/20/PDF/Haushalt%202023%202024/20_pdf_hh_2023_2024_jahresabschluss_2023.pdf) |
| **`20_pdf_hh_2023_2024_Haushaltsplan.pdf`** | 1.384 Seiten (31,8 MB) | **2022** (Ansatz), **2021** (Ist-Ergebnis) *(sowie 2023/2024 Plan)* | [PDF-Direktlink (HH 2023/2024)](https://www.heidelberg.de/site/Heidelberg2021/get/documents_E2049744753/heidelberg/Objektdatenbank/20/PDF/Haushalt%202023%202024/20_pdf_hh_2023_2024_Haushaltsplan.pdf) |
| **`20_pdf_hh_2021_2022_Haushaltsplan.pdf`** | 1.368 Seiten (31,3 MB) | **2020** (Ansatz), **2019** (Ist-Ergebnis) *(sowie 2021/2022 Plan)* | [PDF-Direktlink (HH 2021/2022)](https://www.heidelberg.de/site/Heidelberg2021/get/documents_E1171315068/heidelberg/Objektdatenbank/20/PDF/20_pdf_hh_2021_2022_Haushaltsplan.pdf) |
| **`20_pdf_hh_2019_2020_Haushaltsplan.pdf`** | 1.242 Seiten (28,9 MB) | **2018** (Ansatz), **2017** (Ist-Ergebnis) *(sowie 2019/2020 Plan)* | [PDF-Direktlink (HH 2019/2020)](https://www.heidelberg.de/site/Heidelberg2021/get/documents_E-141009777/heidelberg/Objektdatenbank/20/PDF/20_pdf_hh_2019_2020_Haushaltsplan.pdf) |
| **`20_pdf_hh_2015_16_Haushaltsplanentwurf.pdf`** *(Neu)* | 1.400 Seiten (25,7 MB) | **2016** (Plan), **2015** (Plan), **2014** (Ansatz), **2013** (Ist-Ergebnis) für alle 38 Teilhaushalte | [PDF-Direktlink (HH 2015/2016)](https://www.heidelberg.de/site/Heidelberg2021/get/documents_E-1892877613/heidelberg/Objektdatenbank/20/PDF/20_pdf_hh_2015_16_Haushaltsplanentwurf.pdf) |
| **`20_pdf_hh_2020_11_17_nachtragshaushalt_endgueltig.pdf`** *(Neu)* | 1,9 MB | Nachtragshaushalt 2020 (COVID-19-Anpassungen) | [PDF-Direktlink (Nachtrag 2020)](https://www.heidelberg.de/site/Heidelberg2021/get/documents_E-654759116/heidelberg/Objektdatenbank/20/PDF/20_pdf_hh_2020_11_17_nachtragshaushalt_endgueltig.pdf) |
| **`20_pdf_Haushalt_25_26_Gesamtuebersicht_Aenderungsantraege_Stand_22_05_2025.pdf`** *(Neu)* | 47 Seiten (0,9 MB) | Gesamtübersicht aller Fraktions-Änderungsanträge zum Doppelhaushalt 2025/2026 | [PDF-Direktlink (Änderungsanträge 25/26)](https://www.heidelberg.de/site/Heidelberg2021/get/documents_E-1598027856/heidelberg/Objektdatenbank/20/PDF/Haushalt%202025%202026/20_pdf_Haushalt_25_26_Gesamtuebersicht_Aenderungsantraege_Stand_22_05_2025.pdf) |
| **`20_pdf_Haushalt_Grafik_Ausgaben_2025-26_Steigerungen_durch_Bundesbeschluesse.pdf`** *(Neu)* | 1 Seite (0,5 MB) | Städtische Analyse: `+80 Mio. €` (2025) bzw. `+90 Mio. €` (2026) Mehrausgaben durch Bundesgesetze (BTHG, Kita, Ganztagsschule) | [PDF-Direktlink (Grafik Bundesbeschlüsse)](https://www.heidelberg.de/site/Heidelberg2021/get/documents_E1376761723/heidelberg/Objektdatenbank/20/PDF/Haushalt%202025%202026/20_pdf_Haushalt_Grafik_Ausgaben_2025-26_Steigerungen_durch_Bundesbeschluesse.pdf) |
| **`20_pdf_Haushalt_Grafik_Bereiche_mit_besonderen_Einnahmeverlusten.pdf`** *(Neu)* | 1 Seite (0,4 MB) | Städtische Analyse: `-23 Mio. €` Gewerbesteuer-Ausfall & `-30 Mio. €` Zensus-2022-Verlust bei Schlüsselzuweisungen | [PDF-Direktlink (Grafik Einnahmeverluste)](https://www.heidelberg.de/site/Heidelberg2021/get/documents_E192563408/heidelberg/Objektdatenbank/20/PDF/Haushalt%202025%202026/20_pdf_Haushalt_Grafik_Bereiche_mit_besonderen_Einnahmeverlusten.pdf) |
| `20_pdf_hh_2019_2020_Haushaltbroschuere.pdf` | 15,9 MB | Bürgerbroschüre zum Doppelhaushalt 2019/2020 | [PDF-Direktlink (Broschüre 2019/2020)](https://www.heidelberg.de/site/Heidelberg2021/get/documents_E1092188529/heidelberg/Objektdatenbank/20/PDF/20_pdf_hh_2019_2020_Haushaltbroschuere.pdf) |
| `20_pdf_HH_2017_18_haushaltbroschuere_beschlossen.pdf` | 4,6 MB | Bürgerbroschüre zum Doppelhaushalt 2017/2018 | [PDF-Direktlink (Broschüre 2017/2018)](https://www.heidelberg.de/site/Heidelberg2021/get/documents_E-1402471440/heidelberg/Objektdatenbank/20/PDF/20_pdf_HH_2017_18_haushaltbroschuere_beschlossen.pdf) |
| `20_pdf_hh_2021_2022_Online-Anregungen der Bürgerinnen und Bürger zum Haushalt 21_22.pdf` | 0,6 MB | Bürgerbeteiligung / Online-Anregungen 2021/2022 | [PDF-Direktlink (Bürgeranregungen 2021/2022)](https://www.heidelberg.de/site/Heidelberg2021/get/documents_E-1423316900/heidelberg/Objektdatenbank/20/PDF/20_pdf_hh_2021_2022_Online-Anregungen%20der%20B%C3%BCrgerinnen%20und%20B%C3%BCrger%20zum%20Haushalt%2021_22.pdf) |

---

## 📂 Projektstruktur

```text
Heidelberg_Financials/
├── README.md                                        # Projektdokumentation & Quellenverzeichnis
├── app.py                                           # Root-Wrapper zum direkten Starten der Streamlit-App
├── input/
│   └── pdfs/                                        # 15 offizielle PDF-Finanzdokumente der Stadt Heidelberg (~192 MB)
├── data/                                            # Extrahierte & rekonsiliierte CSV-Datensätze
│   ├── haushalt_heidelberg_deep.csv                 # 8.539 Einzelposten (2013–2026, alle 41 Teilhaushalte)
│   ├── haushalt_heidelberg_aemter.csv               # 5.159 Zeilen auf Ebene Amt × Kategorie (2013–2026)
│   ├── haushalt_heidelberg_real.csv                 # 17-Jahres-Kategorienreihe (2013–2029, Ist & Finanzplanung)
│   ├── heidelberg_macro_2013_2029.csv               # 17-Jahres-Makrozeitreihe (Ergebnis, Cashflow, Schulden, Rücklagen, Steuern)
│   ├── heidelberg_nachtrag_2026_gesamt.csv          # 1. Nachtrag 2026: Gesamtergebnishaushalt (Bisher vs. Änderung vs. Neu)
│   ├── heidelberg_nachtrag_2026_aemter.csv          # 1. Nachtrag 2026: 455 Zeilen Teilhaushalts-Änderungen
│   ├── heidelberg_nachtrag_2026_massnahmen.csv      # 1. Nachtrag 2026: 249 konkrete Kürzungs- & Konsolidierungsmaßnahmen
│   ├── heidelberg_jahresabschluss_2024_aemter.csv   # Jahresabschluss 2024: 673 Zeilen Plan-vs.-Ist-Vergleich je Amt
│   ├── heidelberg_bilanz_2015_2024.csv              # 10-Jahres-Schlussbilanz 2015–2024 (250 Zeilen Aktiva & Passiva)
│   ├── heidelberg_vorbelastungen.csv                # Außerbilanzielle Vorbelastungen 2023/2024 (1,221 Mrd. €)
│   ├── heidelberg_personal_stellen.csv              # Personal-Ist (2023/2024) & Stellenplan 2025/26 (Beamte & Tarif)
│   └── heidelberg_beteiligungen.csv                 # Städtische Gesellschaften, Eigenbetriebe & Konzernverschuldung 2026
├── src/                                             # Produktiver Quellcode (GUI & PDF-Extraktions-Pipeline)
│   ├── app.py                                       # Interaktive Streamlit-Applikation (5 Analyse-Tabs)
│   ├── download_all.py                              # Automatischer Downloader für alle PDF-Finanzdokumente von heidelberg.de
│   ├── extract_deep_2025.py                         # 14-Jahres-PDF-Extraktion & Rekonsiliierung (Teilhaushalte + Erläuterungen)
│   ├── extract_financial_reports.py                 # Extraktor für Nachtrag 2026, Jahresabschluss 2024, Bilanz, Personal & Konzern
│   ├── extract_all.py                               # Extraktion des Gesamtergebnishaushalts
│   ├── extract_amts.py                              # Extraktion der Teilergebnishaushalte auf Amtsebene
│   ├── extract_pdf.py                               # Einzel-Extraktor für den Gesamtergebnishaushalt 2025/2026
│   └── get_toc.py                                   # CLI-Hilfsskript zum Auslesen des PDF-Inhaltsverzeichnisses
├── assets/
│   └── screenshot.png                               # Aktueller Screenshot der Web-Applikation
└── tests/                                           # Automatisierte Browser-Tests (Playwright)
```

---

## 🚀 Schnellstart & 5 Analyse-Tabs

### 1. Interaktive GUI starten

```powershell
.\venv\Scripts\python.exe -m streamlit run app.py
```

Die Anwendung öffnet sich unter **`http://localhost:8501`** und bietet **fünf Analyse-Tabs**:
1. **🧩 Tab 1 — Kachel-Ansicht & Drill-Down (2013–2026)**:
   - Umschaltbar zwischen **Treemap (Kacheln)** und **Sunburst (Ring)** sowie zwischen den Hierarchien `Amt ➔ Kategorie ➔ Einzelposten` und `Kategorie ➔ Amt ➔ Einzelposten` über **14 Haushaltsjahre (`2013–2026`)**.
   - Top-15-Ämter-Ranking, Kategorien-Verteilung und interaktive **AgGrid-Tabelle** mit CSV-Export.
2. **📈 Tab 2 — Zeitreihen & Kostentreiber (2013–2026)**:
   - Frei wählbares **Basisjahr** und **Zieljahr** (`2013–2026`), sortierbar nach **Absoluter Steigerung (€)** oder **Prozentualem Wachstum (%)** auf 3 Ebenen (`Teilhaushalt`, `Amt × Kategorie`, `Einzelposten`).
   - **Kaskadierender 14-Jahres-Zeitreihen-Explorer** (`Amt` ➔ `Kategorie` ➔ `Einzelposten`).
3. **🏛️ Tab 3 — Gesamthaushalt (2013–2029) & Ämter-Saldo**:
   - **17-Jahres-Gesamtschau (`2013–2029`)** aus geprüften Jahresabschlüssen (`2013–2024`), Haushaltsplan `2025`, `1. Nachtrag 2026` und `Finanzplanung 2027–2029`.
   - Gegenüberstellung von **laufendem Cashflow vs. Investitionsauszahlungen** sowie **Kernhaushalts-Schulden (`130 Mio. €` ➔ `548 Mio. €`) vs. Ergebnisrücklagen-Abbau**.
4. **🚨 Tab 4 — 1. Nachtragshaushalt 2026 & Finanzplanung bis 2029**:
   - Analyse des am **18.12.2025** beschlossenen Konsolidierungspakets (`+42,04 Mio. €` Ergebnisverbesserung, `+11,19 Mio. €` positiver Cashflow).
   - Durchsuchbare Tabelle aller **249 konkreten Kürzungs- & Änderungsmaßnahmen** (inkl. Filter für die pauschale **5%-Kürzung freiwilliger Zuschüsse**) sowie Visualisierung der strukturellen Defizitursachen (`+80/+90 Mio. €` Bundesgesetze, `-30 Mio. €` Zensus-Effekt, `-23 Mio. €` Gewerbesteuer-Einbruch).
5. **🏦 Tab 5 — Bilanz (2015–2024), Jahresabschluss 2024, Stellenplan & Konzern**:
   - **10-Jahres-Schlussbilanz (`2015–2024`)**: Entwicklung von `Aktiva` (`Sachvermögen 1,382 Mrd. €`, `Finanzvermögen 359,8 Mio. €`, Abschmelzen der `Liquiden Mittel` auf `0 €` Ende 2024) und `Passiva` (`Eigenkapital 1,007 Mrd. € [56,6%]`, `Verbindlichkeiten 431,1 Mio. €`).
   - **Außerbilanzielle Vorbelastungen (`1,221 Mrd. €`)**: `Bürgschaften (634,3 Mio. €)`, `KVBW-Pensionen (279,9 Mio. €)`, `ZVK (148,8 Mio. €)`, `Beihilfe (113,2 Mio. €)`.
   - **Konzernverschuldung (`719,4 Mio. €` Ende 2026)** & Wirtschaftsdaten der **städtischen Gesellschaften & Eigenbetriebe** (`SWH`, `GGH`, `SBH`, `ETO`, `ESB`, `Bahnstadt`, `HKK`, `Zoo`, `TP`).
   - **Geprüfter Jahresabschluss 2024 (Plan vs. Ist je Amt)** & **Stellenplan (`2.658 Planstellen`: `733,75 Beamte` + `1.924,25 Tarifbeschäftigte`)**.

### 2. Daten-Extraktion aus allen PDFs neu ausführen

```powershell
.\venv\Scripts\python.exe src\extract_deep_2025.py
.\venv\Scripts\python.exe src\extract_financial_reports.py
```
