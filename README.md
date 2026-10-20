# 🏛️ Haushalt & Finanzen der Stadt Heidelberg — Interaktiver Explorer & PDF-Analyse-Pipeline (2013–2029)

[![🌐 Live Interactive Report (GitHub Pages)](https://img.shields.io/badge/%F0%9F%8C%90_Live_Interactive_Report-GitHub_Pages_(Zero--Install)-1d4ed8?style=for-the-badge)](https://martinoschuetz.github.io/Heidelberg_Financials/)
[![📂 GitHub Repository](https://img.shields.io/badge/GitHub-martinoschuetz%2FHeidelberg__Financials-0f172a?style=for-the-badge&logo=github)](https://github.com/martinoschuetz/Heidelberg_Financials)

> **🌐 Direkt im Browser öffnen (ohne Python-Installation):**  
> 👉 **[https://martinoschuetz.github.io/Heidelberg_Financials/](https://martinoschuetz.github.io/Heidelberg_Financials/)**  
> *(Vollständiges interaktives HTML/Plotly-Dashboard mit allen 6 Analyse-Tabs, Jahres-/Amts-Filtern, Volltextsuche, Investitionsprogramm, Gemeinderat-Anträgen, automatisierter Finanz-Konsistenzprüfung und CSV-Export)*

Interaktive Datenanalyse-Plattform (Streamlit + Plotly + AgGrid sowie eigenständiges GitHub-Pages-Web-Dashboard) und automatisierte PDF-Extraktions-Pipeline für die offiziellen Doppelhaushaltspläne, Nachtragshaushalte, Jahresabschlüsse, Schlussbilanzen, Stellenpläne, Investitionsprogramme, Steuer-Hebesätze, Gemeinderat-Änderungsanträge und Beteiligungsberichte der **Stadt Heidelberg** über den Zeitraum **2013 bis 2029**.

Die Pipeline extrahiert und rekonsiliiert:
1. **Alle 41 Ämter / Teilhaushalte (2013–2026)** (`TH 01 Referat des Oberbürgermeisters` bis `TH FW Allgemeine Finanzwirtschaft`) inklusive aller untergeordneten **Erläuterungs-Einzelposten** (**`8.539` Einzelpositionen**, exakt auf **`0,00 €`** rekonsiliiert mit den Teilhaushalt-Summen in `haushalt_heidelberg_aemter.csv`).
2. Den am **18. Dezember 2025** beschlossenen **1. Nachtragshaushalt 2026** (`20_pdf_nachtragshaushalt_2026.pdf`, 238 Seiten) mit allen **41 Teilhaushalten** (exakt auf **`0,00 €`** rekonsiliiert mit dem Gesamtergebnishaushalt: `868.460.060 €` Erträge, `909.078.188 €` Aufwendungen, `-40.618.128 €` Ordentliches Ergebnis), allen **236 konkreten Konsolidierungsmaßnahmen & 5%-Zuschusskürzungen**, der **aktuellen Kämmerei-Prognose vom 16.10.2026** (`Gewerbesteuer 166,0 Mio. €`, Senkung des Kreditbedarfs um `-16,4 Mio. €` auf `55,4 Mio. €`) sowie der **Mittelfristigen Finanzplanung bis 2029**.
3. Die geprüften **Jahresabschlüsse 2023 & 2024** (`958` bzw. `966` Seiten) inklusive aller **39 Teilhaushalte** (`829,86 Mio. €` Erträge / `869,58 Mio. €` Aufwendungen in 2024), der **10-Jahres-Schlussbilanz (`2015–2024`, Bilanzsumme `1,780 Mrd. €`, Aktiva == Passiva für jedes Jahr)**, der **außerbilanziellen Vorbelastungen (`1,221 Mrd. €`)**, des **Stellenplans (`2.658,00 Planstellen`: `733,75 Beamte` + `1.924,25 Tarifbeschäftigte`)** sowie der **städtischen Gesellschaften & Eigenbetriebe**.
4. Das **Investitionsprogramm 2024–2029** (`29 Schwerpunktprojekte`, `494,68 Mio. €` Gesamtvolumen), die **Steuererträge & Hebesätze im Vergleich der 9 Stadtkreise in Baden-Württemberg** (`Grundsteuer B 190 v.H.` nach Bodenwertmodell-Reform, `Gewerbesteuer 400 v.H.`) sowie alle **359 Gemeinderat-Änderungsanträge zum Doppelhaushalt 2025/2026**.

![Screenshot des Interaktiven Haushalts-Explorers](assets/screenshot.png)

---

## 📥 Offizielle Datenquellen & Download-Links (Stadt Heidelberg)

Sämtliche **15 PDF-Quelldokumente** (~192 MB, über 9.000 Seiten) in [`input/pdfs/`](input/pdfs/) wurden von den offiziellen Finanz-Portalseiten der **Stadt Heidelberg** (`https://www.heidelberg.de`) über das Skript [`src/download_all.py`](src/download_all.py) heruntergeladen:

### 1. Übersicht der Portalseiten (Rathaus ➔ Haushalt & Finanzen)

| Finanz-Portal / Zeitraum | Offizielle Webseite der Stadt Heidelberg |
| :--- | :--- |
| **Haushalt & Finanzen (Hauptportal)** | [https://www.heidelberg.de/HD/Rathaus/Haushalt+_+Finanzen.html](https://www.heidelberg.de/HD/Rathaus/Haushalt+_+Finanzen.html) |
| **Prognose-Update Haushalt 2026 (16.10.2026)** | [https://www.heidelberg.de/HD/Presse/16_10_2026+haushalt+2026_+leichte+verbesserungen+erwartet.html](https://www.heidelberg.de/HD/Presse/16_10_2026+haushalt+2026_+leichte+verbesserungen+erwartet.html) |
| **Doppelhaushalt 2025/2026 & 1. Nachtrag 2026** | [https://www.heidelberg.de/HD/Rathaus/doppelhaushalt+2025_2026.html](https://www.heidelberg.de/HD/Rathaus/doppelhaushalt+2025_2026.html) |
| **Informationen zur Haushaltserstellung 2025/26** | [https://www.heidelberg.de/HD/Rathaus/informationen+zur+haushaltserstellung+2025_26.html](https://www.heidelberg.de/HD/Rathaus/informationen+zur+haushaltserstellung+2025_26.html) |
| **Doppelhaushalt 2023/2024 & Jahresabschlüsse** | [https://www.heidelberg.de/HD/Rathaus/doppelhaushalt+2023_2024.html](https://www.heidelberg.de/HD/Rathaus/doppelhaushalt+2023_2024.html) |
| **Doppelhaushalt 2021/2022** | [https://www.heidelberg.de/HD/Rathaus/doppelhaushalt+2021_2022.html](https://www.heidelberg.de/HD/Rathaus/doppelhaushalt+2021_2022.html) |
| **Doppelhaushalt 2019/2020** | [https://www.heidelberg.de/HD/Rathaus/doppelhaushalt+2019_2020.html](https://www.heidelberg.de/HD/Rathaus/doppelhaushalt+2019_2020.html) |
| **Doppelhaushalt 2017/2018** | [https://www.heidelberg.de/HD/Rathaus/doppelhaushalt+2017_2018.html](https://www.heidelberg.de/HD/Rathaus/doppelhaushalt+2017_2018.html) |
| **Doppelhaushalt 2015/2016** | [https://www.heidelberg.de/HD/Rathaus/doppelhaushalt+2015_2016.html](https://www.heidelberg.de/HD/Rathaus/doppelhaushalt+2015_2016.html) |
| **Doppelhaushalt 2013/2014** | [https://www.heidelberg.de/HD/Rathaus/Doppelhaushalt+2013_2014.html](https://www.heidelberg.de/HD/Rathaus/Doppelhaushalt+2013_2014.html) |
| **FAQ zum Haushalt & Städtische Unternehmen** | [https://www.heidelberg.de/HD/Rathaus/FAQ+zum+Haushalt.html](https://www.heidelberg.de/HD/Rathaus/FAQ+zum+Haushalt.html) |

---

## 📂 Projektstruktur & 16 Rekonsiliierte CSV-Datensätze

```text
Heidelberg_Financials/
├── README.md                                        # Projektdokumentation & Quellenverzeichnis
├── app.py                                           # Root-Wrapper zum direkten Starten der Streamlit-App
├── docs/
│   └── index.html                                   # Eigenständiges GitHub-Pages-Dashboard (6 Tabs, Plotly.js)
├── input/
│   └── pdfs/                                        # 15 offizielle PDF-Finanzdokumente der Stadt Heidelberg (~192 MB)
├── data/                                            # 16 extrahierte & zu 100% rekonsiliierte CSV-Datensätze
│   ├── haushalt_heidelberg_deep.csv                 # 8.539 Einzelposten (2013–2026, alle Teilhaushalte)
│   ├── haushalt_heidelberg_aemter.csv               # 5.164 Zeilen auf Ebene Amt × Kategorie (0,00 € Differenz zu deep.csv)
│   ├── haushalt_heidelberg_real.csv                 # 17-Jahres-Kategorienreihe (2013–2029, Ist & Finanzplanung)
│   ├── heidelberg_macro_2013_2029.csv               # 17-Jahres-Makrozeitreihe (Ergebnis, Cashflow, Schulden, Rücklagen, Steuern)
│   ├── heidelberg_nachtrag_2026_gesamt.csv          # 1. Nachtrag 2026: Gesamtergebnishaushalt (Bisher vs. Änderung vs. Neu)
│   ├── heidelberg_nachtrag_2026_aemter.csv          # 1. Nachtrag 2026: Alle 41 Teilhaushalte (0,00 € Differenz zu gesamt.csv)
│   ├── heidelberg_nachtrag_2026_massnahmen.csv      # 1. Nachtrag 2026: 236 konkrete Kürzungs- & Konsolidierungsmaßnahmen
│   ├── heidelberg_jahresabschluss_2024_aemter.csv   # Jahresabschluss 2024: Alle 39 Teilhaushalte (Plan vs. Ist 2024 & Ist 2023)
│   ├── heidelberg_bilanz_2015_2024.csv              # 10-Jahres-Schlussbilanz 2015–2024 (Aktiva == Passiva == Bilanzsumme)
│   ├── heidelberg_vorbelastungen.csv                # Außerbilanzielle Vorbelastungen 2023/2024 (1,221 Mrd. €)
│   ├── heidelberg_personal_stellen.csv              # Personal-Ist (2023/2024) & Stellenplan 2025/26 (exakt 2.658,00 VZÄ)
│   ├── heidelberg_beteiligungen.csv                 # Städtische Gesellschaften, Eigenbetriebe & Konzernverschuldung 2026
│   ├── heidelberg_steuern_kennzahlen.csv            # Steuerarten (inkl. Okt-2026-Prognose), FAG & Pro-Kopf-Kennzahlen (€/EW)
│   ├── heidelberg_hebesaetze_bw.csv                 # Hebesatz-Vergleich aller 9 Stadtkreise in Baden-Württemberg
│   ├── heidelberg_investitionen_2024_2029.csv       # 29 Schwerpunktprojekte im Investitionsprogramm 2024–2029
│   └── heidelberg_aenderungsantraege_2025_26.csv    # Alle 359 Gemeinderat-Änderungsanträge zum Doppelhaushalt 2025/2026
├── src/                                             # Produktiver Quellcode (GUI & PDF-Extraktions-Pipeline)
│   ├── app.py                                       # Interaktive Streamlit-Applikation (6 Analyse-Tabs)
│   ├── export_static_dashboard.py                   # Generator für das statische GitHub-Pages-Dashboard (docs/index.html)
│   ├── download_all.py                              # Automatischer Downloader für alle PDF-Finanzdokumente von heidelberg.de
│   ├── extract_deep_2025.py                         # 14-Jahres-PDF-Extraktion & Rekonsiliierung (Teilhaushalte + Erläuterungen)
│   └── extract_financial_reports.py                 # PyMuPDF-Extraktor für Nachtrag 2026, JA 2024, Bilanz, Steuern, Investitionen & Anträge
└── tests/                                           # Automatisierte Test-Suite (pytest + Streamlit AppTest + Playwright)
    ├── test_financial_consistency.py                # Mathematische & buchhalterische Konsistenztests über alle 16 CSVs
    ├── test_app.py                                  # Funktionale & Performance-Tests der Streamlit-App
    └── test_static_dashboard.py                     # Headless-Browser-E2E-Tests für docs/index.html
```

---

## 🚀 Schnellstart & Test-Suite ausführen

### 1. Interaktive GUI starten

```powershell
.\venv\Scripts\python.exe -m streamlit run app.py
```

### 2. Statisches HTML-Dashboard (`docs/index.html`) generieren

```powershell
.\venv\Scripts\python.exe src\export_static_dashboard.py
```

### 3. Vollständige Test-Suite (`pytest`) ausführen

```powershell
.\venv\Scripts\python.exe -m pytest tests -v
```
