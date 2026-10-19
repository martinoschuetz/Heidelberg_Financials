"""
Export a standalone, zero-backend interactive HTML financial report & dashboard
for GitHub Pages (`docs/index.html`).

Reproduces all 5 analytical tabs of `src/app.py` (2013-2029) directly in the browser
using Plotly.js and interactive client-side filtering, sorting, and CSV export.
"""
import json
from pathlib import Path
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
DOCS_DIR = ROOT_DIR / "docs"


def load_json_records(filename: str) -> list:
    fpath = DATA_DIR / filename
    if not fpath.exists():
        return []
    df = pd.read_csv(fpath, encoding="utf-8")
    return json.loads(df.to_json(orient="records", force_ascii=False))


def build_static_dashboard() -> Path:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    (DOCS_DIR / ".nojekyll").write_text("", encoding="utf-8")

    df_deep = pd.read_csv(DATA_DIR / "haushalt_heidelberg_deep.csv", encoding="utf-8")
    df_deep = df_deep[df_deep["Amt"].notna() & (df_deep["Amt"] != "Unbekanntes Amt")].copy()
    df_deep["Jahr"] = df_deep["Jahr"].astype(int)
    df_deep["Betrag"] = pd.to_numeric(df_deep["Betrag"], errors="coerce").fillna(0.0).round(2)
    df_deep["Kategorie"] = df_deep["Kategorie"].fillna("Sonstige").astype(str).str.strip().replace({"": "Sonstige"})
    df_deep["Sub_Kategorie"] = df_deep["Sub_Kategorie"].fillna("Allgemein").astype(str).str.strip().replace({"": "Allgemein"})

    # Compact array representation for deep rows: [Jahr, Amt_idx, Kat_idx, Sub_idx, Typ_idx, Betrag]
    aemter = sorted(df_deep["Amt"].unique().tolist())
    kats = sorted(df_deep["Kategorie"].unique().tolist())
    subs = sorted(df_deep["Sub_Kategorie"].unique().tolist())
    typen = ["Aufwendungen", "Erträge"]

    amt_map = {v: i for i, v in enumerate(aemter)}
    kat_map = {v: i for i, v in enumerate(kats)}
    sub_map = {v: i for i, v in enumerate(subs)}
    typ_map = {v: i for i, v in enumerate(typen)}

    compact_rows = [
        [
            int(r.Jahr),
            amt_map[r.Amt],
            kat_map[r.Kategorie],
            sub_map[r.Sub_Kategorie],
            typ_map.get(r.Typ, 0),
            float(r.Betrag),
        ]
        for r in df_deep.itertuples(index=False)
    ]

    payload = {
        "aemter": aemter,
        "kats": kats,
        "subs": subs,
        "typen": typen,
        "rows": compact_rows,
        "macro": load_json_records("heidelberg_macro_2013_2029.csv"),
        "nh_gesamt": load_json_records("heidelberg_nachtrag_2026_gesamt.csv"),
        "nh_aemter": load_json_records("heidelberg_nachtrag_2026_aemter.csv"),
        "nh_massnahmen": load_json_records("heidelberg_nachtrag_2026_massnahmen.csv"),
        "ja2024_aemter": load_json_records("heidelberg_jahresabschluss_2024_aemter.csv"),
        "personal": load_json_records("heidelberg_personal_stellen.csv"),
        "bilanz": load_json_records("heidelberg_bilanz_2015_2024.csv"),
        "vorbelastungen": load_json_records("heidelberg_vorbelastungen.csv"),
        "beteiligungen": load_json_records("heidelberg_beteiligungen.csv"),
    }

    data_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))

    html = f"""<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>🏛️ Haushalt & Finanzen der Stadt Heidelberg — Interaktiver Report (2013–2029)</title>
  <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
  <style>
    :root {{
      --bg: #f8fafc;
      --card: #ffffff;
      --border: #e2e8f0;
      --text: #0f172a;
      --muted: #475569;
      --primary: #1d4ed8;
      --primary-light: #eff6ff;
      --red: #dc2626;
      --green: #16a34a;
      --teal: #0d9488;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background: var(--bg);
      color: var(--text);
      display: flex;
      min-height: 100vh;
    }}
    /* Sidebar */
    .sidebar {{
      width: 310px;
      background: #ffffff;
      border-right: 1px solid var(--border);
      padding: 20px 18px;
      flex-shrink: 0;
      position: sticky;
      top: 0;
      height: 100vh;
      overflow-y: auto;
    }}
    .sidebar h2 {{
      font-size: 1.15rem;
      margin: 0 0 14px 0;
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .control-group {{
      margin-bottom: 14px;
    }}
    .control-group label {{
      display: block;
      font-size: 0.8rem;
      font-weight: 600;
      color: var(--muted);
      margin-bottom: 5px;
    }}
    select, input[type="text"], input[type="number"] {{
      width: 100%;
      padding: 8px 10px;
      border: 1px solid var(--border);
      border-radius: 6px;
      font-size: 0.88rem;
      background: #fff;
      color: var(--text);
    }}
    .radio-pill-group {{
      display: flex;
      gap: 6px;
      flex-wrap: wrap;
    }}
    .radio-pill {{
      flex: 1;
      text-align: center;
      padding: 7px 8px;
      font-size: 0.8rem;
      font-weight: 600;
      border: 1px solid var(--border);
      border-radius: 6px;
      cursor: pointer;
      background: #f8fafc;
      user-select: none;
    }}
    .radio-pill.active {{
      background: var(--primary);
      color: #fff;
      border-color: var(--primary);
    }}
    .sidebar-footer {{
      margin-top: 18px;
      padding-top: 14px;
      border-top: 1px solid var(--border);
      font-size: 0.78rem;
      color: var(--muted);
      line-height: 1.45;
    }}
    .sidebar-footer a {{
      color: var(--primary);
      text-decoration: none;
      font-weight: 600;
    }}
    /* Main Content */
    .main {{
      flex: 1;
      padding: 24px 28px 48px 28px;
      max-width: calc(100vw - 310px);
      overflow-x: hidden;
    }}
    .header-title {{
      margin: 0 0 6px 0;
      font-size: 1.65rem;
      font-weight: 800;
    }}
    .header-sub {{
      margin: 0 0 18px 0;
      color: var(--muted);
      font-size: 0.92rem;
      line-height: 1.5;
    }}
    /* KPI Grid */
    .kpi-grid {{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 14px;
      margin-bottom: 20px;
    }}
    .kpi-card {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 14px 16px;
      box-shadow: 0 1px 2px rgba(0,0,0,0.03);
    }}
    .kpi-label {{
      font-size: 0.78rem;
      font-weight: 600;
      color: var(--muted);
      margin-bottom: 4px;
    }}
    .kpi-value {{
      font-size: 1.35rem;
      font-weight: 800;
      color: var(--text);
    }}
    .kpi-delta {{
      font-size: 0.76rem;
      margin-top: 5px;
      font-weight: 600;
    }}
    .delta-pos {{ color: var(--green); }}
    .delta-neg {{ color: var(--red); }}
    .delta-neutral {{ color: var(--muted); }}
    /* Tabs */
    .tabs {{
      display: flex;
      gap: 6px;
      border-bottom: 2px solid var(--border);
      margin-bottom: 20px;
      flex-wrap: wrap;
    }}
    .tab-btn {{
      padding: 10px 16px;
      font-size: 0.88rem;
      font-weight: 700;
      border: none;
      background: transparent;
      color: var(--muted);
      cursor: pointer;
      border-bottom: 3px solid transparent;
      margin-bottom: -2px;
      transition: all 0.15s;
    }}
    .tab-btn:hover {{
      color: var(--primary);
    }}
    .tab-btn.active {{
      color: var(--primary);
      border-bottom-color: var(--primary);
      background: var(--primary-light);
      border-radius: 6px 6px 0 0;
    }}
    .tab-panel {{
      display: none;
    }}
    .tab-panel.active {{
      display: block;
    }}
    .card {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 16px 18px;
      margin-bottom: 18px;
      box-shadow: 0 1px 2px rgba(0,0,0,0.02);
    }}
    .grid-2 {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
      margin-bottom: 18px;
    }}
    .toolbar-row {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 12px;
      margin-bottom: 14px;
      align-items: end;
    }}
    .info-banner {{
      background: #eff6ff;
      border-left: 4px solid var(--primary);
      padding: 12px 16px;
      border-radius: 6px;
      font-size: 0.88rem;
      line-height: 1.5;
      margin-bottom: 16px;
    }}
    .caption-banner {{
      background: #f8fafc;
      border: 1px solid var(--border);
      padding: 8px 12px;
      border-radius: 6px;
      font-size: 0.8rem;
      color: var(--muted);
      margin-bottom: 12px;
    }}
    /* Data Tables */
    .table-wrap {{
      max-height: 460px;
      overflow-y: auto;
      border: 1px solid var(--border);
      border-radius: 8px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.83rem;
    }}
    th {{
      position: sticky;
      top: 0;
      background: #f1f5f9;
      color: var(--text);
      text-align: left;
      padding: 9px 10px;
      font-weight: 700;
      border-bottom: 1px solid var(--border);
      cursor: pointer;
      user-select: none;
    }}
    td {{
      padding: 7px 10px;
      border-bottom: 1px solid #f1f5f9;
    }}
    tr:hover td {{
      background: #f8fafc;
    }}
    .num {{
      text-align: right;
      font-variant-numeric: tabular-nums;
      font-weight: 600;
    }}
    .btn {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 8px 13px;
      background: var(--primary);
      color: #fff;
      border: none;
      border-radius: 6px;
      font-size: 0.82rem;
      font-weight: 600;
      cursor: pointer;
      text-decoration: none;
    }}
    .btn:hover {{ opacity: 0.92; }}
    @media (max-width: 1024px) {{
      body {{ flex-direction: column; }}
      .sidebar {{ width: 100%; height: auto; position: static; border-right: none; border-bottom: 1px solid var(--border); }}
      .main {{ max-width: 100vw; padding: 16px; }}
      .kpi-grid, .grid-2 {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <!-- SIDEBAR -->
  <aside class="sidebar">
    <h2>🏛️ Haushalt-Filter</h2>
    <div class="control-group">
      <label for="selYear">Haushaltsjahr auswählen (Teilhaushalte)</label>
      <select id="selYear"></select>
    </div>
    <div class="control-group">
      <label>Haushaltsseite (Typ)</label>
      <div class="radio-pill-group" id="pillType">
        <div class="radio-pill active" data-val="Aufwendungen">Aufwendungen</div>
        <div class="radio-pill" data-val="Erträge">Erträge</div>
      </div>
    </div>
    <div class="control-group">
      <label>Hierarchie-Gruppierung</label>
      <select id="selHierarchy">
        <option value="amt_first">Amt ➔ Kategorie ➔ Einzelposten</option>
        <option value="kat_first">Kategorie ➔ Amt ➔ Einzelposten</option>
      </select>
    </div>
    <div class="control-group">
      <label>Diagramm-Typ (Tab 1)</label>
      <div class="radio-pill-group" id="pillChart">
        <div class="radio-pill active" data-val="treemap">Treemap (Kacheln)</div>
        <div class="radio-pill" data-val="sunburst">Sunburst (Ring)</div>
      </div>
    </div>
    <div class="control-group">
      <label for="selAmt">Amt / Teilhaushalt filtern</label>
      <select id="selAmt">
        <option value="ALL">Alle 41 Teilhaushalte</option>
      </select>
    </div>
    <div class="control-group">
      <label for="inpSearch">🔍 Volltextsuche (Posten / Amt / Kat.)</label>
      <input type="text" id="inpSearch" placeholder="z.B. Gewerbesteuer, Jugend, Kita..." />
    </div>

    <div class="sidebar-footer">
      <strong>Datenbasis (15 PDFs, 2013–2029):</strong><br/>
      • Doppelhaushalte <strong>2013–2026</strong> (41 Teilhaushalte, 8.539 Positionen)<br/>
      • <strong>1. Nachtragshaushalt 2026</strong> (18.12.2025) &amp; Finanzplan bis 2029<br/>
      • <strong>Jahresabschlüsse 2023 &amp; 2024</strong> inkl. 10-Jahres-Bilanz (1,78 Mrd. €)<br/><br/>
      🔗 <a href="https://github.com/martinoschuetz/Heidelberg_Financials" target="_blank">GitHub Repository &amp; CSV-Daten</a><br/>
      🏛️ <a href="https://www.heidelberg.de/HD/Rathaus/haushalt.html" target="_blank">Offizielles Portal heidelberg.de</a>
    </div>
  </aside>

  <!-- MAIN CONTENT -->
  <main class="main">
    <h1 class="header-title">🏛️ Haushalt &amp; Finanzen der Stadt Heidelberg — Explorer (2013–2029)</h1>
    <p class="header-sub">
      Interaktive Gesamtanalyse aller <strong>41 Teilhaushalte (2013–2026)</strong>, des <strong>1. Nachtragshaushalts 2026 (+42,04 Mio. € Konsolidierungspaket)</strong>,
      der <strong>Mittelfristigen Finanzplanung bis 2029</strong>, des geprüften <strong>Jahresabschlusses 2024</strong>, der <strong>10-Jahres-Schlussbilanz (1,78 Mrd. €)</strong>
      sowie der <strong>städtischen Gesellschaften &amp; Eigenbetriebe</strong>.
    </p>

    <!-- GLOBAL KPI CARDS -->
    <div class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-label" id="kpi1Label">Ordentliche Aufwendungen</div>
        <div class="kpi-value" id="kpi1Val">-</div>
        <div class="kpi-delta" id="kpi1Delta"></div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label" id="kpi2Label">Ordentliche Erträge</div>
        <div class="kpi-value" id="kpi2Val">-</div>
        <div class="kpi-delta" id="kpi2Delta"></div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label" id="kpi3Label">Ordentliches Ergebnis / Saldo</div>
        <div class="kpi-value" id="kpi3Val">-</div>
        <div class="kpi-delta" id="kpi3Delta"></div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label" id="kpi4Label">Kostendeckungsgrad</div>
        <div class="kpi-value" id="kpi4Val">-</div>
        <div class="kpi-delta delta-neutral" id="kpi4Delta"></div>
      </div>
    </div>

    <!-- TABS -->
    <div class="tabs" id="tabBar">
      <button class="tab-btn active" data-tab="tab1">🧩 Kacheln &amp; Drill-Down (2013–26)</button>
      <button class="tab-btn" data-tab="tab2">📈 Zeitreihen &amp; Treiber (2013–26)</button>
      <button class="tab-btn" data-tab="tab3">🏛️ Gesamthaushalt (2013–29)</button>
      <button class="tab-btn" data-tab="tab4">🚨 1. Nachtrag 2026 &amp; Finanzplan</button>
      <button class="tab-btn" data-tab="tab5">🏦 Bilanz, JA 2024 &amp; Konzern</button>
    </div>

    <!-- TAB 1 -->
    <section class="tab-panel active" id="tab1">
      <div id="tab1NegNotice" class="caption-banner" style="display:none;"></div>
      <div class="card">
        <div id="chartTreemap" style="width:100%;height:700px;"></div>
      </div>
      <div class="grid-2">
        <div class="card"><div id="chartTopAemter" style="width:100%;height:450px;"></div></div>
        <div class="card"><div id="chartKategorien" style="width:100%;height:450px;"></div></div>
      </div>
      <div class="card">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;flex-wrap:wrap;gap:10px;">
          <div>
            <h3 style="margin:0;font-size:1.05rem;" id="tab1TableTitle">📋 Extrahierte Einzelpositionen</h3>
            <span style="font-size:0.8rem;color:var(--muted);">Klicke auf Spaltenköpfe zum Sortieren.</span>
          </div>
          <button class="btn" id="btnDownloadTab1">📥 Als CSV herunterladen</button>
        </div>
        <div class="table-wrap">
          <table id="tblTab1">
            <thead>
              <tr>
                <th data-col="Amt">Amt / Teilhaushalt</th>
                <th data-col="Kategorie">Kategorie</th>
                <th data-col="Sub_Kategorie">Einzelposten (Erläuterung)</th>
                <th data-col="Betrag" class="num">Betrag (EUR) ↓</th>
                <th data-col="Anteil" class="num">Anteil (%)</th>
              </tr>
            </thead>
            <tbody></tbody>
          </table>
        </div>
      </div>
    </section>

    <!-- TAB 2 -->
    <section class="tab-panel" id="tab2">
      <div class="card">
        <h3 style="margin:0 0 12px 0;">📈 Größte Veränderungen &amp; Treiber-Analyse (2013–2026)</h3>
        <div class="toolbar-row">
          <div>
            <label style="font-size:0.78rem;font-weight:600;color:var(--muted);">Haushaltsseite</label>
            <select id="t2Typ">
              <option value="Aufwendungen">Aufwendungen (Kosten)</option>
              <option value="Erträge">Erträge (Einnahmen)</option>
            </select>
          </div>
          <div>
            <label style="font-size:0.78rem;font-weight:600;color:var(--muted);">Basisjahr (Von)</label>
            <select id="t2Start"></select>
          </div>
          <div>
            <label style="font-size:0.78rem;font-weight:600;color:var(--muted);">Zieljahr (Bis)</label>
            <select id="t2End"></select>
          </div>
          <div>
            <label style="font-size:0.78rem;font-weight:600;color:var(--muted);">Sortierung Top 30</label>
            <select id="t2Rank">
              <option value="abs">Absolute Steigerung (€)</option>
              <option value="pct">Prozentuales Wachstum (%)</option>
            </select>
          </div>
          <div>
            <label style="font-size:0.78rem;font-weight:600;color:var(--muted);">Analyse-Ebene</label>
            <select id="t2Level">
              <option value="sub">Einzelposten (Sub_Kategorie)</option>
              <option value="kat">Amt × Kategorie</option>
              <option value="amt">Teilhaushalt (Amt gesamt)</option>
            </select>
          </div>
          <div>
            <label style="font-size:0.78rem;font-weight:600;color:var(--muted);">Mindestvolumen Basis (€)</label>
            <input type="number" id="t2MinBase" value="50000" step="25000" min="0" />
          </div>
        </div>
        <div id="chartGrowth" style="width:100%;height:680px;"></div>
      </div>

      <div class="card">
        <h3 style="margin:0 0 8px 0;">⏱️ Mehrjahres-Zeitreihe (2013–2026) nach Amt, Kategorie &amp; Einzelposten</h3>
        <div class="toolbar-row">
          <div>
            <label style="font-size:0.78rem;font-weight:600;color:var(--muted);">1. Haushaltsseite</label>
            <select id="tsTyp">
              <option value="Aufwendungen">Aufwendungen</option>
              <option value="Erträge">Erträge</option>
            </select>
          </div>
          <div>
            <label style="font-size:0.78rem;font-weight:600;color:var(--muted);">2. Amt / Teilhaushalt</label>
            <select id="tsAmt"></select>
          </div>
          <div>
            <label style="font-size:0.78rem;font-weight:600;color:var(--muted);">3. Kategorie</label>
            <select id="tsKat"></select>
          </div>
          <div>
            <label style="font-size:0.78rem;font-weight:600;color:var(--muted);">4. Einzelposten</label>
            <select id="tsSub"></select>
          </div>
        </div>
        <div id="chartTimeSeries" style="width:100%;height:450px;"></div>
      </div>
    </section>

    <!-- TAB 3 -->
    <section class="tab-panel" id="tab3">
      <div class="card">
        <h3 style="margin:0 0 6px 0;">🏛️ 17-Jahres-Entwicklung des Gesamthaushalts (2013–2029)</h3>
        <p style="margin:0 0 12px 0;font-size:0.86rem;color:var(--muted);">
          Kombiniert die geprüften Ist-Ergebnisse 2013–2024 (Jahresabschluss 2024) mit dem Haushaltsplan 2025, dem 1. Nachtragshaushalt 2026 und der Finanzplanung 2027–2029.
        </p>
        <div id="chartMacroMain" style="width:100%;height:520px;"></div>
      </div>
      <div class="grid-2">
        <div class="card"><div id="chartMacroCF" style="width:100%;height:410px;"></div></div>
        <div class="card"><div id="chartMacroDebt" style="width:100%;height:410px;"></div></div>
      </div>
      <div class="card">
        <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px;margin-bottom:8px;">
          <h3 style="margin:0;" id="tab3SaldoTitle">⚖️ Netto-Ressourcen-/Zuschussbedarf je Teilhaushalt</h3>
          <label style="font-size:0.84rem;cursor:pointer;">
            <input type="checkbox" id="chkExcludeFW" checked />
            TH FW (Allgemeine Finanzwirtschaft) ausblenden, um Fachämter besser zu skalieren
          </label>
        </div>
        <div id="chartAmtSaldo" style="width:100%;height:680px;"></div>
      </div>
    </section>

    <!-- TAB 4 -->
    <section class="tab-panel" id="tab4">
      <div class="info-banner">
        <strong>🚨 1. Nachtragshaushalt 2026 (Beschluss 18.12.2025):</strong> Durch <strong>+25,20 Mio. € höhere Erträge</strong> (u.a. Gewerbesteuer-Hebesatz 400%, Schlüsselzuweisungen)
        und <strong>-16,84 Mio. € geringere Aufwendungen</strong> (u.a. 5%-Kürzung freiwilliger Zuschüsse, Sachkostenreduktion) verbessert sich das Ordentliche Ergebnis 2026 um
        <strong>+42,04 Mio. €</strong> (von -82,65 Mio. € auf -40,62 Mio. €), und der laufende Cashflow dreht von <strong>-28,93 Mio. € auf +11,19 Mio. €</strong>.
      </div>
      <div class="kpi-grid">
        <div class="kpi-card">
          <div class="kpi-label">Ordentliche Erträge 2026 (Neu)</div>
          <div class="kpi-value">868.460.060 €</div>
          <div class="kpi-delta delta-pos">+25,20 Mio. € (+3,0%) ggü. Ursprungsplan</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">Ordentliche Aufwendungen 2026 (Neu)</div>
          <div class="kpi-value">909.078.188 €</div>
          <div class="kpi-delta delta-pos">-16,84 Mio. € (-1,8%) Einsparung</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">Ordentliches Ergebnis 2026 (Neu)</div>
          <div class="kpi-value">-40.618.128 €</div>
          <div class="kpi-delta delta-pos">+42,04 Mio. € Verbesserung</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">Cashflow Ergebnishaushalt 2026</div>
          <div class="kpi-value">+11.188.802 €</div>
          <div class="kpi-delta delta-pos">+40,12 Mio. € (von -28,93 Mio. €)</div>
        </div>
      </div>
      <div class="grid-2">
        <div class="card"><div id="chartNhPos" style="width:100%;height:450px;"></div></div>
        <div class="card"><div id="chartNhAmt" style="width:100%;height:450px;"></div></div>
      </div>
      <div class="grid-2">
        <div class="card"><div id="chartBund" style="width:100%;height:400px;"></div></div>
        <div class="card"><div id="chartLoss" style="width:100%;height:400px;"></div></div>
      </div>
      <div class="card">
        <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px;margin-bottom:12px;">
          <h3 style="margin:0;">✂️ Alle 249 Einzel-Änderungsmaßnahmen im 1. Nachtragshaushalt 2026</h3>
          <div style="display:flex;gap:14px;align-items:center;flex-wrap:wrap;">
            <input type="text" id="inpNhSearch" placeholder="🔍 Maßnahme / Amt filtern..." style="width:260px;" />
            <label style="font-size:0.84rem;cursor:pointer;">
              <input type="checkbox" id="chkOnly5Pct" /> Nur 5%-Kürzungen freiwilliger Zuschüsse (*)
            </label>
          </div>
        </div>
        <div class="table-wrap">
          <table id="tblNhMass">
            <thead>
              <tr>
                <th>TH</th>
                <th>Amt</th>
                <th>Kategorie</th>
                <th>Maßnahme / Erläuterung</th>
                <th>5%-Kürzung</th>
                <th class="num">Bisher 2026 (€)</th>
                <th class="num">Änderung (€)</th>
                <th class="num">Neu 2026 (€)</th>
              </tr>
            </thead>
            <tbody></tbody>
          </table>
        </div>
      </div>
    </section>

    <!-- TAB 5 -->
    <section class="tab-panel" id="tab5">
      <div class="kpi-grid">
        <div class="kpi-card">
          <div class="kpi-label">Bilanzsumme (31.12.2024)</div>
          <div class="kpi-value">1.780,06 Mio. €</div>
          <div class="kpi-delta delta-pos">+22,43 Mio. € (+1,3%) ggü. 2023</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">Eigenkapital / Kapitalposition (2024)</div>
          <div class="kpi-value">1.006,93 Mio. €</div>
          <div class="kpi-delta delta-neutral">-37,47 Mio. € (EK-Quote 56,6%)</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">Verbindlichkeiten Bilanz (2024)</div>
          <div class="kpi-value">431,15 Mio. €</div>
          <div class="kpi-delta delta-neg">+79,47 Mio. € (+22,6%) ggü. 2023</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">Vorbelastungen künftiger Jahre</div>
          <div class="kpi-value">1.220,57 Mio. €</div>
          <div class="kpi-delta delta-neutral">Bürgschaften 634 Mio. + Pensionen 542 Mio.</div>
        </div>
      </div>
      <div class="grid-2">
        <div class="card"><div id="chartBilanzAkt" style="width:100%;height:440px;"></div></div>
        <div class="card"><div id="chartBilanzPas" style="width:100%;height:440px;"></div></div>
      </div>
      <div class="grid-2">
        <div class="card"><div id="chartVorbelastungen" style="width:100%;height:410px;"></div></div>
        <div class="card">
          <h3 style="margin:0 0 10px 0;font-size:1rem;">🏢 Städtische Gesellschaften, Eigenbetriebe &amp; Schulden 2026</h3>
          <div class="table-wrap" style="max-height:365px;">
            <table id="tblBeteiligungen">
              <thead>
                <tr>
                  <th>Einheit</th>
                  <th>Aufgabenfeld</th>
                  <th class="num">Erträge 26 (T€)</th>
                  <th class="num">Aufwand 26 (T€)</th>
                  <th class="num">Ergebnis 26 (T€)</th>
                  <th class="num">Schulden Ende 26 (T€)</th>
                </tr>
              </thead>
              <tbody></tbody>
            </table>
          </div>
        </div>
      </div>
      <div class="grid-2">
        <div class="card"><div id="chartJa2024" style="width:100%;height:480px;"></div></div>
        <div class="card"><div id="chartPersonal" style="width:100%;height:480px;"></div></div>
      </div>
    </section>
  </main>

  <script>
    const RAW = {data_json};

    const YEAR_STATUS = {{
      2013: "Ergebnis",
      2014: "Plan",
      2015: "Plan (HH 15/16) / Ist in Tab 3&5",
      2016: "Plan (HH 15/16) / Ist in Tab 3&5",
      2017: "Ergebnis",
      2018: "Plan",
      2019: "Ergebnis",
      2020: "Plan",
      2021: "Ergebnis",
      2022: "Plan",
      2023: "Ergebnis (JA 2023/24)",
      2024: "Plan (HH 25/26) / Ist in Tab 3&5",
      2025: "Plan (HH 25/26)",
      2026: "Plan (HH 25/26) / 1. Nachtrag in Tab 4"
    }};

    const ALL_ROWS = RAW.rows.map(r => ({{
      Jahr: r[0],
      Amt: RAW.aemter[r[1]],
      Kategorie: RAW.kats[r[2]],
      Sub_Kategorie: RAW.subs[r[3]],
      Typ: RAW.typen[r[4]],
      Betrag: r[5]
    }}));

    const YEARS_DESC = Array.from(new Set(ALL_ROWS.map(r => r.Jahr))).sort((a,b) => b - a);
    const YEARS_ASC = [...YEARS_DESC].reverse();

    let state = {{
      year: 2025,
      type: "Aufwendungen",
      hierarchy: "amt_first",
      chartType: "treemap",
      amt: "ALL",
      search: "",
      activeTab: "tab1",
      tab1SortCol: "Betrag",
      tab1SortAsc: false
    }};

    function fmtEur(val, decimals = 0) {{
      if (val === null || val === undefined || isNaN(val)) return "0 €";
      return Number(val).toLocaleString("de-DE", {{
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
      }}) + " €";
    }}

    function fmtMio(val) {{
      if (val === null || val === undefined || isNaN(val)) return "0,00 Mio. €";
      return (Number(val) / 1e6).toLocaleString("de-DE", {{
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      }}) + " Mio. €";
    }}

    function shortAmt(s) {{
      if (!s) return "";
      return s.length <= 38 ? s : s.slice(0, 36) + "…";
    }}

    // Initialize controls
    function initControls() {{
      const selYear = document.getElementById("selYear");
      YEARS_DESC.forEach(y => {{
        const opt = document.createElement("option");
        opt.value = y;
        opt.textContent = `${{y}} (${{YEAR_STATUS[y] || "Plan"}})`;
        if (y === state.year) opt.selected = true;
        selYear.appendChild(opt);
      }});
      selYear.addEventListener("change", e => {{
        state.year = parseInt(e.target.value, 10);
        refreshAll();
      }});

      const selAmt = document.getElementById("selAmt");
      RAW.aemter.forEach(a => {{
        const opt = document.createElement("option");
        opt.value = a;
        opt.textContent = a;
        selAmt.appendChild(opt);
      }});
      selAmt.addEventListener("change", e => {{
        state.amt = e.target.value;
        refreshAll();
      }});

      document.getElementById("selHierarchy").addEventListener("change", e => {{
        state.hierarchy = e.target.value;
        renderTab1();
      }});

      document.getElementById("inpSearch").addEventListener("input", e => {{
        state.search = e.target.value.trim().toLowerCase();
        refreshAll();
      }});

      document.querySelectorAll("#pillType .radio-pill").forEach(el => {{
        el.addEventListener("click", () => {{
          document.querySelectorAll("#pillType .radio-pill").forEach(x => x.classList.remove("active"));
          el.classList.add("active");
          state.type = el.dataset.val;
          renderTab1();
        }});
      }});

      document.querySelectorAll("#pillChart .radio-pill").forEach(el => {{
        el.addEventListener("click", () => {{
          document.querySelectorAll("#pillChart .radio-pill").forEach(x => x.classList.remove("active"));
          el.classList.add("active");
          state.chartType = el.dataset.val;
          renderTab1();
        }});
      }});

      // Tab bar
      document.querySelectorAll("#tabBar .tab-btn").forEach(btn => {{
        btn.addEventListener("click", () => {{
          document.querySelectorAll("#tabBar .tab-btn").forEach(b => b.classList.remove("active"));
          document.querySelectorAll(".tab-panel").forEach(p => p.classList.remove("active"));
          btn.classList.add("active");
          state.activeTab = btn.dataset.tab;
          document.getElementById(state.activeTab).classList.add("active");
          renderActiveTab();
        }});
      }});

      // Tab 2 Controls
      const t2Start = document.getElementById("t2Start");
      const t2End = document.getElementById("t2End");
      YEARS_ASC.forEach(y => {{
        const o1 = document.createElement("option");
        o1.value = y; o1.textContent = y;
        if (y === 2013) o1.selected = true;
        t2Start.appendChild(o1);

        const o2 = document.createElement("option");
        o2.value = y; o2.textContent = y;
        if (y === 2026) o2.selected = true;
        t2End.appendChild(o2);
      }});
      ["t2Typ", "t2Start", "t2End", "t2Rank", "t2Level", "t2MinBase"].forEach(id => {{
        document.getElementById(id).addEventListener("change", renderTab2Growth);
      }});

      // Tab 2 Cascading Time Series
      document.getElementById("tsTyp").addEventListener("change", () => {{ populateTsAmt(); renderTab2TS(); }});
      document.getElementById("tsAmt").addEventListener("change", () => {{ populateTsKat(); renderTab2TS(); }});
      document.getElementById("tsKat").addEventListener("change", () => {{ populateTsSub(); renderTab2TS(); }});
      document.getElementById("tsSub").addEventListener("change", renderTab2TS);
      populateTsAmt();

      // Tab 3 Exclude FW
      document.getElementById("chkExcludeFW").addEventListener("change", renderTab3Saldo);

      // Tab 4 Filters
      document.getElementById("inpNhSearch").addEventListener("input", renderTab4Table);
      document.getElementById("chkOnly5Pct").addEventListener("change", renderTab4Table);

      // Tab 1 Table Sorting & Download
      document.querySelectorAll("#tblTab1 th").forEach(th => {{
        th.addEventListener("click", () => {{
          const col = th.dataset.col;
          if (!col) return;
          if (state.tab1SortCol === col) {{
            state.tab1SortAsc = !state.tab1SortAsc;
          }} else {{
            state.tab1SortCol = col;
            state.tab1SortAsc = col !== "Betrag" && col !== "Anteil";
          }}
          renderTab1Table();
        }});
      }});
      document.getElementById("btnDownloadTab1").addEventListener("click", downloadTab1Csv);
    }}

    function filterRowsForYear(yr) {{
      return ALL_ROWS.filter(r => {{
        if (r.Jahr !== yr) return false;
        if (state.amt !== "ALL" && r.Amt !== state.amt) return false;
        if (state.search) {{
          const q = state.search;
          if (
            !r.Amt.toLowerCase().includes(q) &&
            !r.Kategorie.toLowerCase().includes(q) &&
            !r.Sub_Kategorie.toLowerCase().includes(q)
          ) return false;
        }}
        return true;
      }});
    }}

    function updateKPIs() {{
      const cur = filterRowsForYear(state.year);
      const prev = filterRowsForYear(state.year - 1);

      const aufwCur = cur.filter(r => r.Typ === "Aufwendungen").reduce((s, r) => s + r.Betrag, 0);
      const ertrCur = cur.filter(r => r.Typ === "Erträge").reduce((s, r) => s + r.Betrag, 0);
      const saldoCur = ertrCur - aufwCur;
      const deckCur = aufwCur > 0 ? (ertrCur / aufwCur) * 100 : 0;

      document.getElementById("kpi1Label").textContent = `Ordentliche Aufwendungen (${{state.year}})`;
      document.getElementById("kpi1Val").textContent = fmtEur(aufwCur, 0);
      document.getElementById("kpi2Label").textContent = `Ordentliche Erträge (${{state.year}})`;
      document.getElementById("kpi2Val").textContent = fmtEur(ertrCur, 0);
      document.getElementById("kpi3Label").textContent = `Ordentliches Ergebnis / Saldo (${{state.year}})`;
      document.getElementById("kpi3Val").textContent = fmtEur(saldoCur, 0);
      document.getElementById("kpi4Label").textContent = `Kostendeckungsgrad (${{state.year}})`;
      document.getElementById("kpi4Val").textContent = deckCur.toFixed(1).replace(".", ",") + " %";

      const uniqueAemter = new Set(cur.map(r => r.Amt)).size;
      document.getElementById("kpi4Delta").textContent = `${{uniqueAemter}} Teilhaushalte aktiv`;

      const d1 = document.getElementById("kpi1Delta");
      const d2 = document.getElementById("kpi2Delta");
      const d3 = document.getElementById("kpi3Delta");

      if (prev.length > 0) {{
        const aufwPrev = prev.filter(r => r.Typ === "Aufwendungen").reduce((s, r) => s + r.Betrag, 0);
        const ertrPrev = prev.filter(r => r.Typ === "Erträge").reduce((s, r) => s + r.Betrag, 0);
        const saldoPrev = ertrPrev - aufwPrev;

        const da = aufwCur - aufwPrev;
        const pa = aufwPrev !== 0 ? (da / Math.abs(aufwPrev)) * 100 : 0;
        d1.textContent = `${{da >= 0 ? "+" : ""}}${{(da/1e6).toFixed(2).replace(".", ",")}} Mio. € (${{pa >= 0 ? "+" : ""}}${{pa.toFixed(1).replace(".", ",")}}%) ggü. ${{state.year - 1}}`;
        d1.className = "kpi-delta " + (da <= 0 ? "delta-pos" : "delta-neg");

        const de = ertrCur - ertrPrev;
        const pe = ertrPrev !== 0 ? (de / Math.abs(ertrPrev)) * 100 : 0;
        d2.textContent = `${{de >= 0 ? "+" : ""}}${{(de/1e6).toFixed(2).replace(".", ",")}} Mio. € (${{pe >= 0 ? "+" : ""}}${{pe.toFixed(1).replace(".", ",")}}%) ggü. ${{state.year - 1}}`;
        d2.className = "kpi-delta " + (de >= 0 ? "delta-pos" : "delta-neg");

        const ds = saldoCur - saldoPrev;
        d3.textContent = `${{ds >= 0 ? "+" : ""}}${{(ds/1e6).toFixed(2).replace(".", ",")}} Mio. € ggü. ${{state.year - 1}}`;
        d3.className = "kpi-delta " + (ds >= 0 ? "delta-pos" : "delta-neg");
      }} else {{
        d1.textContent = ""; d2.textContent = ""; d3.textContent = "";
      }}
    }}

    // ================= TAB 1 =================
    let currentTab1Rows = [];

    function renderTab1() {{
      const rows = filterRowsForYear(state.year).filter(r => r.Typ === state.type);
      currentTab1Rows = rows;

      // Group by Amt, Kategorie, Sub_Kategorie
      const grpMap = new Map();
      rows.forEach(r => {{
        const key = `${{r.Amt}}|||${{r.Kategorie}}|||${{r.Sub_Kategorie}}`;
        grpMap.set(key, (grpMap.get(key) || 0) + r.Betrag);
      }});

      const grouped = [];
      const negItems = [];
      let negSum = 0;
      let posSum = 0;

      grpMap.forEach((val, key) => {{
        const [Amt, Kategorie, Sub_Kategorie] = key.split("|||");
        if (val < 0) {{
          negSum += val;
          negItems.push(`${{Amt}}: ${{Sub_Kategorie}} (${{fmtEur(val, 0)}})`);
        }} else if (val > 0) {{
          posSum += val;
          grouped.push({{ Amt, Kategorie, Sub_Kategorie, Betrag: val }});
        }}
      }});

      const noticeEl = document.getElementById("tab1NegNotice");
      if (negItems.length > 0) {{
        noticeEl.style.display = "block";
        noticeEl.innerHTML = `ℹ️ <strong>Hinweis zur Kachel-Darstellung:</strong> Im Gesamtsaldo (${{fmtEur(posSum + negSum, 0)}}) sind pauschale Minderaufwendungen/Absetzungen in Höhe von <strong>${{fmtEur(negSum, 0)}}</strong> enthalten (${{negItems.join(", ")}}). Die Flächenanteile im Diagramm zeigen die positiven Brutto-Ansätze (${{fmtEur(posSum, 0)}}).`;
      }} else {{
        noticeEl.style.display = "none";
      }}

      // Build hierarchical nodes for Plotly treemap / sunburst
      const rootId = "ROOT";
      const rootLabel = `Gesamt ${{state.type}} (${{state.year}})`;
      const ids = [rootId];
      const labels = [rootLabel];
      const parents = [""];
      const values = [posSum];

      const l1Map = new Map();
      const l2Map = new Map();

      grouped.forEach(g => {{
        const l1 = state.hierarchy === "amt_first" ? g.Amt : g.Kategorie;
        const l2 = state.hierarchy === "amt_first" ? g.Kategorie : g.Amt;
        l1Map.set(l1, (l1Map.get(l1) || 0) + g.Betrag);
        const l2Key = `${{l1}}|||${{l2}}`;
        l2Map.set(l2Key, (l2Map.get(l2Key) || 0) + g.Betrag);
      }});

      l1Map.forEach((val, l1) => {{
        ids.push(`L1:${{l1}}`);
        labels.push(l1);
        parents.push(rootId);
        values.push(val);
      }});

      l2Map.forEach((val, l2Key) => {{
        const [l1, l2] = l2Key.split("|||");
        ids.push(`L2:${{l2Key}}`);
        labels.push(l2);
        parents.push(`L1:${{l1}}`);
        values.push(val);
      }});

      grouped.forEach((g, idx) => {{
        const l1 = state.hierarchy === "amt_first" ? g.Amt : g.Kategorie;
        const l2 = state.hierarchy === "amt_first" ? g.Kategorie : g.Amt;
        const subLbl = g.Sub_Kategorie === g.Kategorie ? `${{g.Sub_Kategorie}} (Gesamtposition)` : g.Sub_Kategorie;
        ids.push(`L3:${{idx}}`);
        labels.push(subLbl);
        parents.push(`L2:${{l1}}|||${{l2}}`);
        values.push(g.Betrag);
      }});

      const customFmt = values.map(v => fmtEur(v, 0));
      const trace = {{
        type: state.chartType === "sunburst" ? "sunburst" : "treemap",
        ids,
        labels,
        parents,
        values,
        branchvalues: "total",
        customdata: customFmt,
        maxdepth: 3,
        texttemplate: "<b>%{{label}}</b><br>%{{customdata}}<br>%{{percentParent:.1%}}",
        hovertemplate: "<b>%{{label}}</b><br>Betrag: <b>%{{customdata}}</b><br>Anteil Überkat.: <b>%{{percentParent:.2%}}</b><br>Anteil Gesamt: <b>%{{percentRoot:.2%}}</b><extra></extra>"
      }};

      Plotly.react("chartTreemap", [trace], {{
        title: `${{state.chartType === "sunburst" ? "Interaktives Sunburst-Diagramm" : "Drillable Tile-Chart (Treemap)"}} der ${{state.type}} im Jahr ${{state.year}} (${{YEAR_STATUS[state.year] || ""}})`,
        margin: {{ t: 50, l: 12, r: 12, b: 12 }}
      }}, {{ responsive: true }});

      // Top 15 Ämter Bar Chart
      const amtMapSum = new Map();
      rows.forEach(r => amtMapSum.set(r.Amt, (amtMapSum.get(r.Amt) || 0) + r.Betrag));
      const topAemter = Array.from(amtMapSum.entries())
        .map(([Amt, Betrag]) => ({{ Amt, AmtKurz: shortAmt(Amt), Betrag }}))
        .sort((a,b) => b.Betrag - a.Betrag)
        .slice(0, 15)
        .reverse();

      Plotly.react("chartTopAemter", [{{
        type: "bar",
        orientation: "h",
        y: topAemter.map(x => x.AmtKurz),
        x: topAemter.map(x => x.Betrag),
        text: topAemter.map(x => fmtMio(x.Betrag)),
        textposition: "outside",
        cliponaxis: false,
        marker: {{ color: state.type === "Aufwendungen" ? "#dc2626" : "#16a34a" }},
        hovertemplate: "<b>%{{y}}</b><br>Betrag: %{{x:,.0f}} €<extra></extra>"
      }}], {{
        title: `Top 15 Ämter / Teilhaushalte — ${{state.type}} (${{state.year}})`,
        margin: {{ t: 45, l: 210, r: 85, b: 35 }},
        xaxis: {{ title: "Betrag (€)" }}
      }}, {{ responsive: true }});

      // Kategorien Bar Chart
      const katMapSum = new Map();
      rows.forEach(r => katMapSum.set(r.Kategorie, (katMapSum.get(r.Kategorie) || 0) + r.Betrag));
      const topKats = Array.from(katMapSum.entries())
        .map(([Kategorie, Betrag]) => ({{ Kategorie, Betrag }}))
        .sort((a,b) => b.Betrag - a.Betrag)
        .reverse();

      Plotly.react("chartKategorien", [{{
        type: "bar",
        orientation: "h",
        y: topKats.map(x => shortAmt(x.Kategorie)),
        x: topKats.map(x => x.Betrag),
        text: topKats.map(x => fmtMio(x.Betrag)),
        textposition: "outside",
        cliponaxis: false,
        marker: {{ color: state.type === "Aufwendungen" ? "#ea580c" : "#0d9488" }},
        hovertemplate: "<b>%{{y}}</b><br>Betrag: %{{x:,.0f}} €<extra></extra>"
      }}], {{
        title: `Verteilung nach Kategorie — ${{state.type}} (${{state.year}})`,
        margin: {{ t: 45, l: 210, r: 85, b: 35 }},
        xaxis: {{ title: "Betrag (€)" }}
      }}, {{ responsive: true }});

      renderTab1Table();
    }}

    function renderTab1Table() {{
      const total = currentTab1Rows.reduce((s, r) => s + r.Betrag, 0);
      const enriched = currentTab1Rows.map(r => ({{
        ...r,
        Anteil: total !== 0 ? (r.Betrag / total) * 100 : 0
      }}));

      const col = state.tab1SortCol;
      const dir = state.tab1SortAsc ? 1 : -1;
      enriched.sort((a, b) => {{
        if (typeof a[col] === "number") return (a[col] - b[col]) * dir;
        return String(a[col]).localeCompare(String(b[col]), "de") * dir;
      }});

      document.getElementById("tab1TableTitle").textContent =
        `📋 Extrahierte Positionen (${{state.type}} ${{state.year}} — ${{enriched.length.toLocaleString("de-DE")}} Zeilen)`;

      const tbody = document.querySelector("#tblTab1 tbody");
      tbody.innerHTML = enriched.map(r => `
        <tr>
          <td>${{r.Amt}}</td>
          <td>${{r.Kategorie}}</td>
          <td>${{r.Sub_Kategorie}}</td>
          <td class="num">${{fmtEur(r.Betrag, 2)}}</td>
          <td class="num">${{r.Anteil.toLocaleString("de-DE", {{minimumFractionDigits:2, maximumFractionDigits:2}})}} %</td>
        </tr>
      `).join("");
    }}

    function downloadTab1Csv() {{
      const header = ["Jahr", "Amt", "Kategorie", "Sub_Kategorie", "Typ", "Betrag"];
      const lines = [header.join(";")];
      currentTab1Rows.forEach(r => {{
        lines.push([
          r.Jahr,
          `"${{r.Amt.replace(/"/g, '""')}}"`,
          `"${{r.Kategorie.replace(/"/g, '""')}}"`,
          `"${{r.Sub_Kategorie.replace(/"/g, '""')}}"`,
          r.Typ,
          r.Betrag.toFixed(2).replace(".", ",")
        ].join(";"));
      }});
      const blob = new Blob(["\\uFEFF" + lines.join("\\n")], {{ type: "text/csv;charset=utf-8;" }});
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `haushalt_heidelberg_${{state.type.toLowerCase()}}_${{state.year}}.csv`;
      a.click();
      URL.revokeObjectURL(url);
    }}

    // ================= TAB 2 =================
    function renderTab2Growth() {{
      const typ = document.getElementById("t2Typ").value;
      const startYr = parseInt(document.getElementById("t2Start").value, 10);
      const endYr = parseInt(document.getElementById("t2End").value, 10);
      const rankMode = document.getElementById("t2Rank").value;
      const level = document.getElementById("t2Level").value;
      const minBase = parseFloat(document.getElementById("t2MinBase").value) || 0;

      if (startYr >= endYr) return;

      const baseRows = ALL_ROWS.filter(r => r.Typ === typ && (r.Jahr === startYr || r.Jahr === endYr) && (state.amt === "ALL" || r.Amt === state.amt));
      const map = new Map();
      baseRows.forEach(r => {{
        let key = r.Amt;
        if (level === "kat") key = `${{r.Amt}}|||${{r.Kategorie}}`;
        else if (level === "sub") key = `${{r.Amt}}|||${{r.Kategorie}}|||${{r.Sub_Kategorie}}`;
        if (!map.has(key)) map.set(key, {{ key, Amt: r.Amt, Kategorie: r.Kategorie, Sub: r.Sub_Kategorie, s: 0, e: 0 }});
        const item = map.get(key);
        if (r.Jahr === startYr) item.s += r.Betrag;
        if (r.Jahr === endYr) item.e += r.Betrag;
      }});

      let items = Array.from(map.values()).filter(it => Math.abs(it.s) >= minBase);
      items.forEach(it => {{
        it.delta = it.e - it.s;
        it.pct = Math.abs(it.s) > 0 ? (it.delta / Math.abs(it.s)) * 100 : 0;
        const amtCode = it.Amt.startsWith("TH ") ? it.Amt.split(" ")[1] : it.Amt.slice(0, 10);
        if (level === "amt") it.label = shortAmt(it.Amt);
        else if (level === "kat") it.label = `TH ${{amtCode}} | ${{shortAmt(it.Kategorie)}}`;
        else it.label = `TH ${{amtCode}} | ${{shortAmt(it.Sub)}}`;
      }});

      items.sort((a, b) => rankMode === "abs" ? b.delta - a.delta : b.pct - a.pct);
      const top = items.slice(0, 30).reverse();

      Plotly.react("chartGrowth", [{{
        type: "bar",
        orientation: "h",
        y: top.map((x, i) => `${{x.label}}`),
        x: top.map(x => rankMode === "abs" ? x.delta : x.pct),
        marker: {{ color: typ === "Aufwendungen" ? "#dc2626" : "#16a34a" }},
        customdata: top.map(x => [x.Amt, fmtEur(x.s, 0), fmtEur(x.e, 0), fmtEur(x.delta, 0), x.pct.toFixed(1) + "%"]),
        hovertemplate: `<b>%{{y}}</b><br>Amt: %{{customdata[0]}}<br>${{startYr}}: <b>%{{customdata[1]}}</b><br>${{endYr}}: <b>%{{customdata[2]}}</b><br>Delta: <b>%{{customdata[3]}} (%{{customdata[4]}})</b><extra></extra>`
      }}], {{
        title: `Top ${{top.length}} Treiber (${{typ}}: ${{startYr}} ➔ ${{endYr}}, Basis ≥ ${{fmtEur(minBase, 0)}})`,
        margin: {{ t: 45, l: 270, r: 40, b: 40 }},
        xaxis: {{ title: rankMode === "abs" ? `Absolute Veränderung ${{startYr}} ➔ ${{endYr}} (€)` : `Prozentuales Wachstum ${{startYr}} ➔ ${{endYr}} (%)` }}
      }}, {{ responsive: true }});
    }}

    function populateTsAmt() {{
      const typ = document.getElementById("tsTyp").value;
      const sel = document.getElementById("tsAmt");
      const aemter = Array.from(new Set(ALL_ROWS.filter(r => r.Typ === typ).map(r => r.Amt))).sort();
      sel.innerHTML = `<option value="ALL">Alle Ämter (Gesamthaushalt)</option>` + aemter.map(a => `<option value="${{a}}">${{a}}</option>`).join("");
      populateTsKat();
    }}

    function populateTsKat() {{
      const typ = document.getElementById("tsTyp").value;
      const amt = document.getElementById("tsAmt").value;
      const sel = document.getElementById("tsKat");
      const kats = Array.from(new Set(ALL_ROWS.filter(r => r.Typ === typ && (amt === "ALL" || r.Amt === amt)).map(r => r.Kategorie))).sort();
      sel.innerHTML = `<option value="ALL">Alle Kategorien</option>` + kats.map(k => `<option value="${{k}}">${{k}}</option>`).join("");
      populateTsSub();
    }}

    function populateTsSub() {{
      const typ = document.getElementById("tsTyp").value;
      const amt = document.getElementById("tsAmt").value;
      const kat = document.getElementById("tsKat").value;
      const sel = document.getElementById("tsSub");
      const subs = Array.from(new Set(ALL_ROWS.filter(r => r.Typ === typ && (amt === "ALL" || r.Amt === amt) && (kat === "ALL" || r.Kategorie === kat)).map(r => r.Sub_Kategorie))).sort();
      sel.innerHTML = `<option value="ALL">Alle Einzelposten (Summe)</option>` + subs.map(s => `<option value="${{s}}">${{s}}</option>`).join("");
    }}

    function renderTab2TS() {{
      const typ = document.getElementById("tsTyp").value;
      const amt = document.getElementById("tsAmt").value;
      const kat = document.getElementById("tsKat").value;
      const sub = document.getElementById("tsSub").value;

      const filtered = ALL_ROWS.filter(r =>
        r.Typ === typ &&
        (amt === "ALL" || r.Amt === amt) &&
        (kat === "ALL" || r.Kategorie === kat) &&
        (sub === "ALL" || r.Sub_Kategorie === sub)
      );

      const yrMap = new Map();
      filtered.forEach(r => yrMap.set(r.Jahr, (yrMap.get(r.Jahr) || 0) + r.Betrag));
      const yrs = Array.from(yrMap.keys()).sort((a,b) => a - b);
      const vals = yrs.map(y => yrMap.get(y));
      const baseVal = vals.find(v => v !== 0) || 1;
      const pcts = vals.map(v => `${{((v - baseVal) / Math.abs(baseVal) * 100 >= 0 ? "+" : "")}}${{((v - baseVal) / Math.abs(baseVal) * 100).toFixed(1)}}%`);

      Plotly.react("chartTimeSeries", [{{
        type: "scatter",
        mode: "lines+markers+text",
        x: yrs,
        y: vals,
        text: pcts,
        textposition: "top center",
        line: {{ width: 3, color: typ === "Aufwendungen" ? "#dc2626" : "#16a34a" }},
        marker: {{ size: 9 }},
        hovertemplate: "<b>Jahr %{{x}}</b><br>Betrag: <b>%{{y:,.0f}} €</b><br>ggü. Basis: <b>%{{text}}</b><extra></extra>"
      }}], {{
        title: `Mehrjahres-Zeitreihe: ${{typ}} ➔ ${{amt === "ALL" ? "Gesamthaushalt" : shortAmt(amt)}}`,
        xaxis: {{ dtick: 1, title: "Haushaltsjahr" }},
        yaxis: {{ title: "Betrag (€)" }},
        margin: {{ t: 50, l: 70, r: 30, b: 40 }}
      }}, {{ responsive: true }});
    }}

    // ================= TAB 3 =================
    function renderTab3() {{
      const m = RAW.macro;
      const labels = m.map(r => `${{r.Jahr}} (${{String(r.Status).split(" ")[0]}})`);
      const ertr = m.map(r => r.Ordentliche_Ertraege_TEUR * 1000);
      const aufw = m.map(r => r.Ordentliche_Aufwendungen_TEUR * 1000);
      const saldo = m.map(r => r.Ordentliches_Ergebnis_TEUR * 1000);

      Plotly.react("chartMacroMain", [
        {{ type: "bar", name: "Ordentliche Erträge", x: labels, y: ertr, marker: {{ color: "#16a34a" }} }},
        {{ type: "bar", name: "Ordentliche Aufwendungen", x: labels, y: aufw, marker: {{ color: "#dc2626" }} }},
        {{ type: "scatter", mode: "lines+markers", name: "Ordentliches Ergebnis (Saldo)", x: labels, y: saldo, line: {{ color: "#1d4ed8", width: 3, dash: "dot" }}, marker: {{ size: 8 }} }}
      ], {{
        barmode: "group",
        title: "Ordentliche Erträge vs. Aufwendungen & Ordentliches Ergebnis (2013–2029)",
        legend: {{ orientation: "h", y: 1.1 }},
        margin: {{ t: 55, l: 70, r: 25, b: 60 }}
      }}, {{ responsive: true }});

      Plotly.react("chartMacroCF", [
        {{
          type: "bar",
          name: "Laufender Cashflow (Mio. €)",
          x: m.map(r => r.Jahr),
          y: m.map(r => r.Cashflow_Laufend_TEUR / 1000),
          marker: {{ color: m.map(r => r.Cashflow_Laufend_TEUR >= 0 ? "#0d9488" : "#e11d48") }}
        }},
        {{
          type: "scatter",
          mode: "lines+markers",
          name: "Investitionsauszahlungen (Mio. €)",
          x: m.map(r => r.Jahr),
          y: m.map(r => r.Investitionsauszahlungen_TEUR / 1000),
          line: {{ color: "#f59e0b", width: 3 }}
        }}
      ], {{
        title: "Laufender Cashflow vs. Investitionsauszahlungen (2013–2029, Mio. €)",
        legend: {{ orientation: "h", y: 1.12 }},
        margin: {{ t: 55, l: 55, r: 20, b: 40 }}
      }}, {{ responsive: true }});

      Plotly.react("chartMacroDebt", [
        {{
          type: "scatter",
          mode: "lines+markers",
          fill: "tozeroy",
          name: "Schulden Kernhaushalt (Mio. €)",
          x: m.map(r => r.Jahr),
          y: m.map(r => r.Schulden_Kernhaushalt_TEUR / 1000),
          line: {{ color: "#dc2626", width: 3 }}
        }},
        {{
          type: "scatter",
          mode: "lines+markers",
          name: "Ergebnisrücklagen (Mio. €)",
          x: m.map(r => r.Jahr),
          y: m.map(r => r.Ergebnisruecklagen_TEUR / 1000),
          line: {{ color: "#2563eb", width: 3, dash: "dash" }}
        }}
      ], {{
        title: "Schuldenstand Kernhaushalt vs. Ergebnisrücklagen (2013–2029, Mio. €)",
        legend: {{ orientation: "h", y: 1.12 }},
        margin: {{ t: 55, l: 55, r: 20, b: 40 }}
      }}, {{ responsive: true }});

      renderTab3Saldo();
    }}

    function renderTab3Saldo() {{
      const rows = filterRowsForYear(state.year);
      const excludeFW = document.getElementById("chkExcludeFW").checked;
      const map = new Map();
      rows.forEach(r => {{
        if (excludeFW && r.Amt.startsWith("TH FW")) return;
        if (!map.has(r.Amt)) map.set(r.Amt, {{ Amt: r.Amt, e: 0, a: 0 }});
        const it = map.get(r.Amt);
        if (r.Typ === "Erträge") it.e += r.Betrag;
        else it.a += r.Betrag;
      }});
      const list = Array.from(map.values()).map(it => ({{
        ...it,
        saldo: it.e - it.a
      }})).sort((a,b) => b.saldo - a.saldo);

      document.getElementById("tab3SaldoTitle").textContent = `⚖️ Netto-Ressourcen-/Zuschussbedarf je Teilhaushalt im Jahr ${{state.year}}`;

      Plotly.react("chartAmtSaldo", [{{
        type: "bar",
        orientation: "h",
        y: list.map(x => shortAmt(x.Amt)),
        x: list.map(x => x.saldo),
        marker: {{ color: list.map(x => x.saldo >= 0 ? "#16a34a" : "#dc2626") }},
        customdata: list.map(x => [x.Amt, fmtEur(x.e, 0), fmtEur(x.a, 0)]),
        hovertemplate: "<b>%{{customdata[0]}}</b><br>Saldo: <b>%{{x:,.0f}} €</b><br>Erträge: %{{customdata[1]}}<br>Aufwendungen: %{{customdata[2]}}<extra></extra>"
      }}], {{
        title: `Ordentliches Ergebnis (Erträge − Aufwendungen) je Teilhaushalt (${{state.year}})`,
        margin: {{ t: 45, l: 250, r: 30, b: 40 }},
        xaxis: {{ title: "Ordentliches Ergebnis (€)" }}
      }}, {{ responsive: true }});
    }}

    // ================= TAB 4 =================
    function renderTab4() {{
      const nhGes = RAW.nh_gesamt.filter(r => r.Aenderung_2026_EUR !== 0).map(r => ({{
        ...r,
        wirk: r.Typ === "Erträge" ? r.Aenderung_2026_EUR : -r.Aenderung_2026_EUR
      }})).sort((a,b) => a.wirk - b.wirk);

      Plotly.react("chartNhPos", [{{
        type: "bar",
        orientation: "h",
        y: nhGes.map(r => shortAmt(r.Position)),
        x: nhGes.map(r => r.wirk),
        marker: {{ color: nhGes.map(r => r.Typ === "Erträge" ? "#16a34a" : "#2563eb") }},
        hovertemplate: "<b>%{{y}}</b><br>Entlastungsbeitrag: <b>%{{x:,.0f}} €</b><extra></extra>"
      }}], {{
        title: "Ergebnisverbesserung (+42,04 Mio. €) nach Position im 1. Nachtrag 2026",
        margin: {{ t: 45, l: 220, r: 30, b: 35 }}
      }}, {{ responsive: true }});

      const nhAmt = RAW.nh_aemter
        .filter(r => String(r.Position).toLowerCase().includes("anteiliges ordentliches ergebnis") && r.Aenderung_2026 !== 0)
        .sort((a,b) => b.Aenderung_2026 - a.Aenderung_2026)
        .slice(0, 18)
        .reverse();

      Plotly.react("chartNhAmt", [{{
        type: "bar",
        orientation: "h",
        y: nhAmt.map(r => shortAmt(r.Amt)),
        x: nhAmt.map(r => r.Aenderung_2026),
        marker: {{ color: "#0d9488" }},
        hovertemplate: "<b>%{{y}}</b><br>Verbesserung: <b>%{{x:+,.0f}} €</b><extra></extra>"
      }}], {{
        title: "Top 18 Teilhaushalte nach Ergebnisverbesserung im 1. Nachtrag 2026",
        margin: {{ t: 45, l: 220, r: 30, b: 35 }}
      }}, {{ responsive: true }});

      Plotly.react("chartBund", [
        {{ type: "bar", name: "Sozial- & Jugendhilfe (BTHG)", x: ["2025", "2026"], y: [39.1, 44.5], marker: {{ color: "#dc2626" }} }},
        {{ type: "bar", name: "Kindertageseinrichtungen (Kita)", x: ["2025", "2026"], y: [28.7, 32.7], marker: {{ color: "#f97316" }} }},
        {{ type: "bar", name: "Bildung (Ganztagsschule)", x: ["2025", "2026"], y: [11.6, 12.2], marker: {{ color: "#eab308" }} }}
      ], {{
        barmode: "stack",
        title: "Mehrausgaben durch Bundesbeschlüsse (+80 / +90 Mio. € ggü. 2021)",
        yaxis: {{ title: "Mio. €" }},
        legend: {{ orientation: "h", y: -0.22 }},
        margin: {{ t: 45, l: 55, r: 20, b: 75 }}
      }}, {{ responsive: true }});

      Plotly.react("chartLoss", [{{
        type: "bar",
        orientation: "h",
        y: ["Gewerbesteuer-Einbruch 2024", "Schlüsselzuweisungen (Zensus 2022)"],
        x: [-23.0, -30.0],
        marker: {{ color: ["#be123c", "#9f1239"] }},
        text: ["-23 Mio. €", "-30 Mio. €"],
        textposition: "inside"
      }}], {{
        title: "Strukturelle Einnahmeverluste (-53 Mio. €)",
        xaxis: {{ title: "Mio. €" }},
        margin: {{ t: 45, l: 210, r: 25, b: 45 }}
      }}, {{ responsive: true }});

      renderTab4Table();
    }}

    function renderTab4Table() {{
      const q = document.getElementById("inpNhSearch").value.trim().toLowerCase();
      const only5 = document.getElementById("chkOnly5Pct").checked;

      const list = RAW.nh_massnahmen.filter(r => {{
        if (only5 && !r.Kuerzung_5_Prozent_Freiwillig) return false;
        if (q) {{
          return (
            String(r.Amt).toLowerCase().includes(q) ||
            String(r.Massnahme).toLowerCase().includes(q) ||
            String(r.Kategorie).toLowerCase().includes(q)
          );
        }}
        return true;
      }}).sort((a,b) => a.Aenderung_2026 - b.Aenderung_2026);

      const tbody = document.querySelector("#tblNhMass tbody");
      tbody.innerHTML = list.map(r => `
        <tr>
          <td>${{r.TH}}</td>
          <td>${{r.Amt}}</td>
          <td>${{r.Kategorie}}</td>
          <td>${{r.Massnahme}}</td>
          <td>${{r.Kuerzung_5_Prozent_Freiwillig ? "✅ 5%" : "—"}}</td>
          <td class="num">${{fmtEur(r.Bisher_2026, 0)}}</td>
          <td class="num" style="color:${{r.Aenderung_2026 < 0 ? '#16a34a' : '#dc2626'}}">${{r.Aenderung_2026 >= 0 ? "+" : ""}}${{fmtEur(r.Aenderung_2026, 0)}}</td>
          <td class="num">${{fmtEur(r.Neu_2026, 0)}}</td>
        </tr>
      `).join("");
    }}

    // ================= TAB 5 =================
    function renderTab5() {{
      const plotBilanz = (seite, divId, title) => {{
        const sub = RAW.bilanz.filter(r => r.Seite === seite);
        const posList = Array.from(new Set(sub.map(r => r.Position)));
        const traces = posList.map(pos => {{
          const pts = sub.filter(r => r.Position === pos).sort((a,b) => a.Jahr - b.Jahr);
          return {{
            type: "scatter",
            mode: "lines",
            stackgroup: "one",
            name: pos,
            x: pts.map(p => p.Jahr),
            y: pts.map(p => p.Betrag_TEUR)
          }};
        }});
        Plotly.react(divId, traces, {{
          title,
          xaxis: {{ dtick: 1 }},
          yaxis: {{ title: "T€" }},
          legend: {{ orientation: "h", y: -0.25, font: {{ size: 10 }} }},
          margin: {{ t: 45, l: 65, r: 20, b: 95 }}
        }}, {{ responsive: true }});
      }};

      plotBilanz("Aktiva", "chartBilanzAkt", "Aktiva-Entwicklung 2015–2024 (in T€, Bilanzsumme 1,78 Mrd. €)");
      plotBilanz("Passiva", "chartBilanzPas", "Passiva-Entwicklung 2015–2024 (Eigenkapital, Rücklagen, Schulden in T€)");

      const vorb = [...RAW.vorbelastungen].sort((a,b) => a.Stand_2024_TEUR - b.Stand_2024_TEUR);
      Plotly.react("chartVorbelastungen", [{{
        type: "bar",
        orientation: "h",
        y: vorb.map(r => shortAmt(r.Kategorie)),
        x: vorb.map(r => r.Stand_2024_TEUR),
        marker: {{ color: "#ea580c" }},
        hovertemplate: "<b>%{{y}}</b><br>Stand 2024: <b>%{{x:,.0f}} T€</b><extra></extra>"
      }}], {{
        title: "Außerbilanzielle Vorbelastungen zum 31.12.2024 (1,221 Mrd. € gesamt, in T€)",
        margin: {{ t: 45, l: 210, r: 25, b: 40 }}
      }}, {{ responsive: true }});

      const tbodyBet = document.querySelector("#tblBeteiligungen tbody");
      tbodyBet.innerHTML = RAW.beteiligungen.map(r => `
        <tr>
          <td><strong>${{r.Einheit}}</strong></td>
          <td>${{r.Aufgabenfeld}}</td>
          <td class="num">${{Number(r.Ertraege_2026_TEUR).toLocaleString("de-DE")}}</td>
          <td class="num">${{Number(r.Aufwendungen_2026_TEUR).toLocaleString("de-DE")}}</td>
          <td class="num" style="color:${{r.Jahresergebnis_2026_TEUR >= 0 ? '#16a34a' : '#dc2626'}}">${{Number(r.Jahresergebnis_2026_TEUR).toLocaleString("de-DE")}}</td>
          <td class="num">${{Number(r.Schulden_Ende_2026_TEUR).toLocaleString("de-DE")}}</td>
        </tr>
      `).join("");

      const ja = RAW.ja2024_aemter
        .filter(r => String(r.Position).toLowerCase().includes("anteiliges ordentliches ergebnis") && String(r.TH) !== "FW")
        .sort((a,b) => a.Abweichung_2024 - b.Abweichung_2024)
        .slice(0, 20);

      Plotly.react("chartJa2024", [{{
        type: "bar",
        orientation: "h",
        y: ja.map(r => shortAmt(r.Amt)),
        x: ja.map(r => r.Abweichung_2024),
        marker: {{ color: ja.map(r => r.Abweichung_2024 >= 0 ? "#16a34a" : "#dc2626") }},
        hovertemplate: "<b>%{{y}}</b><br>Abweichung 2024: <b>%{{x:+,.0f}} €</b><extra></extra>"
      }}], {{
        title: "Jahresabschluss 2024: Größte Budgetabweichungen (Ist vs. Plan je Amt, €)",
        margin: {{ t: 45, l: 210, r: 25, b: 40 }}
      }}, {{ responsive: true }});

      const pers = RAW.personal
        .filter(r => r.Jahr === 2025)
        .sort((a,b) => b.Planstellen - a.Planstellen)
        .slice(0, 20)
        .reverse();

      Plotly.react("chartPersonal", [
        {{ type: "bar", orientation: "h", name: "Beamte (733,75)", y: pers.map(r => shortAmt(r.Amt)), x: pers.map(r => r.Beamte_Stellen), marker: {{ color: "#1d4ed8" }} }},
        {{ type: "bar", orientation: "h", name: "Tarifbeschäftigte (1.924,25)", y: pers.map(r => shortAmt(r.Amt)), x: pers.map(r => r.Tarif_Stellen), marker: {{ color: "#0d9488" }} }}
      ], {{
        barmode: "stack",
        title: "Top 20 Ämter nach Planstellen 2025/2026 (2.658 Stellen gesamt)",
        legend: {{ orientation: "h", y: 1.08 }},
        margin: {{ t: 50, l: 210, r: 25, b: 40 }}
      }}, {{ responsive: true }});
    }}

    function renderActiveTab() {{
      if (state.activeTab === "tab1") renderTab1();
      else if (state.activeTab === "tab2") {{ renderTab2Growth(); renderTab2TS(); }}
      else if (state.activeTab === "tab3") renderTab3();
      else if (state.activeTab === "tab4") renderTab4();
      else if (state.activeTab === "tab5") renderTab5();
    }}

    function refreshAll() {{
      updateKPIs();
      renderActiveTab();
    }}

    initControls();
    refreshAll();
  </script>
</body>
</html>
"""
    out_path = DOCS_DIR / "index.html"
    out_path.write_text(html, encoding="utf-8")
    return out_path


if __name__ == "__main__":
    p = build_static_dashboard()
    print(f"Generated static dashboard: {p} ({p.stat().st_size:,} bytes)")
