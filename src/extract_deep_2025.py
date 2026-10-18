import pymupdf
import pandas as pd
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent
NUM_RE = re.compile(r"^\*?[-+]?\d{1,3}(?:\.\d{3})*(?:,\d+)?-?(?:\d\))?$")


def parse_num(s: str) -> float:
    s = re.sub(r"\d\)$", "", s.lstrip("*").strip())
    neg = s.endswith("-") or s.startswith("-")
    s = s.strip("-+").replace(".", "").replace(",", ".").strip()
    val = float(s)
    return -val if neg else val


# Canonical category classification for I. Gesamtbudget rows
# Checked in order: Aufwendungen before Erträge so 'Zinsen und ähnliche Aufwendungen' never matches 'Zinsen'.
CANONICAL_CATS = [
    ("Personalaufwendungen", "Personalaufwendungen", "Aufwendungen"),
    ("Personal- und Versorgungsaufwendungen", "Personalaufwendungen", "Aufwendungen"),
    ("Versorgungsaufwendungen", "Versorgungsaufwendungen", "Aufwendungen"),
    ("Aufwendungen für Sach-", "Aufwendungen für Sach- und Dienstleistungen", "Aufwendungen"),
    ("Planmäßige Abschreibungen", "Abschreibungen", "Aufwendungen"),
    ("Abschreibungen", "Abschreibungen", "Aufwendungen"),
    ("Zinsen und ähnliche Aufwendungen", "Zinsen und ähnliche Aufwendungen", "Aufwendungen"),
    ("Transferaufwendungen", "Transferaufwendungen", "Aufwendungen"),
    ("Sonstige ordentliche Aufwendungen", "Sonstige ordentliche Aufwendungen", "Aufwendungen"),
    ("Weitere ordentliche Aufwendungen", "Sonstige ordentliche Aufwendungen", "Aufwendungen"),
    ("Globaler Minderaufwand", "Sonstige ordentliche Aufwendungen", "Aufwendungen"),
    # Erträge
    ("Steuern und", "Steuern und ähnliche Abgaben", "Erträge"),
    ("Zuweisungen", "Zuweisungen, Zuwendungen und Umlagen", "Erträge"),
    ("Aufgelöste Investitions", "Aufgelöste Investitionszuwendungen und -beiträge", "Erträge"),
    ("Sonstige Transfererträge", "Sonstige Transfererträge", "Erträge"),
    ("Öffentlich-rechtliche Entgelte", "Entgelte für öffentliche Leistungen oder Einrichtungen", "Erträge"),
    ("Entgelte für öffentliche", "Entgelte für öffentliche Leistungen oder Einrichtungen", "Erträge"),
    ("Privatrechtliche Leistungsentgelte", "Sonstige Privatrechtliche Leistungsentgelte", "Erträge"),
    ("Sonstige Privatrechtliche", "Sonstige Privatrechtliche Leistungsentgelte", "Erträge"),
    ("Kostenerstattungen", "Kostenerstattungen und Kostenumlagen", "Erträge"),
    ("Zinsen und ähnliche Erträge", "Zinsen und ähnliche Erträge", "Erträge"),
    ("Aktivierte Eigenleistungen", "Aktivierte Eigenleistungen und Bestandsveränderungen", "Erträge"),
    ("Sonstige ordentliche Erträge", "Sonstige ordentliche Erträge", "Erträge"),
    ("Bußgelder", "Sonstige ordentliche Erträge", "Erträge"),
]

OFFICIAL_AMT_NAMES = {
    "01": "TH 01 Referat des Oberbürgermeisters",
    "11": "TH 11 Personal- und Organisationsamt",
    "12": "TH 12 Amt für Stadtentwicklung und Statistik",
    "12-KW": "TH 12-KW Stabsstelle Kultur- und Kreativwirtschaft",
    "KKW": "TH 12-KW Stabsstelle Kultur- und Kreativwirtschaft",
    "13": "TH 13 Amt für Öffentlichkeitsarbeit",
    "14": "TH 14 Rechnungsprüfungsamt",
    "15": "TH 15 Bürger- und Ordnungsamt",
    "16": "TH 16 Amt für Chancengleichheit",
    "16-IZ": "TH 16-IZ Geschäftsstelle Interkulturelles Zentrum",
    "IZ": "TH 16-IZ Geschäftsstelle Interkulturelles Zentrum",
    "17": "TH 17 Amt für Digitales und Informationsverarbeitung",
    "19": "TH 65 Hochbauamt",
    "20": "TH 20 Kämmereiamt",
    "20-KV": "TH 23-KV Stabsstelle Konversion",
    "KV": "TH 23-KV Stabsstelle Konversion",
    "23": "TH 23 Amt für Liegenschaften",
    "23-01 SW": "TH 23-SW Team Wohnen und aktive Bodenpolitik",
    "02-01": "TH 23-SW Team Wohnen und aktive Bodenpolitik",
    "23-02 KV": "TH 23-KV Stabsstelle Konversion",
    "02-02": "TH 23-KV Stabsstelle Konversion",
    "24": "TH 23-KV Stabsstelle Konversion",
    "30": "TH 30 Rechtsamt",
    "31": "TH 31 Amt für Umweltschutz, Gewerbeaufsicht und Energie",
    "34": "TH 34 Standesamt",
    "37": "TH 37 Feuerwehr",
    "40": "TH 40 Amt für Schule und Bildung",
    "41": "TH 41 Kulturamt",
    "41-LT": "TH 41-LT Stabsstelle feeLit",
    "LT": "TH 41-LT Stabsstelle feeLit",
    "42": "TH 42 Kurpfälzisches Museum",
    "44": "TH 44 Theater und Philharmonisches Orchester",
    "45": "TH 45 Stadtbücherei",
    "46": "TH 46 Musik- und Singschule",
    "47": "TH 47 Stadtarchiv",
    "50": "TH 50 Amt für Soziales und Senioren",
    "50-JC": "TH 50-JC Jobcenter Heidelberg",
    "JC": "TH 50-JC Jobcenter Heidelberg",
    "51": "TH 51 Kinder- und Jugendamt",
    "52": "TH 52 Amt für Sport und Gesundheitsförderung",
    "61": "TH 61 Stadtplanungsamt",
    "61-GB": "TH 61-GB Geschäftsstelle Bahnstadt / Konversion",
    "GB": "TH 61-GB Geschäftsstelle Bahnstadt / Konversion",
    "62": "TH 62 Vermessungsamt",
    "63": "TH 63 Amt für Baurecht und Denkmalschutz",
    "65": "TH 65 Hochbauamt",
    "66": "TH 66 Tiefbauamt",
    "67": "TH 67 Landschafts- und Forstamt (Grünanlagen, Friedhöfe)",
    "68": "TH 67-Forst Landschafts- und Forstamt (Bereich Forst)",
    "70": "TH 70 Abfallwirtschaft und Stadtreinigung",
    "80": "TH 80 Amt für Wirtschaftsförderung und Wissenschaft",
    "81": "TH 81 Amt für Mobilität",
    "FW": "TH FW Allgemeine Finanzwirtschaft",
}


def normalize_amt_name(code_or_header: str) -> str:
    s = code_or_header.strip()
    s_clean = s.replace("Amt ", "").replace("TH ", "").replace(".pdf", "").strip()
    if s_clean in OFFICIAL_AMT_NAMES:
        return OFFICIAL_AMT_NAMES[s_clean]
    if s_clean == "20 - 20":
        return OFFICIAL_AMT_NAMES["20"]
    for k, v in OFFICIAL_AMT_NAMES.items():
        if s_clean.startswith(k + " "):
            if k == "67" and "Forst" in s_clean and "Landschafts" not in s_clean:
                return OFFICIAL_AMT_NAMES["68"]
            return v
    return s


def classify_gb_row(lbl: str):
    for prefix, canon_cat, typ in CANONICAL_CATS:
        if prefix.lower() in lbl.lower():
            return canon_cat, typ
    return None, None


def is_ordentliche_subtotal(rl: str) -> bool:
    return (
        "Anteilige ordentliche" in rl
        or rl in ("Ordentliche Erträge", "Ordentliche Aufwendungen", "Ordentliches Ergebnis")
    )


def extract_4year_tables(text: str, target_years=(2026, 2025, 2024, 2023)):
    y1, y2, y3, y4 = (str(y) for y in target_years)
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    tables = []
    i = 0
    n = len(lines)
    while i < n:
        window = " ".join(lines[i : min(n, i + 14)])
        if (f"Plan {y1}" in lines[i] or f"{y2}/{y1}" in lines[i]) and (f"Plan {y2}" in window or f"{y3}/{y2}" in window) and y4 in window:
            headings = []
            for back in range(i - 1, max(-1, i - 10), -1):
                cand = lines[back]
                if not cand.startswith("Seite |") and not cand.startswith("TH ") and "in €" not in cand:
                    headings.append(cand)
            j = i + 1
            while j < min(n, i + 18):
                if y4 in lines[j]:
                    j += 1
                    if j < n and lines[j] == "in €":
                        j += 1
                    break
                j += 1
            rows = []
            label_parts = []
            while j < n:
                if j + 3 < n and all(NUM_RE.match(lines[j + k]) for k in range(4)):
                    lbl = " ".join(label_parts).strip()
                    lbl = re.sub(r"\s+", " ", lbl)
                    v1, v2, v3, v4 = (parse_num(lines[j + k]) for k in range(4))
                    if lbl:
                        rows.append(
                            (
                                lbl,
                                {
                                    target_years[0]: v1,
                                    target_years[1]: v2,
                                    target_years[2]: v3,
                                    target_years[3]: v4,
                                },
                            )
                        )
                    label_parts = []
                    j += 4
                else:
                    if lines[j].startswith(f"Plan {y1}") or lines[j].startswith(f"{y2}/{y1}"):
                        break
                    if rows and (
                        rows[-1][0].startswith("Summe")
                        or "Veranschlagtes Gesamtergebnis" in rows[-1][0]
                        or rows[-1][0] == "Gesamtergebnis"
                        or "insgesamt" in rows[-1][0]
                    ):
                        break
                    label_parts.append(lines[j])
                    j += 1
                    if len(label_parts) > 6:
                        break
            if rows:
                tables.append({"headings": headings, "rows": rows})
            i = j
        else:
            i += 1
    return tables


def extract_pdf_deep(pdf_path: Path, table_years: tuple[int, int, int, int], emit_years: tuple[int, ...]) -> tuple[list[dict], list[dict]]:
    doc = pymupdf.open(str(pdf_path))
    gb_pages = []
    for p_idx in range(50, len(doc)):
        txt = doc[p_idx].get_text("text")
        if ("I. Gesamtbudget" in txt or "Gesamtbudget" in txt) and ("Anteilige ordentliche" in txt or ("I. Gesamtbudget" in txt and "Personalaufwendungen" in txt)):
            tbls = extract_4year_tables(txt, table_years)
            if any(any(is_ordentliche_subtotal(r[0]) for r in t["rows"]) for t in tbls):
                hdr_line = ""
                for ln in txt.splitlines()[:6]:
                    ls = ln.strip()
                    if ls.startswith("TH "):
                        hdr_line = ls
                        break
                if hdr_line:
                    if "Teilbudget" in txt and "I. Gesamtbudget" not in txt:
                        continue
                    gb_pages.append((p_idx, hdr_line))

    print(f"[{pdf_path.name}] Extracting {len(gb_pages)} Teilhaushalte for years {emit_years}...")
    deep_records = []
    amt_records = []

    for idx, (gb_p_idx, hdr_line) in enumerate(gb_pages):
        end_p_idx = gb_pages[idx + 1][0] if idx + 1 < len(gb_pages) else min(len(doc), gb_p_idx + 35)
        if "TH 67" in hdr_line and ("Forst" in hdr_line and "Landschafts" not in hdr_line):
            amt_name = OFFICIAL_AMT_NAMES["68"]
        else:
            amt_name = normalize_amt_name(hdr_line)

        gb_cat_totals = {}
        gb_special_rows = []
        detail_tables = []

        txt_gb = doc[gb_p_idx].get_text("text")
        for t in extract_4year_tables(txt_gb, table_years):
            rlabels = [r[0] for r in t["rows"]]
            if any(is_ordentliche_subtotal(rl) for rl in rlabels):
                aufw_sub = [v for rl, v in t["rows"] if "Anteilige ordentliche Aufwendungen" in rl or rl == "Ordentliche Aufwendungen"]
                flip_aufw = bool(aufw_sub and any(v < 0 for v in aufw_sub[0].values()))
                for lbl, vals in t["rows"]:
                    if "Anteilige ordentliche Aufwendungen" in lbl or lbl == "Ordentliche Aufwendungen" or "Anteiliges ordentliches Ergebnis" in lbl or lbl == "Ordentliches Ergebnis":
                        break
                    if "Anteilige ordentliche Erträge" in lbl or lbl == "Ordentliche Erträge":
                        continue
                    canon_cat, typ = classify_gb_row(lbl)
                    if canon_cat and typ:
                        norm_vals = dict(vals)
                        if flip_aufw and typ == "Aufwendungen" and "Globaler Minderaufwand" not in lbl:
                            norm_vals = {y: abs(norm_vals[y]) for y in table_years}
                        if "Globaler Minderaufwand" in lbl or "Bußgelder" in lbl:
                            gb_special_rows.append((typ, canon_cat, lbl.replace(" 1)", "").strip(), norm_vals))
                        else:
                            key = (typ, canon_cat)
                            if key not in gb_cat_totals:
                                gb_cat_totals[key] = {y: 0.0 for y in table_years}
                            for y in table_years:
                                gb_cat_totals[key][y] += norm_vals[y]
                break

        # Emit Amt-level category records
        for (typ, canon_cat), tot_vals in gb_cat_totals.items():
            for y in emit_years:
                val = tot_vals[y]
                for s_typ, s_cat, _, s_vals in gb_special_rows:
                    if s_typ == typ and s_cat == canon_cat:
                        val += s_vals[y]
                if val != 0:
                    amt_records.append({
                        "Jahr": y,
                        "Amt": amt_name,
                        "Typ": typ,
                        "Kategorie": canon_cat,
                        "Betrag": val,
                    })

        # Scan Erläuterungen pages
        for p_idx in range(gb_p_idx, end_p_idx):
            txt = doc[p_idx].get_text("text")
            if p_idx > gb_p_idx and (
                "Gesamtbudget nach Produktgruppen" in txt
                or "II. Ziele" in txt
                or "III. Investitionen" in txt
            ):
                break
            tbls = extract_4year_tables(txt, table_years)
            for t in tbls:
                rlabels = [r[0] for r in t["rows"]]
                if p_idx == gb_p_idx and any(is_ordentliche_subtotal(rl) for rl in rlabels):
                    continue
                detail_tables.append((p_idx + 1, t))

        matched_cats = {}

        if amt_name == OFFICIAL_AMT_NAMES["FW"]:
            for p_idx in range(gb_p_idx + 1, end_p_idx):
                txt = doc[p_idx].get_text("text")
                if "III. Investitionen" in txt:
                    break
                if "Grundsteuer A" in txt and "Teilbudget" in txt:
                    tbls = extract_4year_tables(txt, table_years)
                    if tbls:
                        t6110 = tbls[0]
                        aufw_sub_fw = [v for rl, v in t6110["rows"] if "Anteilige ordentliche Aufwendungen" in rl]
                        flip_fw = bool(aufw_sub_fw and any(v < 0 for v in aufw_sub_fw[0].values()))
                        steuern_rows = []
                        zuw_rows = []
                        transf_rows = []
                        mode_fw = "Erträge"
                        for lbl, vals in t6110["rows"]:
                            if "Anteilige ordentliche Erträge" in lbl:
                                mode_fw = "Aufwendungen"
                                continue
                            if "Anteilige ordentliche Aufwendungen" in lbl or "Anteiliges ordentliche" in lbl:
                                break
                            if mode_fw == "Erträge":
                                if any(
                                    k in lbl
                                    for k in (
                                        "Schlüsselzuweisungen",
                                        "Zuweisungen nach",
                                        "Sonderzuweisungen",
                                        "Grunderwerbsteuer",
                                        "Investitionspauschale",
                                    )
                                ):
                                    zuw_rows.append((lbl, vals))
                                elif "Auflösung von Rückstellungen" in lbl or "Sonstige ordentliche" in lbl:
                                    pass
                                else:
                                    steuern_rows.append((lbl, vals))
                            else:
                                if "Absetzung von Forderungen" not in lbl and "Abschreibungen" not in lbl:
                                    norm_v = {y: abs(vals[y]) for y in table_years} if flip_fw else vals
                                    transf_rows.append((lbl, norm_v))
                        if steuern_rows:
                            matched_cats[("Erträge", "Steuern und ähnliche Abgaben")] = steuern_rows
                        if zuw_rows:
                            matched_cats[("Erträge", "Zuweisungen, Zuwendungen und Umlagen")] = zuw_rows
                        if transf_rows:
                            matched_cats[("Aufwendungen", "Transferaufwendungen")] = transf_rows
            if 2026 in emit_years:
                matched_cats[("Aufwendungen", "Zinsen und ähnliche Aufwendungen")] = [
                    ("Zinsaufwendungen für Darlehen", {2026: 11619000.0, 2025: 10077000.0, 2024: 4859000.0, 2023: 2971290.0}),
                    ("Zinsaufwendungen an die BSG im Rahmen von ÖPP-Projekten", {2026: 1011000.0, 2025: 1046200.0, 2024: 1100200.0, 2023: 1162182.0}),
                    ("Kreditbeschaffungskosten", {2026: 121000.0, 2025: 121000.0, 2024: 121000.0, 2023: 0.0}),
                    ("Verzinsung von Rückstellungen", {2026: 0.0, 2025: 0.0, 2024: 0.0, 2023: 219649.0}),
                ]

        cleaned_detail_tables = []
        for pg_no, t in detail_tables:
            rows = t["rows"]
            non_sum_rows = [
                (lbl, vals)
                for lbl, vals in rows
                if not lbl.startswith("Summe") and "insgesamt" not in lbl and not is_ordentliche_subtotal(lbl)
            ]
            if not non_sum_rows:
                continue
            sums = {y: sum(vals[y] for _, vals in non_sum_rows) for y in table_years}
            merged_into_prev = False
            if cleaned_detail_tables:
                prev_pg, prev_t, prev_rows = cleaned_detail_tables[-1]
                for idx_r, (r_lbl, r_vals) in enumerate(prev_rows):
                    if all(abs(r_vals[y] - sums[y]) < 5.0 for y in table_years) and any(sums[y] != 0 for y in table_years):
                        clean_parent = re.sub(r"[\*\d\)\s]+$", "", r_lbl).strip()
                        expanded = [(f"{clean_parent}: {sub_l}", sub_v) for sub_l, sub_v in non_sum_rows]
                        prev_rows[idx_r : idx_r + 1] = expanded
                        merged_into_prev = True
                        break
            if not merged_into_prev:
                cleaned_detail_tables.append((pg_no, t, non_sum_rows))

        for pg_no, t, non_sum_rows in cleaned_detail_tables:
            sums = {y: sum(vals[y] for _, vals in non_sum_rows) for y in table_years}
            matched_key = None
            for key, tot_vals in gb_cat_totals.items():
                if key in matched_cats:
                    continue
                if all(abs(tot_vals[y] - sums[y]) < 5.0 for y in table_years) and any(sums[y] != 0 for y in table_years):
                    matched_key = key
                    break
            if not matched_key:
                for h in t["headings"]:
                    c_cat, c_typ = classify_gb_row(h)
                    if c_cat and c_typ and (c_typ, c_cat) in gb_cat_totals and (c_typ, c_cat) not in matched_cats:
                        tot_vals = gb_cat_totals[(c_typ, c_cat)]
                        if all(sums[y] <= tot_vals[y] + 5.0 for y in table_years[:2]) and any(sums[y] > 0 for y in table_years[:2]):
                            matched_key = (c_typ, c_cat)
                            break
            if matched_key:
                matched_cats[matched_key] = non_sum_rows

        for (typ, canon_cat), tot_vals in gb_cat_totals.items():
            if (typ, canon_cat) in matched_cats:
                sub_rows = matched_cats[(typ, canon_cat)]
                for sub_lbl, vals in sub_rows:
                    clean_lbl = sub_lbl.lstrip("*").strip()
                    for y in emit_years:
                        if vals[y] != 0:
                            deep_records.append({
                                "Jahr": y,
                                "Amt": amt_name,
                                "Kategorie": canon_cat,
                                "Sub_Kategorie": clean_lbl,
                                "Typ": typ,
                                "Betrag": vals[y],
                            })
                for y in emit_years:
                    sub_sum = sum(vals[y] for _, vals in sub_rows)
                    diff = round(tot_vals[y] - sub_sum, 2)
                    if abs(diff) >= 1.0:
                        deep_records.append({
                            "Jahr": y,
                            "Amt": amt_name,
                            "Kategorie": canon_cat,
                            "Sub_Kategorie": f"Weitere Positionen ({canon_cat})",
                            "Typ": typ,
                            "Betrag": diff,
                        })
            else:
                for y in emit_years:
                    if tot_vals[y] != 0:
                        deep_records.append({
                            "Jahr": y,
                            "Amt": amt_name,
                            "Kategorie": canon_cat,
                            "Sub_Kategorie": canon_cat,
                            "Typ": typ,
                            "Betrag": tot_vals[y],
                        })

        for typ, canon_cat, sub_lbl, vals in gb_special_rows:
            for y in emit_years:
                if vals[y] != 0:
                    deep_records.append({
                        "Jahr": y,
                        "Amt": amt_name,
                        "Kategorie": canon_cat,
                        "Sub_Kategorie": sub_lbl,
                        "Typ": typ,
                        "Betrag": vals[y],
                    })

    doc.close()
    return deep_records, amt_records


def main():
    root_dir = Path(__file__).resolve().parent.parent
    pdf_dir = root_dir / "input" / "pdfs"
    data_dir = root_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    pdf_configs = [
        (pdf_dir / "20_pdf_hh_2015_16_Haushaltsplanentwurf.pdf", (2016, 2015, 2014, 2013), (2016, 2015, 2014, 2013)),
        (pdf_dir / "20_pdf_hh_2019_2020_Haushaltsplan.pdf", (2020, 2019, 2018, 2017), (2018, 2017)),
        (pdf_dir / "20_pdf_hh_2021_2022_Haushaltsplan.pdf", (2022, 2021, 2020, 2019), (2020, 2019)),
        (pdf_dir / "20_pdf_hh_2023_2024_Haushaltsplan.pdf", (2024, 2023, 2022, 2021), (2022, 2021)),
        (pdf_dir / "20_pdf_haushaltsplan 2025_2026_web.pdf", (2026, 2025, 2024, 2023), (2026, 2025, 2024, 2023)),
    ]

    all_deep = []
    all_amt = []
    for pdf_p, tbl_yrs, emit_yrs in pdf_configs:
        if pdf_p.exists():
            d_rec, a_rec = extract_pdf_deep(pdf_p, tbl_yrs, emit_yrs)
            all_deep.extend(d_rec)
            all_amt.extend(a_rec)

    df_deep = pd.DataFrame(all_deep)
    df_deep = df_deep[df_deep["Betrag"] != 0].sort_values(["Jahr", "Amt", "Typ", "Kategorie", "Sub_Kategorie"])
    df_deep.to_csv(data_dir / "haushalt_heidelberg_deep.csv", index=False, encoding="utf-8")

    df_amt = pd.DataFrame(all_amt)
    df_amt = df_amt.groupby(["Jahr", "Amt", "Typ", "Kategorie"], as_index=False)["Betrag"].sum()
    df_amt.to_csv(data_dir / "haushalt_heidelberg_aemter.csv", index=False, encoding="utf-8")

    print(f"Saved {len(df_deep)} rows to {data_dir / 'haushalt_heidelberg_deep.csv'} and {len(df_amt)} rows to {data_dir / 'haushalt_heidelberg_aemter.csv'}")


if __name__ == "__main__":
    main()
