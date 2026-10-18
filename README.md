# 🏛️ Haushalt der Stadt Heidelberg — Interaktiver Explorer & PDF-Analyse-Pipeline (2017–2026)

Interaktive Datenanalyse-Plattform (Streamlit + Plotly + AgGrid) und automatisierte PDF-Extraktions-Pipeline für die offiziellen Doppelhaushaltspläne der **Stadt Heidelberg** über den Zehnjahreszeitraum **2017 bis 2026**.

Die Pipeline extrahiert und rekonsiliiert sämtliche **41 Ämter / Teilhaushalte** (`TH 01 Referat des Oberbürgermeisters` bis `TH FW Allgemeine Finanzwirtschaft`) inklusive aller untergeordneten **Erläuterungs-Einzelposten** (`6.239` Einzelpositionen) und gleicht diese exakt gegen den offiziellen **Gesamtergebnishaushalt** ab.

![Screenshot des Interaktiven Haushalts-Explorers](assets/screenshot.png)

---

## 📥 Offizielle Datenquellen & Download-Links (Stadt Heidelberg)

Sämtliche PDF-Quelldokumente in [`input/pdfs/`](input/pdfs/) wurden von den offiziellen Haushalts-Portalseiten der **Stadt Heidelberg** (`https://www.heidelberg.de`) über das Skript [`src/download_all.py`](src/download_all.py) heruntergeladen:

### 1. Übersicht der Portalseiten (Rathaus -> Finanzen -> Haushalt)

| Doppelhaushalt / Zeitraum | Offizielle Webseite der Stadt Heidelberg |
| :--- | :--- |
| **Haushalt Überblick** | [https://www.heidelberg.de/HD/Rathaus/Haushalt.html](https://www.heidelberg.de/HD/Rathaus/Haushalt.html) |
| **Doppelhaushalt 2025/2026** | [https://www.heidelberg.de/HD/Rathaus/doppelhaushalt+2025_2026.html](https://www.heidelberg.de/HD/Rathaus/doppelhaushalt+2025_2026.html) |
| **Doppelhaushalt 2023/2024** | [https://www.heidelberg.de/HD/Rathaus/doppelhaushalt+2023_2024.html](https://www.heidelberg.de/HD/Rathaus/doppelhaushalt+2023_2024.html) |
| **Doppelhaushalt 2021/2022** | [https://www.heidelberg.de/HD/Rathaus/doppelhaushalt+2021_2022.html](https://www.heidelberg.de/HD/Rathaus/doppelhaushalt+2021_2022.html) |
| **Doppelhaushalt 2019/2020** | [https://www.heidelberg.de/HD/Rathaus/doppelhaushalt+2019_2020.html](https://www.heidelberg.de/HD/Rathaus/doppelhaushalt+2019_2020.html) |
| **Doppelhaushalt 2017/2018** | [https://www.heidelberg.de/HD/Rathaus/doppelhaushalt+2017_2018.html](https://www.heidelberg.de/HD/Rathaus/doppelhaushalt+2017_2018.html) |

### 2. Heruntergeladene PDF-Dokumente (`input/pdfs/`) & Direkt-URLs

| Lokale Datei in `input/pdfs/` | Umfang / Größe | Abgedeckte Jahre in der Pipeline | Direkter Download-Link (`heidelberg.de`) |
| :--- | :--- | :--- | :--- |
| **`20_pdf_haushaltsplan 2025_2026_web.pdf`** | 1.402 Seiten (18,8 MB) | **2026** (Plan), **2025** (Plan), **2024** (Ansatz), **2023** (Ist-Ergebnis) | [PDF-Direktlink (2025/2026)](https://www.heidelberg.de/site/Heidelberg2021/get/documents_E-177182658/heidelberg/Objektdatenbank/20/PDF/Haushalt%202025%202026/20_pdf_haushaltsplan%202025_2026_web.pdf) |
| **`20_pdf_hh_2023_2024_Haushaltsplan.pdf`** | 1.384 Seiten (31,8 MB) | **2022** (Ansatz), **2021** (Ist-Ergebnis) *(sowie 2023/2024 Plan)* | [PDF-Direktlink (2023/2024)](https://www.heidelberg.de/site/Heidelberg2021/get/documents_E2049744753/heidelberg/Objektdatenbank/20/PDF/Haushalt%202023%202024/20_pdf_hh_2023_2024_Haushaltsplan.pdf) |
| **`20_pdf_hh_2021_2022_Haushaltsplan.pdf`** | 1.368 Seiten (31,3 MB) | **2020** (Ansatz), **2019** (Ist-Ergebnis) *(sowie 2021/2022 Plan)* | [PDF-Direktlink (2021/2022)](https://www.heidelberg.de/site/Heidelberg2021/get/documents_E1171315068/heidelberg/Objektdatenbank/20/PDF/20_pdf_hh_2021_2022_Haushaltsplan.pdf) |
| **`20_pdf_hh_2019_2020_Haushaltsplan.pdf`** | 1.242 Seiten (28,9 MB) | **2018** (Ansatz), **2017** (Ist-Ergebnis) *(sowie 2019/2020 Plan)* | [PDF-Direktlink (2019/2020)](https://www.heidelberg.de/site/Heidelberg2021/get/documents_E-141009777/heidelberg/Objektdatenbank/20/PDF/20_pdf_hh_2019_2020_Haushaltsplan.pdf) |
| `20_pdf_haushalt_2023_24_jahresabschluss_2024.pdf` | 14,5 MB | Jahresabschluss 2024 (Ergänzungsdokument) | [PDF-Direktlink (Jahresabschluss 2024)](https://www.heidelberg.de/site/Heidelberg2021/get/documents_E703536380/heidelberg/Objektdatenbank/20/PDF/Haushalt%202023%202024/20_pdf_haushalt_2023_24_jahresabschluss_2024.pdf) |
| `20_pdf_hh_2023_2024_jahresabschluss_2023.pdf` | 13,3 MB | Jahresabschluss 2023 (Ergänzungsdokument) | [PDF-Direktlink (Jahresabschluss 2023)](https://www.heidelberg.de/site/Heidelberg2021/get/documents_E-323802164/heidelberg/Objektdatenbank/20/PDF/Haushalt%202023%202024/20_pdf_hh_2023_2024_jahresabschluss_2023.pdf) |
| `20_pdf_hh_2019_2020_Haushaltbroschuere.pdf` | 15,9 MB | Bürgerbroschüre zum Doppelhaushalt 2019/2020 | [PDF-Direktlink (Broschüre 2019/2020)](https://www.heidelberg.de/site/Heidelberg2021/get/documents_E1092188529/heidelberg/Objektdatenbank/20/PDF/20_pdf_hh_2019_2020_Haushaltbroschuere.pdf) |
| `20_pdf_HH_2017_18_haushaltbroschuere_beschlossen.pdf` | 4,6 MB | Bürgerbroschüre zum Doppelhaushalt 2017/2018 | [PDF-Direktlink (Broschüre 2017/2018)](https://www.heidelberg.de/site/Heidelberg2021/get/documents_E-1402471440/heidelberg/Objektdatenbank/20/PDF/20_pdf_HH_2017_18_haushaltbroschuere_beschlossen.pdf) |
| `20_pdf_hh_2021_2022_Online-Anregungen der Bürgerinnen und Bürger zum Haushalt 21_22.pdf` | 0,6 MB | Bürgerbeteiligung / Online-Anregungen 2021/2022 | [PDF-Direktlink (Bürgeranregungen 2021/2022)](https://www.heidelberg.de/site/Heidelberg2021/get/documents_E-1423316900/heidelberg/Objektdatenbank/20/PDF/20_pdf_hh_2021_2022_Online-Anregungen%20der%20B%C3%BCrgerinnen%20und%20B%C3%BCrger%20zum%20Haushalt%2021_22.pdf) |

---

## 📂 Projektstruktur

```text
Heidelberg/
├── README.md                                   # Projektdokumentation & Quellenverzeichnis
├── app.py                                      # Root-Wrapper zum direkten Starten der Streamlit-App
├── input/
│   └── pdfs/                                   # Offizielle PDF-Haushaltspläne & Jahresabschlüsse der Stadt Heidelberg
│       ├── 20_pdf_haushaltsplan 2025_2026_web.pdf
│       ├── 20_pdf_hh_2023_2024_Haushaltsplan.pdf
│       ├── 20_pdf_hh_2021_2022_Haushaltsplan.pdf
│       ├── 20_pdf_hh_2019_2020_Haushaltsplan.pdf
│       ├── 20_pdf_haushalt_2023_24_jahresabschluss_2024.pdf
│       ├── 20_pdf_hh_2023_2024_jahresabschluss_2023.pdf
│       ├── 20_pdf_hh_2019_2020_Haushaltbroschuere.pdf
│       ├── 20_pdf_HH_2017_18_haushaltbroschuere_beschlossen.pdf
│       └── 20_pdf_hh_2021_2022_Online-Anregungen der Bürgerinnen und Bürger zum Haushalt 21_22.pdf
├── data/                                       # Extrahierte & rekonsiliierte CSV-Datensätze
│   ├── haushalt_heidelberg_deep.csv            # Hauptdatensatz: 6.239 Einzelposten (2017–2026, alle 41 Teilhaushalte)
│   ├── haushalt_heidelberg_aemter.csv          # Aggregierter Datensatz auf Ebene Amt × Kategorie (3.770 Zeilen)
│   ├── haushalt_heidelberg_real.csv            # Gesamtergebnishaushalt-Summen nach Kategorie (2017–2026)
│   ├── gesamtergebnishaushalt_2025_2026.csv    # Rohtabelle des Gesamtergebnishaushalts (S. 47 aus HH 2025/2026)
│   ├── haushalt_modell.csv                     # Synthetischer Demo-/Testdatensatz
│   └── toc.txt                                 # Ausgelesenes Inhaltsverzeichnis (PDF-Bookmarks)
├── src/                                        # Produktiver Quellcode (GUI & PDF-Extraktions-Pipeline)
│   ├── app.py                                  # Interaktive Streamlit-Applikation (3 Analyse-Tabs)
│   ├── download_all.py                         # Automatischer Downloader für alle PDF-Haushaltspläne von heidelberg.de
│   ├── extract_deep_2025.py                    # Vollständige PDF-Extraktion & Rekonsiliierung (Teilhaushalte + Erläuterungen)
│   ├── extract_all.py                          # Extraktion des Gesamtergebnishaushalts über alle 4 Doppelhaushalte
│   ├── extract_amts.py                         # Extraktion der Teilergebnishaushalte auf Amtsebene
│   ├── extract_pdf.py                          # Einzel-Extraktor für den Gesamtergebnishaushalt 2025/2026
│   └── get_toc.py                              # CLI-Hilfsskript zum Auslesen des PDF-Inhaltsverzeichnisses
├── assets/
│   └── screenshot.png                          # Aktueller Screenshot der Web-Applikation
└── tests/                                      # Automatisierte Browser-Tests (Playwright) & Hilfsskripte
    ├── test_app.py                             # Headless-Playwright-Test für das Streamlit-Frontend
    ├── test_click.py                           # Interaktionstest für Plotly-Kacheln
    ├── generate_mock_data.py                   # Generator für synthetische Testdaten
    ├── rewrite_app.py                          # Historisches Hilfsskript
    └── rewrite_tab2.py                         # Historisches Hilfsskript
```

---

## 🧮 Methodik & Daten-Rekonsiliierung (2023–2026)

Jeder der **41 Teilhaushalte** (`TH 01` bis `TH FW`) im Haushaltsplan enthält:
1. Eine **`I. Gesamtbudget`**-Übersichtstabelle (Zeilen 1–9: *Ordentliche Erträge*, Zeilen 11–18: *Ordentliche Aufwendungen*).
2. Darunterliegende **`Erläuterungen zu den ...`**-Tabellen mit den konkreten Einzelposten (sowie in einigen Ämtern wie `TH 80`, `TH 81` und `TH FW` vertiefende Untertabellen für einzelne Produktgruppen).

Das Extraktionsskript [`src/extract_deep_2025.py`](src/extract_deep_2025.py) liest beide Ebenen aus, ersetzt Sammelzeilen (z. B. `Leistungen für die Kultur- und Wissenschaftsförderung (PG ...)` in `TH 80` oder `Leistungen für den ÖPNV (PG ...)` in `TH 81`) durch ihre detaillierten Untertabellen ohne Doppelzählung und bildet für nicht einzeln aufgeschlüsselte Restbeträge eine transparente Ausgleichsposition `Weitere Positionen (...)`.

| Jahr | Offizielle Erträge (Gesamtergebnishaushalt) | Summe aller 41 Teilhaushalte (`deep.csv`) | Differenz Erträge | Offizielle Aufwendungen (Gesamtergebnishaushalt) | Summe aller 41 Teilhaushalte (`deep.csv`) | Differenz Aufwendungen |
| :---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **2023 (Ist)** | `839.257.283,16 €` | `839.257.283,32 €` | `+0,16 €` *(Rundung)* | `828.985.394,81 €` | `828.985.394,74 €` | `-0,07 €` *(Rundung)* |
| **2024 (Ansatz)** | `835.931.430,00 €` | `835.931.430,00 €` | **`0,00 €`** | `859.674.908,00 €` | `859.674.908,00 €` | **`0,00 €`** |
| **2025 (Plan)** | `808.911.010,00 €` | `808.911.010,00 €` | **`0,00 €`** | `907.753.195,00 €` | `907.753.195,00 €` | **`0,00 €`** |
| **2026 (Plan)** | `823.797.547,00 €` | `823.797.547,00 €` | **`0,00 €`** | `946.663.643,00 €` | `946.655.643,00 €` | **`-8.000,00 €`*** |

> \* **Hinweis zur 8.000-€-Differenz im Planjahr 2026**: Auf **Seite 1044** des offiziellen Haushaltsplans 2025/2026 (`TH 80 Amt für Wirtschaftsförderung und Wissenschaft`, Tabelle *Erläuterungen zu den Aufwendungen für Sach- und Dienstleistungen*) weist die gedruckte Summenzeile `3.094.900 €` aus, während die exakt 6 gedruckten Einzelzeilen (`1.448.000 + 235.100 + 178.900 + 82.900 + 1.072.000 + 70.000`) sich mathematisch auf `3.086.900 €` summieren.

---

## 🚀 Schnellstart & Bedienung

### 1. Interaktive GUI starten

Aus dem Projekt-Hauptverzeichnis:

```powershell
.\venv\Scripts\python.exe -m streamlit run app.py
```
*(Alternativ direkt über `.\venv\Scripts\python.exe -m streamlit run src/app.py`)*

Die Anwendung öffnet sich unter **`http://localhost:8501`** und bietet drei Analyse-Bereiche:
- **🧩 Tab 1 — Kachel-Ansicht & Drill-Down (Jahres-Fokus)**:
  - Umschaltbar zwischen **Treemap (Kacheln)** und **Sunburst (Ring)** sowie zwischen den Hierarchien `Amt ➔ Kategorie ➔ Einzelposten` und `Kategorie ➔ Amt ➔ Einzelposten`.
  - Top-15-Ämter-Ranking und Kategorien-Verteilung.
  - Interaktive **AgGrid-Tabelle** mit echter numerischer Sortierung, Gruppensummen und **CSV-Export**.
- **📈 Tab 2 — Zeitliche Entwicklung & Kostentreiber (2017–2026)**:
  - Frei wählbares **Basisjahr** und **Zieljahr** (`2017–2026`).
  - Ranking wahlweise nach **Absoluter Steigerung (€)** oder **Prozentualem Wachstum (%)** auf 3 Aggregationsebenen (`Teilhaushalt`, `Amt × Kategorie`, `Einzelposten`).
  - **Kaskadierender 10-Jahres-Zeitreihen-Explorer** (`Amt` ➔ `Kategorie` ➔ `Einzelposten`).
- **🏛️ Tab 3 — Gesamthaushalt & Ämter-Saldo-Vergleich**:
  - 10-Jahres-Entwicklung von Erträgen, Aufwendungen und ordentlichem Ergebnis (`2017–2026`).
  - **Netto-Zuschussbedarf / Überschuss je Amt** (`Ordentliche Erträge minus Ordentliche Aufwendungen`).
  - Offizielle **Abstimmungs-Tabelle** (`Gesamtergebnishaushalt` vs. `Teilhaushalte`).

### 2. PDF-Dokumente erneut herunterladen

```powershell
.\venv\Scripts\python.exe src\download_all.py
```

### 3. Daten-Extraktion aus den PDFs neu ausführen

```powershell
.\venv\Scripts\python.exe src\extract_deep_2025.py
.\venv\Scripts\python.exe src\extract_all.py
```
