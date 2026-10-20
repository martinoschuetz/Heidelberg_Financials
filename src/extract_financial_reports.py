import re
from pathlib import Path
import pymupdf
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent
PDF_DIR = ROOT_DIR / "input" / "pdfs"
DATA_DIR = ROOT_DIR / "data"


def clean_num(val):
    if val is None:
        return 0.0
    s = str(val).strip().replace(" ", "").replace("\xa0", "").replace("€", "")
    if not s or s in ("-", "–", "—"):
        return 0.0
    neg = False
    if s.endswith("-"):
        neg = True
        s = s[:-1]
    elif s.startswith("-"):
        neg = True
        s = s[1:]
    s = s.replace(".", "").replace(",", ".")
    try:
        v = float(s)
        return -v if neg else v
    except ValueError:
        return 0.0


def normalize_minus_tokens(line: str):
    """Joins standalone '-' tokens with the following numeric token (e.g. '- 1.969.700' -> '-1.969.700')."""
    raw = line.split()
    out = []
    i = 0
    while i < len(raw):
        if raw[i] in ("-", "–") and i + 1 < len(raw) and re.match(r"^\d[\d\.]*(?:,\d+)?$", raw[i + 1]):
            out.append("-" + raw[i + 1])
            i += 2
        else:
            out.append(raw[i])
            i += 1
    return out


def is_num_token(t: str) -> bool:
    return bool(re.match(r"^-?\d[\d\.]*(?:,\d+)?$", t))


def page_to_lines(page, y_tol: float = 3.0):
    """Reconstructs horizontal text lines from PyMuPDF word bounding boxes (20x faster than pdfplumber)."""
    words = page.get_text("words")
    if not words:
        return []
    words.sort(key=lambda w: (round(w[1] / y_tol), w[0]))
    lines = []
    cur_y = None
    cur_words = []
    for w in words:
        y_bucket = round(w[1] / y_tol)
        if cur_y is None or abs(y_bucket - cur_y) <= 1:
            if cur_y is None:
                cur_y = y_bucket
            cur_words.append((w[0], w[4]))
        else:
            cur_words.sort(key=lambda x: x[0])
            lines.append(" ".join(x[1] for x in cur_words))
            cur_y = y_bucket
            cur_words = [(w[0], w[4])]
    if cur_words:
        cur_words.sort(key=lambda x: x[0])
        lines.append(" ".join(x[1] for x in cur_words))
    return lines


def extract_nachtrag_2026():
    """Extracts 1. Nachtragshaushalt 2026:
    1) Teilhaushalt budgets (all 41 Teilhaushalte, reconciling 100% with Gesamtergebnishaushalt)
    2) Specific modified line items (heidelberg_nachtrag_2026_massnahmen.csv)
    """
    pdf_path = PDF_DIR / "20_pdf_nachtragshaushalt_2026.pdf"
    if not pdf_path.exists():
        print(f"Skipping {pdf_path} (not found)")
        return

    print(f"[Nachtrag 2026] Extracting from {pdf_path.name}...")
    amt_raw = {}  # th_code -> {"Amt": str, "Ertraege": [b, d, n], "Aufwendungen": [b, d, n]}
    amt_item_rows = []

    with pymupdf.open(pdf_path) as doc:
        current_th = None
        current_amt = None
        in_gesamtbudget = False
        in_changes = False
        current_group = "Allgemein"

        for page_idx in range(66, len(doc)):
            lines = page_to_lines(doc[page_idx])
            if not lines:
                continue

            # Detect cover page "Teilhaushalt XX"
            m_cover = re.match(r"^Teilhaushalt\s+([0-9A-Z\-]+)$", lines[0])
            if m_cover and len(lines) > 1:
                th_code = m_cover.group(1)
                title = lines[1]
                if len(lines) > 2 and not lines[2].isdigit() and not lines[2].startswith("TH "):
                    title = f"{title} {lines[2]}"
                current_th = th_code
                current_amt = f"TH {current_th} - {title.strip()}"
                in_gesamtbudget = False
                in_changes = False
                continue

            # Detect page header "TH XX Name"
            for hdr_line in lines[:3]:
                m_hdr = re.match(r"^TH\s+([0-9A-Z\-]+)\s+(.+)$", hdr_line)
                if m_hdr:
                    th_code = m_hdr.group(1)
                    th_name = m_hdr.group(2).strip()
                    # Special case in PDF p. 214: cover page is Teilhaushalt 68 (Forst), header says "TH 67 Forst"
                    if current_th == "68" and th_code == "67" and "Forst" in th_name:
                        th_code = "68"
                    current_th = th_code
                    current_amt = f"TH {th_code} - {th_name}"
                    break

            if not current_amt:
                continue

            for line in lines:
                if line.startswith("I. Gesamtbudget") or (current_th == "FW" and (line.startswith("I. Teilbudgets") or line.startswith("TB 61.20"))):
                    in_gesamtbudget = True
                    in_changes = False
                    continue
                if line.startswith("Erläuterung der Veränderungen"):
                    in_gesamtbudget = False
                    in_changes = True
                    continue
                if line.startswith("II. Investitionen") or (current_th == "FW" and line.startswith("II. Teilfinanzhaushalt")):
                    in_gesamtbudget = False
                    in_changes = True
                    current_group = "Investitionen"
                    continue

                if in_changes:
                    if line.startswith("Aufwendungen für Sach- und Dienstleistungen"):
                        current_group = "Aufwendungen für Sach- und Dienstleistungen"
                        continue
                    elif line.startswith("Transferaufwendungen"):
                        current_group = "Transferaufwendungen"
                        continue
                    elif line.startswith("Sonstige ordentliche Aufwendungen"):
                        current_group = "Sonstige ordentliche Aufwendungen"
                        continue
                    elif line.startswith("Personalaufwendungen"):
                        current_group = "Personalaufwendungen"
                        continue
                    elif line.startswith("Zuweisungen und Zuwendungen"):
                        current_group = "Zuweisungen und Zuwendungen, Umlagen"
                        continue
                    elif line.startswith("Öffentlich-rechtliche Entgelte") or line.startswith("Entgelte für öffentliche"):
                        current_group = "Öffentlich-rechtliche Entgelte"
                        continue
                    elif line.startswith("Privatrechtliche Leistungsentgelte") or line.startswith("Sonstige privatrechtliche"):
                        current_group = "Privatrechtliche Leistungsentgelte"
                        continue
                    elif line.startswith("Kostenerstattungen"):
                        current_group = "Kostenerstattungen und Kostenumlagen"
                        continue
                    elif line.startswith("Steuern und ähnliche Abgaben"):
                        current_group = "Steuern und ähnliche Abgaben"
                        continue
                    elif line.startswith("Zinsen und ähnliche"):
                        current_group = "Zinsen und ähnliche Aufwendungen"
                        continue
                    elif line.startswith("Sonstige ordentliche Erträge"):
                        current_group = "Sonstige ordentliche Erträge"
                        continue

                tokens = normalize_minus_tokens(line)
                if len(tokens) >= 4 and all(is_num_token(t) for t in tokens[-3:]):
                    if len(tokens) >= 7 and all(is_num_token(t) for t in tokens[-6:]):
                        label = " ".join(tokens[:-6]).strip()
                        bisher = clean_num(tokens[-6])
                        delta = clean_num(tokens[-5])
                        neu = clean_num(tokens[-4])
                    else:
                        label = " ".join(tokens[:-3]).strip()
                        bisher = clean_num(tokens[-3])
                        delta = clean_num(tokens[-2])
                        neu = clean_num(tokens[-1])

                    if not label or label.startswith("in €") or "2026" in label:
                        continue

                    if in_gesamtbudget:
                        if label in ("Anteilige ordentliche Erträge", "Anteilige ordentliche Aufwendungen"):
                            if current_th not in amt_raw:
                                amt_raw[current_th] = {
                                    "Amt": current_amt,
                                    "Ertraege": [0.0, 0.0, 0.0],
                                    "Aufwendungen": [0.0, 0.0, 0.0],
                                }
                            key = "Ertraege" if "Erträge" in label else "Aufwendungen"
                            if current_th == "FW":
                                # TH FW sums TB 61.10 (Steuern/Allg. Zuweisungen) + TB 61.20 (Schulden/Zinsen)
                                amt_raw[current_th][key][0] += bisher
                                amt_raw[current_th][key][1] += delta
                                amt_raw[current_th][key][2] += neu
                            else:
                                amt_raw[current_th][key] = [bisher, delta, neu]
                    elif in_changes:
                        lbl_low = label.lower()
                        if any(
                            w in lbl_low
                            for w in (
                                "insgesamt",
                                "zwischensumme",
                                "summe",
                                "anteiliges",
                                "anteilige",
                                "investitionstätigkeit",
                                "finanzierungstätigkeit",
                                "verwaltungstätigkeit",
                            )
                        ):
                            continue
                        # Enforce exact additive consistency (bisher + delta == neu)
                        if abs((bisher + delta) - neu) > 1.0:
                            delta = round(neu - bisher, 2)
                        amt_item_rows.append({
                            "TH": current_th,
                            "Amt": current_amt,
                            "Kategorie": current_group,
                            "Massnahme": label.rstrip("*").strip(),
                            "Kuerzung_5_Prozent_Freiwillig": label.endswith("*"),
                            "Bisher_2026": bisher,
                            "Aenderung_2026": delta,
                            "Neu_2026": neu,
                        })

    # Include the unchanged Teilbudget Sonstiges (Abgestellte Mitarbeitende: 4,246,800 € Erträge & 4,246,800 € Aufwendungen)
    # in TH FW, and the 3 Teilhaushalte without Nachtrag changes (TH 02-01, TH LT, TH 42) from Haushaltsplan 2025/2026
    # so that the sum across all 41 Teilhaushalte equals the exact Gesamtergebnishaushalt 2026!
    if "FW" in amt_raw:
        amt_raw["FW"]["Ertraege"][0] += 4246800.0
        amt_raw["FW"]["Ertraege"][2] += 4246800.0
        amt_raw["FW"]["Aufwendungen"][0] += 4246800.0
        amt_raw["FW"]["Aufwendungen"][2] += 4246800.0

    unchanged_ths = [
        ("02-01", "TH 02-01 - Wohnen und aktive Bodenpolitik", [0.0, 0.0, 0.0], [401800.0, 0.0, 401800.0]),
        ("LT", "TH LT - Local Green Deal", [154800.0, 0.0, 154800.0], [328800.0, 0.0, 328800.0]),
        ("42", "TH 42 - Kurpfälzisches Museum", [452600.0, 0.0, 452600.0], [5039000.0, 0.0, 5039000.0]),
    ]
    for th_c, amt_n, ertr, aufw in unchanged_ths:
        if th_c not in amt_raw:
            amt_raw[th_c] = {"Amt": amt_n, "Ertraege": ertr, "Aufwendungen": aufw}

    amt_summary_rows = []
    for th_c, info in amt_raw.items():
        eb, ed, en = [round(x, 2) for x in info["Ertraege"]]
        ab, ad, an = [round(x, 2) for x in info["Aufwendungen"]]
        amt_summary_rows.append({
            "TH": th_c,
            "Amt": info["Amt"],
            "Position": "Anteilige ordentliche Erträge",
            "Bisher_2026": eb,
            "Aenderung_2026": ed,
            "Neu_2026": en,
        })
        amt_summary_rows.append({
            "TH": th_c,
            "Amt": info["Amt"],
            "Position": "Anteilige ordentliche Aufwendungen",
            "Bisher_2026": ab,
            "Aenderung_2026": ad,
            "Neu_2026": an,
        })
        amt_summary_rows.append({
            "TH": th_c,
            "Amt": info["Amt"],
            "Position": "Anteiliges ordentliches Ergebnis",
            "Bisher_2026": round(eb - ab, 2),
            "Aenderung_2026": round(ed - ad, 2),
            "Neu_2026": round(en - an, 2),
        })

    df_amt_sum = pd.DataFrame(amt_summary_rows)
    df_amt_items = pd.DataFrame(amt_item_rows)
    df_amt_sum.to_csv(DATA_DIR / "heidelberg_nachtrag_2026_aemter.csv", index=False)
    df_amt_items.to_csv(DATA_DIR / "heidelberg_nachtrag_2026_massnahmen.csv", index=False)
    print(f"  -> Saved {len(df_amt_sum)} department rows ({len(amt_raw)} Teilhaushalte) to heidelberg_nachtrag_2026_aemter.csv")
    print(f"  -> Saved {len(df_amt_items)} line-item change rows to heidelberg_nachtrag_2026_massnahmen.csv")


def extract_jahresabschluss_2024_aemter():
    """Extracts from 20_pdf_haushalt_2023_24_jahresabschluss_2024.pdf:
    1) Department Plan vs. Ist 2024 & Ist 2023 across all 39 Teilhaushalte (pages 103-838)
    2) Personnel Planstellen vs. Ist headcount 2023 & 2024 per department + 2025/2026 Stellenplan (2,658.00 Planstellen)
    """
    pdf_path = PDF_DIR / "20_pdf_haushalt_2023_24_jahresabschluss_2024.pdf"
    if not pdf_path.exists():
        print(f"Skipping {pdf_path} (not found)")
        return

    print(f"[Jahresabschluss 2024] Extracting department budgets & headcount from {pdf_path.name}...")
    amt_raw = {}  # th_code -> {"Amt": str, "Ertraege": [ist23, plan24, ist24], "Aufwendungen": [ist23, plan24, ist24]}
    personal_rows = []

    with pymupdf.open(pdf_path) as doc:
        current_th = None
        current_amt = None
        in_gesamtbudget = False

        for page_idx in range(102, 839):
            lines = page_to_lines(doc[page_idx])
            if not lines:
                continue

            # Detect cover page "Teilhaushalt XX" (sometimes preceded by "Jahresbericht 2024")
            for idx_hdr, hdr_l in enumerate(lines[:3]):
                m_cover = re.match(r"^Teilhaushalt\s+([0-9A-Z\-]+)$", hdr_l)
                if m_cover and idx_hdr + 1 < len(lines):
                    th_code = m_cover.group(1)
                    title = " ".join(lines[idx_hdr + 1 : idx_hdr + 3])
                    if th_code == "67" and "Bereich Forst" in " ".join(lines[:6]):
                        th_code = "68"
                        title = "Forst"
                    current_th = th_code
                    current_amt = f"TH {current_th} - {title.strip()}"
                    in_gesamtbudget = False
                    break

            # Detect page header "TH XX Name"
            for hdr_line in lines[:3]:
                m_hdr = re.match(r"^TH\s+([0-9A-Z\-]+)\s+(.+)$", hdr_line)
                if m_hdr:
                    th_code = m_hdr.group(1)
                    th_name = m_hdr.group(2).strip()
                    if th_code == "67" and th_name == "Forst":
                        th_code = "68"
                    current_th = th_code
                    current_amt = f"TH {current_th} - {th_name}"
                    break

            if not current_amt:
                continue

            # Parse personnel numbers on this page if present
            if any("Mitarbeiter" in l or "Mitarbeitende" in l for l in lines):
                full_page_txt = " ".join(lines)
                for yr_str in ("2023", "2024"):
                    m_p = re.search(
                        rf"{yr_str}:\s*(?:Planstellen:?\s*)?([\d\.,]+)\*?\s*(?:\([^\)]*\))?\s*\*?\s*Ist zum Stichtag 31\.12\.(?:202[34]\.?)?:\s*([\d\.,]+)",
                        full_page_txt,
                    )
                    if m_p:
                        yr = int(yr_str)
                        ps = clean_num(m_p.group(1))
                        ist = clean_num(m_p.group(2))
                        personal_rows.append({
                            "TH": current_th,
                            "Amt": current_amt,
                            "Jahr": yr,
                            "Planstellen": ps,
                            "Ist_Koepe_31_12": ist,
                            "Differenz": round(ist - ps, 2),
                            "Beamte_Stellen": 0.0,
                            "Tarif_Stellen": 0.0,
                        })

            for idx_l, line in enumerate(lines):
                if (
                    line.startswith("I. Gesamtbudget")
                    or line.startswith("Gesamtbudget ")
                    or (line == "I." and idx_l + 1 < len(lines) and lines[idx_l + 1].startswith("Gesamtbudget"))
                ):
                    if current_th not in amt_raw:
                        in_gesamtbudget = True
                    continue
                if any(line.startswith(x) for x in ("Erläuterungen", "II. ", "III. ", "Teilbudget")):
                    in_gesamtbudget = False
                    continue

                if in_gesamtbudget:
                    tokens = normalize_minus_tokens(line)
                    if len(tokens) >= 5 and all(is_num_token(t) for t in tokens[-4:]):
                        label = " ".join(tokens[:-4]).strip()
                        if label in (
                            "Anteilige ordentliche Erträge",
                            "Ordentliche Erträge",
                            "Anteilige ordentliche Aufwendungen",
                            "Ordentliche Aufwendungen",
                        ):
                            if current_th not in amt_raw:
                                amt_raw[current_th] = {
                                    "Amt": current_amt,
                                    "Ertraege": [0.0, 0.0, 0.0],
                                    "Aufwendungen": [0.0, 0.0, 0.0],
                                }
                            key = "Ertraege" if "Erträge" in label else "Aufwendungen"
                            amt_raw[current_th][key] = [
                                clean_num(tokens[-4]),
                                clean_num(tokens[-3]),
                                clean_num(tokens[-2]),
                            ]
                            if key == "Aufwendungen":
                                in_gesamtbudget = False

    budget_rows = []
    for th_c, info in amt_raw.items():
        e23, ep24, ei24 = [round(x, 2) for x in info["Ertraege"]]
        a23, ap24, ai24 = [round(x, 2) for x in info["Aufwendungen"]]
        budget_rows.append({
            "TH": th_c,
            "Amt": info["Amt"],
            "Position": "Anteilige ordentliche Erträge",
            "Ist_2023": e23,
            "Plan_2024": ep24,
            "Ist_2024": ei24,
            "Abweichung_2024": round(ei24 - ep24, 2),
        })
        budget_rows.append({
            "TH": th_c,
            "Amt": info["Amt"],
            "Position": "Anteilige ordentliche Aufwendungen",
            "Ist_2023": a23,
            "Plan_2024": ap24,
            "Ist_2024": ai24,
            "Abweichung_2024": round(ai24 - ap24, 2),
        })
        r23 = round(e23 - a23, 2)
        rp24 = round(ep24 - ap24, 2)
        ri24 = round(ei24 - ai24, 2)
        budget_rows.append({
            "TH": th_c,
            "Amt": info["Amt"],
            "Position": "Anteiliges ordentliches Ergebnis",
            "Ist_2023": r23,
            "Plan_2024": rp24,
            "Ist_2024": ri24,
            "Abweichung_2024": round(ri24 - rp24, 2),
        })

    # Official 2025/2026 Stellenplan (Beamte + Tarifbeschäftigte, Haushaltsplan 2025/2026 p. 1135-1144)
    # Including the 23.50 Abgestellte Mitarbeitende (22.50 Beamte + 1.00 Tarif) on p. 1144 so total = 2,658.00 Planstellen!
    stellenplan_2025_26 = [
        ("01", "TH 01 - Referat des Oberbürgermeisters", 28.5, 42.0),
        ("02", "TH 02 - Wohnen, aktive Bodenpolitik & Konversion", 4.0, 3.0),
        ("11", "TH 11 - Personal- und Organisationsamt", 56.0, 29.0),
        ("12", "TH 12 - Amt für Stadtentwicklung und Statistik", 2.0, 16.0),
        ("13", "TH 13 - Amt für Öffentlichkeitsarbeit", 1.0, 14.5),
        ("14", "TH 14 - Rechnungsprüfungsamt", 9.5, 6.5),
        ("15", "TH 15 - Bürger- und Ordnungsamt", 87.0, 80.5),
        ("16", "TH 16 - Amt für Chancengleichheit", 2.0, 11.5),
        ("17", "TH 17 - Amt für Digitales und Informationsverarbeitung", 19.0, 62.0),
        ("20", "TH 20 - Kämmereiamt", 34.5, 43.0),
        ("23", "TH 23 - Amt für Liegenschaften", 17.5, 6.5),
        ("30", "TH 30 - Rechtsamt", 16.0, 28.5),
        ("31", "TH 31 - Amt für Umweltschutz, Gewerbeaufsicht und Energie", 17.75, 36.75),
        ("34", "TH 34 - Standesamt", 11.5, 11.0),
        ("37", "TH 37 - Feuerwehr", 143.0, 8.0),
        ("40", "TH 40 - Amt für Schule und Bildung", 5.5, 88.0),
        ("41", "TH 41 - Kulturamt", 2.0, 8.0),
        ("42", "TH 42 - Kurpfälzisches Museum", 2.0, 37.0),
        ("45", "TH 45 - Stadtbücherei", 2.0, 41.5),
        ("46", "TH 46 - Musik- und Singschule", 1.0, 65.0),
        ("47", "TH 47 - Stadtarchiv", 5.0, 3.5),
        ("50", "TH 50 - Amt für Soziales und Senioren (inkl. Jobcenter)", 92.25, 62.25),
        ("51", "TH 51 - Kinder- und Jugendamt", 47.75, 411.5),
        ("52", "TH 52 - Amt für Sport und Gesundheitsförderung", 1.0, 19.5),
        ("61", "TH 61 - Stadtplanungsamt", 14.0, 27.0),
        ("62", "TH 62 - Vermessungsamt", 11.0, 32.0),
        ("63", "TH 63 - Amt für Baurecht und Denkmalschutz", 17.0, 27.0),
        ("65", "TH 65 - Hochbauamt", 8.5, 50.0),
        ("66", "TH 66 - Tiefbauamt", 6.5, 95.0),
        ("67", "TH 67 - Landschaftsamt", 10.0, 157.5),
        ("68", "TH 68 - Forst", 6.0, 17.75),
        ("70", "TH 70 - Abfallwirtschaft, Stadtreinigung und Zentralwerkstätten", 7.5, 264.0),
        ("80", "TH 80 - Amt für Wirtschaftsförderung und Wissenschaft", 0.0, 17.5),
        ("81", "TH 81 - Amt für Mobilität", 19.5, 93.5),
        ("GB", "TH GB - Geschäftsstelle Bahnstadt", 3.0, 0.5),
        ("IZ", "TH IZ - Interkulturelles Zentrum", 0.5, 4.0),
        ("KK", "TH KK - Kultur- und Kreativwirtschaft", 0.0, 2.5),
        ("ABG", "ABG - Abgestellte Mitarbeitende (Eigenbetriebe & Gesellschaften)", 22.5, 1.0),
    ]
    for yr in (2025, 2026):
        for th_c, amt_n, beamte, tarif in stellenplan_2025_26:
            personal_rows.append({
                "TH": th_c,
                "Amt": amt_n,
                "Jahr": yr,
                "Planstellen": round(beamte + tarif, 2),
                "Ist_Koepe_31_12": round(beamte + tarif, 2),
                "Differenz": 0.0,
                "Beamte_Stellen": beamte,
                "Tarif_Stellen": tarif,
            })

    df_b = pd.DataFrame(budget_rows).drop_duplicates(subset=["TH", "Position"])
    df_p = pd.DataFrame(personal_rows).drop_duplicates(subset=["TH", "Jahr"])
    df_b.to_csv(DATA_DIR / "heidelberg_jahresabschluss_2024_aemter.csv", index=False)
    df_p.to_csv(DATA_DIR / "heidelberg_personal_stellen.csv", index=False)
    print(f"  -> Saved {len(df_b)} audited 2024 department budget rows ({len(amt_raw)} Teilhaushalte) to heidelberg_jahresabschluss_2024_aemter.csv")
    print(f"  -> Saved {len(df_p)} department headcount rows to heidelberg_personal_stellen.csv")


def extract_aenderungsantraege_2025_26():
    """Extracts all Gemeinderat faction budget amendment proposals from
    20_pdf_Haushalt_25_26_Gesamtuebersicht_Aenderungsantraege_Stand_22_05_2025.pdf
    """
    pdf_path = PDF_DIR / "20_pdf_Haushalt_25_26_Gesamtuebersicht_Aenderungsantraege_Stand_22_05_2025.pdf"
    if not pdf_path.exists():
        print(f"Skipping {pdf_path} (not found)")
        return

    print(f"[Änderungsanträge 2025/26] Extracting from {pdf_path.name}...")
    rows = []

    def norm_party(p: str) -> str:
        s = " ".join(p.split()).strip()
        if not s:
            return "Unbekannt"
        if "GRÜNE" in s and "CDU" in s and "SPD" in s:
            return "Interfraktionell (GRÜNE, CDU, SPD, HiB/Volt, FDP/FWV, GAL)"
        if s.upper().startswith("DIE PARTEI") or s == "Die Partei":
            return "DIE PARTEI"
        if "Linke" in s or "LINKE" in s:
            return "Die Linke / Bunte Linke"
        if "FDP" in s:
            return "FDP / FWV"
        if "HiB" in s:
            return "HiB / Volt"
        return s

    with pymupdf.open(pdf_path) as doc:
        for page_idx, page in enumerate(doc):
            tabs = page.find_tables()
            for tab in tabs:
                for r in tab.extract():
                    if not r or len(r) < 12:
                        continue
                    nr = (r[0] or "").strip()
                    if not nr or nr == "Nr." or nr.startswith("Stand"):
                        continue
                    partei_raw = (r[1] or "").strip()
                    if not partei_raw:
                        continue
                    partei = norm_party(partei_raw)
                    th = " ".join((r[2] or "").split()).strip() or "allg."
                    ehh_fhh = " ".join((r[3] or "").split()).strip()
                    beschr = " ".join((r[4] or "").split()).strip()
                    ziel = " ".join((r[5] or "").split()).strip()
                    massn = " ".join((r[6] or "").split()).strip()
                    ertrag_25 = clean_num(r[7])
                    aufwand_25 = clean_num(r[8])
                    ve_25 = clean_num(r[9])
                    ertrag_26 = clean_num(r[10])
                    aufwand_26 = clean_num(r[11])
                    ve_26 = clean_num(r[12]) if len(r) > 12 else 0.0
                    anm = " ".join((r[13] or "").split()).strip() if len(r) > 13 else ""

                    title = massn if massn else (ziel if ziel else beschr[:140])
                    is_satire = partei == "DIE PARTEI" and (abs(ertrag_25) >= 10_000_000 or abs(ertrag_26) >= 10_000_000)

                    rows.append({
                        "Nr": nr,
                        "Seite": page_idx + 1,
                        "Fraktion": partei,
                        "TH": th,
                        "Haushaltstyp": "Finanzhaushalt (Investition)" if ehh_fhh == "2" else "Ergebnishaushalt",
                        "Titel": title[:220],
                        "Beschreibung": beschr[:400],
                        "Ertrag_Aenderung_2025_EUR": ertrag_25,
                        "Aufwand_Aenderung_2025_EUR": aufwand_25,
                        "VE_2025_EUR": ve_25,
                        "Ertrag_Aenderung_2026_EUR": ertrag_26,
                        "Aufwand_Aenderung_2026_EUR": aufwand_26,
                        "VE_2026_EUR": ve_26,
                        "Netto_Entlastung_2025_26_EUR": round((ertrag_25 - aufwand_25) + (ertrag_26 - aufwand_26), 2),
                        "Stellungnahme_Verwaltung": anm[:400],
                        "Ist_Satire": is_satire,
                    })

    df_ant = pd.DataFrame(rows)
    df_ant.to_csv(DATA_DIR / "heidelberg_aenderungsantraege_2025_26.csv", index=False)
    print(f"  -> Saved {len(df_ant)} Gemeinderat amendment proposals to heidelberg_aenderungsantraege_2025_26.csv")


def build_macro_and_bilanz_datasets():
    """Builds the verified multi-decade city-wide tables from the official PDFs:
    1) data/heidelberg_macro_2013_2029.csv & data/haushalt_heidelberg_real.csv
    2) data/heidelberg_bilanz_2015_2024.csv (reconciled to 0.00 T€ with official Bilanzsumme p. 851)
    3) data/heidelberg_vorbelastungen.csv (JA 2024 p. 10)
    4) data/heidelberg_beteiligungen.csv (HH 2025/26 Part IV & NH 2026 p. 50-51)
    5) data/heidelberg_steuern_kennzahlen.csv & data/heidelberg_hebesaetze_bw.csv (HP 2025/26 p. 1107-1149, NH 2026 p. 53-54, JA 2024 p. 827)
    6) data/heidelberg_investitionen_2024_2029.csv (NH 2026 p. 36-43)
    """
    years = list(range(2013, 2030))

    cat_series_teuro = {
        ("Erträge", "Steuern und ähnliche Abgaben"): {
            2013: 221265.252, 2014: 224810.0,
            2015: 243470.0, 2016: 248870.0, 2017: 221351.0, 2018: 300881.0, 2019: 261329.0,
            2020: 272339.0, 2021: 292636.0, 2022: 324240.0, 2023: 319511.0, 2024: 300810.0,
            2025: 312970.0, 2026: 350890.0, 2027: 342870.0, 2028: 359270.0, 2029: 369220.0,
        },
        ("Erträge", "Zuweisungen und Zuwendungen, Umlagen"): {
            2013: 206538.947, 2014: 207671.5,
            2015: 220035.0, 2016: 230968.0, 2017: 234202.0, 2018: 264409.0, 2019: 295782.0,
            2020: 282647.0, 2021: 311220.0, 2022: 319316.0, 2023: 323345.0, 2024: 335890.0,
            2025: 337590.0, 2026: 366801.7, 2027: 361742.0, 2028: 382625.0, 2029: 385348.0,
        },
        ("Erträge", "Aufgelöste Investitionszuwendungen und -beiträge"): {
            2013: 5478.288, 2014: 4166.9,
            2015: 4179.0, 2016: 4218.0, 2017: 4201.0, 2018: 4265.0, 2019: 4356.0,
            2020: 4486.0, 2021: 5086.0, 2022: 5615.0, 2023: 5808.0, 2024: 6446.0,
            2025: 5718.0, 2026: 5717.85, 2027: 5718.0, 2028: 5718.0, 2029: 5718.0,
        },
        ("Erträge", "Sonstige Transfererträge"): {
            2013: 4862.589, 2014: 4861.0,
            2015: 6009.0, 2016: 6371.0, 2017: 6443.0, 2018: 6349.0, 2019: 6173.0,
            2020: 4106.0, 2021: 4590.0, 2022: 6022.0, 2023: 5233.0, 2024: 7242.0,
            2025: 4110.0, 2026: 4110.0, 2027: 4110.0, 2028: 4110.0, 2029: 4110.0,
        },
        ("Erträge", "Entgelte für öffentliche Leistungen oder Einrichtungen"): {
            2013: 40038.587, 2014: 38593.5,
            2015: 41187.0, 2016: 43680.0, 2017: 44899.0, 2018: 45948.0, 2019: 48093.0,
            2020: 42598.0, 2021: 43887.0, 2022: 53592.0, 2023: 51331.0, 2024: 61009.0,
            2025: 59008.0, 2026: 64270.35, 2027: 64161.0, 2028: 64259.0, 2029: 64259.0,
        },
        ("Erträge", "Sonstige privatrechtliche Leistungsentgelte"): {
            2013: 17594.960, 2014: 17121.3,
            2015: 19426.0, 2016: 20427.0, 2017: 22187.0, 2018: 21656.0, 2019: 21157.0,
            2020: 18277.0, 2021: 20696.0, 2022: 22652.0, 2023: 24590.0, 2024: 24786.0,
            2025: 25150.0, 2026: 25457.12, 2027: 26391.0, 2028: 26237.0, 2029: 26237.0,
        },
        ("Erträge", "Kostenerstattungen und Kostenumlagen"): {
            2013: 15810.674, 2014: 14734.4,
            2015: 16151.0, 2016: 16898.0, 2017: 20758.0, 2018: 25505.0, 2019: 20808.0,
            2020: 21608.0, 2021: 26143.0, 2022: 21383.0, 2023: 21872.0, 2024: 26763.0,
            2025: 24212.0, 2026: 26446.30, 2027: 25525.0, 2028: 25695.0, 2029: 25696.0,
        },
        ("Erträge", "Zinsen und ähnliche Erträge"): {
            2013: 1511.275, 2014: 2639.0,
            2015: 2241.0, 2016: 2029.0, 2017: 2344.0, 2018: 2164.0, 2019: 1869.0,
            2020: 2393.0, 2021: 1866.0, 2022: 2527.0, 2023: 2106.0, 2024: 2212.0,
            2025: 1966.0, 2026: 2196.0, 2027: 2196.0, 2028: 2196.0, 2029: 2196.0,
        },
        ("Erträge", "Aktivierte Eigenleistungen und Bestandsveränderungen"): {
            2013: 2436.935, 2014: 2527.1,
            2015: 2415.0, 2016: 2402.0, 2017: 2204.0, 2018: 2393.0, 2019: 2384.0,
            2020: 2351.0, 2021: 2792.0, 2022: 2322.0, 2023: 2319.0, 2024: 2969.0,
            2025: 2965.0, 2026: 2990.5, 2027: 2991.0, 2028: 2991.0, 2029: 2991.0,
        },
        ("Erträge", "Sonstige ordentliche Erträge"): {
            2013: 27664.961, 2014: 29560.4,
            2015: 24098.0, 2016: 17175.0, 2017: 37008.0, 2018: 29107.0, 2019: 17612.0,
            2020: 53480.0, 2021: 25527.0, 2022: 17923.0, 2023: 38912.0, 2024: 61733.0,
            2025: 35223.0, 2026: 19580.24, 2027: 20097.0, 2028: 19700.0, 2029: 19426.0,
        },
        ("Aufwendungen", "Personalaufwendungen"): {
            2013: 136267.977, 2014: 139729.6,
            2015: 147547.0, 2016: 153823.0, 2017: 159763.0, 2018: 171447.0, 2019: 173338.0,
            2020: 169473.0, 2021: 172300.0, 2022: 182629.0, 2023: 202476.0, 2024: 221167.0,
            2025: 238796.0, 2026: 244034.0, 2027: 248915.0, 2028: 253893.0, 2029: 258971.0,
        },
        ("Aufwendungen", "Versorgungsaufwendungen"): {
            2013: 1998.046, 2014: 2582.5,
            2015: 2274.0, 2016: 2279.0, 2017: 2261.0, 2018: 323.0, 2019: 358.0,
            2020: 261.0, 2021: 251.0, 2022: 293.0, 2023: 166.0, 2024: 182.0,
            2025: 385.0, 2026: 385.0, 2027: 385.0, 2028: 385.0, 2029: 385.0,
        },
        ("Aufwendungen", "Aufwendungen für Sach- und Dienstleistungen"): {
            2013: 89413.156, 2014: 95181.6,
            2015: 90298.0, 2016: 96119.0, 2017: 103031.0, 2018: 117336.0, 2019: 112364.0,
            2020: 103182.0, 2021: 112952.0, 2022: 122354.0, 2023: 125939.0, 2024: 142531.0,
            2025: 149576.0, 2026: 141532.68, 2027: 142318.0, 2028: 142423.0, 2029: 141748.0,
        },
        ("Aufwendungen", "Planmäßige Abschreibungen"): {
            2013: 40507.619, 2014: 38754.2,
            2015: 56366.0, 2016: 56818.0, 2017: 44718.0, 2018: 57568.0, 2019: 54314.0,
            2020: 59589.0, 2021: 58839.0, 2022: 52655.0, 2023: 57329.0, 2024: 64501.0,
            2025: 55148.0, 2026: 58424.20, 2027: 60448.0, 2028: 61868.0, 2029: 63727.0,
        },
        ("Aufwendungen", "Zinsen und ähnliche Aufwendungen"): {
            2013: 5998.187, 2014: 6515.1,
            2015: 6048.0, 2016: 6221.0, 2017: 5753.0, 2018: 6091.0, 2019: 5973.0,
            2020: 5424.0, 2021: 4656.0, 2022: 4484.0, 2023: 4447.0, 2024: 6655.0,
            2025: 8001.0, 2026: 10590.0, 2027: 15590.0, 2028: 17565.0, 2029: 19565.0,
        },
        ("Aufwendungen", "Transferaufwendungen"): {
            2013: 204623.622, 2014: 221970.2,
            2015: 230221.0, 2016: 227305.0, 2017: 227603.0, 2018: 281457.0, 2019: 253874.0,
            2020: 296301.0, 2021: 333356.0, 2022: 363193.0, 2023: 356787.0, 2024: 381569.0,
            2025: 407323.0, 2026: 408265.651, 2027: 429132.0, 2028: 438326.0, 2029: 448418.0,
        },
        ("Aufwendungen", "Sonstige ordentliche Aufwendungen"): {
            2013: 47295.448, 2014: 41695.0,
            2015: 44919.0, 2016: 42192.0, 2017: 44957.0, 2018: 44013.0, 2019: 45254.0,
            2020: 41168.0, 2021: 43679.0, 2022: 45734.0, 2023: 55464.0, 2024: 52974.0,
            2025: 48525.0, 2026: 45846.657, 2027: 26440.0, 2028: 20644.0, 2029: 9304.0,
        },
    }

    real_rows = []
    for (typ, kat), yr_map in cat_series_teuro.items():
        for yr in years:
            if yr in yr_map:
                status = (
                    "Ist (Jahresabschluss)"
                    if 2015 <= yr <= 2024 or yr == 2013
                    else ("1. Nachtrag 2026" if yr == 2026 else ("Finanzplanung" if yr >= 2027 else "Plan"))
                )
                real_rows.append({
                    "Jahr": yr,
                    "Typ": typ,
                    "Kategorie": kat,
                    "Betrag": round(yr_map[yr] * 1000.0, 2),
                    "Status": status,
                })

    df_real = pd.DataFrame(real_rows)
    df_real.to_csv(DATA_DIR / "haushalt_heidelberg_real.csv", index=False)
    print(f"[Macro 2013-2029] Saved {len(df_real)} rows to haushalt_heidelberg_real.csv")

    # 2. Macro Summary Table (2013-2029) with exact Bilanz alignment for Liquide Mittel, Rücklagen & Schulden
    macro_data = [
        # Jahr, Status, Ertraege_TEUR, Aufwendungen_TEUR, Ord_Ergebnis_TEUR, Sonderergebnis_TEUR, Gesamtergebnis_TEUR,
        # Cashflow_Lfd_TEUR, Invest_Auszahlungen_TEUR, Schulden_Kern_TEUR, Liquide_Mittel_TEUR, Ruecklagen_Gesamt_TEUR,
        # Gewerbesteuer_TEUR, Einkommensteuer_TEUR, Schluesselzuweisungen_TEUR, Einwohner, Steuerkraftsumme_TEUR
        (2013, "Ist (HH 15/16)", 543202, 526104, 17098, 0, 17098, 55879, 68420, 129800, 25000, 110000, 118500, 66200, 121500, 150335, 238500),
        (2014, "Plan (HH 15/16)", 546685, 546428, 257, 0, 257, 36911, 79500, 131589, 29403, 122234, 124000, 70100, 125400, 151500, 245000),
        (2015, "Ist (JA 2024)", 579211, 577673, 1538, 1481, 3019, 84412, 91367, 134844, 15791, 125253, 132605, 73790, 130668, 152463, 251686),
        (2016, "Ist (JA 2024)", 593038, 584757, 8281, 2506, 10787, 35535, 78716, 171743, 39962, 135728, 110719, 77191, 140141, 155077, 271052),
        (2017, "Ist (JA 2024)", 595597, 588086, 7511, -228, 7283, 27941, 76469, 180726, 5073, 143013, 82934, 83750, 129543, 158161, 303858),
        (2018, "Ist (JA 2024)", 702677, 678235, 24442, -666, 23776, 115507, 66279, 188929, 68233, 166787, 156553, 85148, 162735, 160264, 303726),
        (2019, "Ist (JA 2024)", 679563, 645475, 34088, 2934, 37022, 79371, 76056, 181534, 63570, 203805, 112529, 87824, 182257, 160547, 295074),
        (2020, "Ist (JA 2024)", 704285, 675398, 28887, 74, 28961, 36300, 90668, 226003, 51528, 232766, 97838, 82210, 152026, 160350, 366619),
        (2021, "Ist (JA 2024)", 734443, 726033, 8410, -662, 7748, 89038, 83520, 217592, 65470, 240512, 139679, 89665, 175260, 159471, 369382),
        (2022, "Ist (JA 2024)", 775592, 771342, 4250, 361, 4611, 82556, 108575, 209320, 52017, 245122, 168646, 93008, 182632, 158404, 360321),
        (2023, "Ist (JA 2024)", 795027, 802608, -7581, -99, -7680, 82950, 81893, 250805, 52445, 237442, 162891, 93599, 180303, 161810, 396590),
        (2024, "Ist (JA 2024)", 829860, 869579, -39719, 2206, -37513, -24238, 112910, 326305, 12, 199970, 134870, 101456, 186063, 155902, 420840),
        (2025, "Plan (HH 25/26)", 808912, 907754, -98842, 0, -98842, -55210, 115235, 397608, 0, 146128, 135000, 104400, 198600, 157255, 286293),
        (2026, "1. Nachtrag 2026", 868460, 909078, -40618, 0, -40618, 11189, 109454, 448077, 0, 105510, 161500, 111200, 213500, 157255, 282462),
        (2027, "Finanzplanung (NH 26)", 855801, 923228, -67427, 0, -67427, -12832, 95534, 495000, 0, 38082, 148000, 115400, 206500, 157255, 297248),
        (2028, "Finanzplanung (NH 26)", 892801, 935104, -42303, 0, -42303, 13847, 81140, 525000, 0, -4222, 158000, 119900, 226000, 157255, 296018),
        (2029, "Finanzplanung (NH 26)", 905201, 942118, -36917, 0, -36917, 21383, 73592, 548000, 0, -41141, 162000, 124600, 228500, 157255, 307419),
    ]
    macro_cols = [
        "Jahr", "Status", "Ordentliche_Ertraege_TEUR", "Ordentliche_Aufwendungen_TEUR",
        "Ordentliches_Ergebnis_TEUR", "Sonderergebnis_TEUR", "Gesamtergebnis_TEUR",
        "Cashflow_Laufend_TEUR", "Investitionsauszahlungen_TEUR", "Schulden_Kernhaushalt_TEUR",
        "Liquide_Mittel_TEUR", "Ergebnisruecklagen_TEUR", "Gewerbesteuer_TEUR",
        "Einkommensteueranteil_TEUR", "Schluesselzuweisungen_TEUR", "Einwohner_Zensus",
        "Steuerkraftsumme_TEUR",
    ]
    df_macro = pd.DataFrame(macro_data, columns=macro_cols)
    df_macro.to_csv(DATA_DIR / "heidelberg_macro_2013_2029.csv", index=False)
    print(f"[Macro 2013-2029] Saved {len(df_macro)} rows to heidelberg_macro_2013_2029.csv")

    # 3. 1. Nachtrag 2026 Overall Comparison Table (Page 14 of 20_pdf_nachtragshaushalt_2026.pdf)
    nachtrag_gesamt = [
        ("Erträge", "1. Steuern und ähnliche Abgaben", 337620000, 13270000, 350890000, "Gewerbesteuer +8,2 Mio. € (Hebesatz bleibt 400%), Umsatzsteuer +4,1 Mio. €, Einkommensteuer +0,8 Mio. €"),
        ("Erträge", "2. Zuweisungen und Zuwendungen, Umlagen", 358126170, 8675530, 366801700, "Schlüsselzuweisungen vom Land +6,1 Mio. € (auf 213,5 Mio. €), Kita-/Sozialzuweisungen +2,6 Mio. €"),
        ("Erträge", "3. Aufgelöste Investitionszuwendungen und -beiträge", 5717850, 0, 5717850, "Unverändert"),
        ("Erträge", "4. Sonstige Transfererträge", 4110000, 0, 4110000, "Unverändert"),
        ("Erträge", "5. Öffentlich-rechtliche Entgelte", 63876100, 394250, 64270350, "Gebührenanpassungen und höhere Benutzungsgebühren (+394 T€)"),
        ("Erträge", "6. Privatrechtliche Leistungsentgelte", 24997120, 460000, 25457120, "Mieterträge und privatrechtliche Entgelte (+460 T€)"),
        ("Erträge", "7. Kostenerstattungen und Kostenumlagen", 24446300, 2000000, 26446300, "Höhere Kostenerstattungen von Bund/Land/Dritten (+2,0 Mio. €)"),
        ("Erträge", "8. Zinsen und ähnliche Erträge", 2196000, 0, 2196000, "Unverändert"),
        ("Erträge", "9. Aktivierte Eigenleistungen und Bestandsveränderungen", 2990500, 0, 2990500, "Unverändert"),
        ("Erträge", "10. Sonstige ordentliche Erträge", 19180240, 400000, 19580240, "Grundstücksverkäufe / Erbbauzinsen (+400 T€)"),
        ("Aufwendungen", "12. Personalaufwendungen", 244407000, -373000, 244034000, "Aufgabenkritik & verzögerte Nachbesetzungen (-373 T€)"),
        ("Aufwendungen", "13. Versorgungsaufwendungen", 385000, 0, 385000, "Unverändert"),
        ("Aufwendungen", "14. Aufwendungen für Sach- und Dienstleistungen", 144176530, -2643850, 141532680, "Kürzungen Gebäude-/Infrastrukturunterhaltung, IT, externe Beratung (-2,64 Mio. €)"),
        ("Aufwendungen", "15. Planmäßige Abschreibungen", 58424200, 0, 58424200, "Unverändert"),
        ("Aufwendungen", "16. Zinsen und ähnliche Aufwendungen", 12839000, -2249000, 10590000, "Geringerer Zinsaufwand durch spätere Kreditinanspruchnahme (-2,25 Mio. €)"),
        ("Aufwendungen", "17. Transferaufwendungen", 416219511, -7953860, 408265651, "5%-Kürzung freiwilliger Zuschüsse & Konsolidierung TH 50/51/40 (-10,35 Mio. €), gegenläufig +2,4 Mio. € Umlagen"),
        ("Aufwendungen", "18. Sonstige ordentliche Aufwendungen", 49462696, -3616039, 45846657, "Erhöhung Globaler Minderaufwand auf -4,38 Mio. €, Fraktions-/Sitzungsmittel -5% (-3,62 Mio. €)"),
    ]
    df_nh_ges = pd.DataFrame(
        nachtrag_gesamt,
        columns=["Typ", "Position", "Bisher_2026_EUR", "Aenderung_2026_EUR", "Neu_2026_EUR", "Haupttreiber"],
    )
    df_nh_ges.to_csv(DATA_DIR / "heidelberg_nachtrag_2026_gesamt.csv", index=False)
    print(f"[Nachtrag 2026] Saved {len(df_nh_ges)} rows to heidelberg_nachtrag_2026_gesamt.csv")

    # 4. 10-Year Audited Balance Sheet (2015-2024, Jahresabschluss 2024 p. 851-854, in T€)
    # Reconciled so Sum(Aktiva) == Sum(Passiva) == Official Bilanzsumme on p. 851 for all 10 years:
    # [1363206, 1408470, 1423640, 1509696, 1546617, 1584183, 1626916, 1669379, 1757629, 1780058]
    bilanz_years = list(range(2015, 2025))
    bilanz_items = [
        # (Seite, Gruppe, Position, [2015..2024 in T€])
        ("Aktiva", "1. Vermögen", "Immaterielles Vermögen", [1078, 943, 1076, 1395, 972, 1410, 1561, 1497, 1773, 1796]),
        ("Aktiva", "1.Sachvermögen", "Unbebaute Grundstücke", [102480, 101949, 105660, 126152, 159364, 180099, 180419, 180888, 180760, 182240]),
        ("Aktiva", "1.Sachvermögen", "Bebaute Grundstücke (Schulen, Kitas, Verwaltungsbauten)", [539968, 550486, 572265, 552782, 510624, 492438, 481418, 526459, 555114, 581237]),
        ("Aktiva", "1.Sachvermögen", "Infrastrukturvermögen (Straßen, Brücken, Netze)", [320431, 325690, 330540, 332284, 330688, 336113, 344942, 335960, 335673, 365698]),
        ("Aktiva", "1.Sachvermögen", "Bauten auf fremdem Grund und Boden", [9916, 9493, 12123, 11721, 11246, 10906, 10791, 10369, 10106, 9718]),
        ("Aktiva", "1.Sachvermögen", "Kunstgegenstände, Kulturdenkmäler", [33228, 33377, 33366, 33371, 33451, 33547, 33686, 37902, 38869, 39231]),
        ("Aktiva", "1.Sachvermögen", "Maschinen, technische Anlagen, Fahrzeuge", [13343, 14644, 15529, 14980, 17120, 18162, 19295, 21086, 20406, 24905]),
        ("Aktiva", "1.Sachvermögen", "Betriebs- und Geschäftsausstattung", [11078, 11848, 12245, 12378, 11247, 10491, 9932, 11086, 11471, 12173]),
        ("Aktiva", "1.Sachvermögen", "Vorräte", [2298, 2322, 2310, 2299, 2514, 2438, 2497, 2595, 2619, 2714]),
        ("Aktiva", "1.Sachvermögen", "Geleistete Anzahlungen, Anlagen im Bau", [57552, 66088, 81845, 97536, 130613, 153839, 183299, 174774, 183724, 164011]),
        ("Aktiva", "1.Finanzvermögen", "Beteiligungen & Sondervermögen (SWH, GGH, SBH, ETO, ESB)", [134819, 142032, 151619, 153933, 160979, 164157, 164997, 190033, 197031, 203347]),
        ("Aktiva", "1.Finanzvermögen", "Ausleihungen & Wertpapiere", [54812, 37013, 36574, 35439, 38428, 37789, 37133, 36154, 36005, 35255]),
        ("Aktiva", "1.Finanzvermögen", "Öffentlich-rechtliche & Privatrechtliche Forderungen", [33422, 39459, 32078, 33372, 38547, 52370, 53312, 46985, 96679, 121193]),
        ("Aktiva", "1.Finanzvermögen", "Liquide Mittel (Kassenbestand & Bankguthaben)", [15791, 39962, 5073, 68233, 63570, 51528, 65470, 52017, 52445, 12]),
        ("Aktiva", "2. Abgrenzungsposten", "Aktive Rechnungsabgrenzung & geleistete Investitionszuschüsse", [32990, 33164, 31337, 33821, 37254, 38896, 38164, 41574, 34954, 36528]),
        ("Passiva", "1. Kapitalposition (Eigenkapital)", "Basiskapital", [806961, 806961, 806961, 806961, 806961, 806961, 806961, 806961, 806961, 806961]),
        ("Passiva", "1. Kapitalposition (Eigenkapital)", "Rücklagen aus Überschüssen des ordentlichen Ergebnisses", [80052, 88333, 95843, 120286, 154375, 183262, 191674, 195924, 188345, 148627]),
        ("Passiva", "1. Kapitalposition (Eigenkapital)", "Rücklagen aus Überschüssen des Sonderergebnisses & Zweckrücklagen", [45201, 47395, 47170, 46501, 49430, 49504, 48838, 49198, 49097, 51343]),
        ("Passiva", "2. Sonderposten", "Sonderposten für Investitionszuweisungen, -beiträge & Sonstiges", [165937, 165128, 172855, 175345, 176123, 181596, 192113, 197313, 205911, 212475]),
        ("Passiva", "3. Rückstellungen", "Wahlrückstellungen (FAG- & Steuerrückstellungen)", [39302, 33200, 9100, 53976, 54060, 16260, 35700, 78800, 109898, 82095]),
        ("Passiva", "3. Rückstellungen", "Pflichtrückstellungen (Altlasten, Deponie, Personal, Gebühren)", [11907, 12210, 13578, 15185, 16364, 17391, 18360, 17314, 21428, 18040]),
        ("Passiva", "4. Verbindlichkeiten", "Verbindlichkeiten aus Kreditaufnahmen", [134844, 171743, 180726, 188929, 181534, 226003, 217592, 209320, 250805, 337461]),
        ("Passiva", "4. Verbindlichkeiten", "Kreditähnliche Verbindlichkeiten (u.a. ÖPP IGH / B3)", [29816, 38288, 51378, 56192, 55396, 56738, 56229, 51440, 65340, 58885]),
        ("Passiva", "4. Verbindlichkeiten", "Verbindlichkeiten aus Lieferungen/Leistungen, Transfer & Sonstige", [27737, 23506, 23823, 23643, 31875, 23529, 36144, 38922, 35527, 34800]),
        ("Passiva", "5. Passive Rechnungsabgrenzung", "Passive Rechnungsabgrenzungsposten (u.a. Grabnutzungsrechte)", [21449, 21706, 22206, 22678, 20499, 22939, 23305, 24187, 24317, 29371]),
    ]
    bilanz_rows = []
    for seite, gruppe, pos, vals in bilanz_items:
        for yr, v in zip(bilanz_years, vals):
            bilanz_rows.append({
                "Jahr": yr,
                "Seite": seite,
                "Gruppe": gruppe,
                "Position": pos,
                "Betrag_TEUR": v,
                "Betrag_EUR": v * 1000.0,
            })
    df_bilanz = pd.DataFrame(bilanz_rows)
    df_bilanz.to_csv(DATA_DIR / "heidelberg_bilanz_2015_2024.csv", index=False)
    print(f"[Bilanz 2015-2024] Saved {len(df_bilanz)} rows to heidelberg_bilanz_2015_2024.csv")

    # 5. Off-Balance-Sheet Contingent Liabilities (Vorbelastungen künftiger Haushaltsjahre, JA 2024 p. 10)
    vorbelastungen = [
        ("Bürgschaften (u.a. für städtische Gesellschaften SWH, GGH, KGH)", 657121.6, 634340.5, "Haftungsrisiken für Kredite städtischer Töchter"),
        ("Pensionsverpflichtungen (KVBW-Versorgungsumlage Beamte)", 269054.5, 279935.7, "Barwert künftiger Beamtenpensionen über KVBW"),
        ("Zusatzversorgungskasse (ZVK-Umlage Tarifbeschäftigte)", 142100.8, 148772.9, "Versorgungsverpflichtungen für Tarifbeschäftigte"),
        ("Beihilfeverpflichtungen (KVBW Krankenversorgung)", 106875.5, 113199.6, "Künftige Krankheitskostenbeihilfen für aktive/pensionierte Beamte"),
        ("In Anspruch genommene Verpflichtungsermächtigungen", 35859.2, 19037.8, "Bereits gebundene Bau- und Investitionsverträge Folgejahre"),
        ("Treuhandvermögen Bahnstadt (Ausgleichsverpflichtung)", 15596.0, 18242.0, "Kalkulatorisches Defizit Entwicklungsmaßnahme Bahnstadt"),
        ("Noch nicht in Anspruch genommene Kreditermächtigungen", 50000.0, 7045.0, "Offene genehmigte Kreditlinien aus Vorjahren"),
    ]
    df_vorb = pd.DataFrame(
        vorbelastungen,
        columns=["Kategorie", "Stand_2023_TEUR", "Stand_2024_TEUR", "Erlaeuterung"],
    )
    df_vorb.to_csv(DATA_DIR / "heidelberg_vorbelastungen.csv", index=False)
    print(f"[Vorbelastungen] Saved {len(df_vorb)} rows to heidelberg_vorbelastungen.csv")

    # 6. Consolidated Debt & Municipal Enterprises (Nachtrag 2026 p. 50-51 & HH 2025/26 Part IV p. 1197-1402)
    beteiligungen = [
        ("Kernhaushalt Stadt Heidelberg", "Kernverwaltung (41 Ämter)", "Kernhaushalt", 868460, 909078, -40618, 420914, 471383, "Inkl. 65 Mio. € Kassenkredite & 23,3 Mio. € ÖPP IGH/B3"),
        ("Eigenbetrieb Stadtbetriebe Heidelberg (SBH)", "Abwasser, Abfall, Straßenreinigung, Friedhöfe", "Sondervermögen / Eigenbetrieb", 95400, 92100, 3300, 219412, 212539, "Größter Schuldenblock im Sondervermögen (Gebührenhaushalte)"),
        ("Eigenbetrieb Städtische Beteiligungen (ESB)", "Holding für SWH / Konzernbeteiligungen", "Sondervermögen / Eigenbetrieb", 18500, 18500, 0, 45000, 45000, "Hält die Beteiligung an den Stadtwerken Heidelberg (SWH)"),
        ("Treuhandvermögen Bahnstadt", "Städtebauliche Entwicklungsmaßnahme", "Treuhandvermögen", 14200, 16800, -2600, 11366, 12500, "Entwicklungsmaßnahme Bahnstadt (Bürgschaft/Schulden)"),
        ("Eigenbetrieb Theater und Orchester (ETO)", "Theater, Philharmonie, Schlossfestspiele", "Sondervermögen / Eigenbetrieb", 39850, 39850, 0, 0, 0, "Finanziert durch ~29,3 Mio. € Betriebskostenzuschuss der Stadt (TH 44)"),
        ("Stadtwerke Heidelberg GmbH (SWH Konzern)", "Energie, Fernwärme, ÖPNV (rnv), Bäder, Garagen", "Städtische Gesellschaft (100%)", 612000, 608500, 3500, 345000, 365000, "Trägt ÖPNV-/Bäderverluste über steuerlichen Querverbund + Wärmewende"),
        ("Gesellschaft für Grund- und Hausbesitz mbH (GGH)", "Kommunale Wohnungsbaugesellschaft (~7.300 Wohnungen)", "Städtische Gesellschaft (100%)", 98500, 91200, 7300, 410000, 435000, "Großinvestitionen in bezahlbaren Wohnraum & Konversionsflächen (PHV/Hospital)"),
        ("Heidelberger Dienste gGmbH (HDD)", "Beschäftigung, soziale Teilhabe, kommunale Services", "Städtische Gesellschaft (100%)", 19800, 19750, 50, 0, 0, "Städtischer Zuschuss im Nachtrag 2026 um 5% reduziert"),
        ("Tiergarten Heidelberg gGmbH (Zoo)", "Zoologischer Garten Heidelberg", "Städtische Gesellschaft (majority)", 9200, 9200, 0, 4200, 4500, "Städtischer Betriebskostenzuschuss ~2,6 Mio. € p.a."),
        ("Technologiepark Heidelberg GmbH (TP)", "Innovations- und Laborflächen (Neuenheimer Feld / HIP)", "Städtische Gesellschaft (96%)", 11400, 10900, 500, 28000, 26500, "Betreibt BioLabs / Innovationspark"),
        ("Heidelberg Marketing GmbH (HDMT)", "Tourismus, Stadtmarketing, Kongressvermarktung", "Städtische Gesellschaft (100%)", 6400, 6400, 0, 0, 0, "Ausgleich über städtischen Zuschuss (~3,1 Mio. €)"),
        ("Kultur- und Kongressgesellschaft mbH (HKK)", "Heidelberg Congress Center (HCC) & Stadthalle", "Städtische Gesellschaft (100%)", 8900, 13400, -4500, 0, 0, "Inbetriebnahme HCC Bahnstadt & Sanierung Stadthalle"),
        ("Internationale Bauausstellung (IBA) / PHV", "Stadtentwicklung Wissen schafft Stadt", "Städtische Gesellschaft", 2100, 2100, 0, 0, 0, "Auslaufende Projektgesellschaft / Nachfolge"),
    ]
    df_bet = pd.DataFrame(
        beteiligungen,
        columns=[
            "Einheit", "Aufgabenfeld", "Rechtsform", "Ertraege_2026_TEUR",
            "Aufwendungen_2026_TEUR", "Jahresergebnis_2026_TEUR",
            "Schulden_Anfang_2026_TEUR", "Schulden_Ende_2026_TEUR", "Hinweis",
        ],
    )
    df_bet.to_csv(DATA_DIR / "heidelberg_beteiligungen.csv", index=False)
    print(f"[Beteiligungen] Saved {len(df_bet)} rows to heidelberg_beteiligungen.csv")

    # 7. Detailed Tax Breakdown & Per-Capita Municipal KPIs (JA 2024 p. 827, HP 2025/26 p. 1107-1149, NH 2026 p. 53-54 & 233)
    steuern_kennzahlen = [
        # (Kategorie, Position, Einheit, Ist_2023, Plan_2024, Ist_2024, Plan_2025, Bisher_2026, Nachtrag_2026, Prognose_Okt2026, Plan_2027, Plan_2028, Plan_2029, Hinweis)
        ("Steuererträge", "Gewerbesteuer (Hebesatz 400%)", "EUR", 162891003, 125000000, 134869745, 135000000, 153300000, 161500000, 166000000, 148000000, 158000000, 162000000, "Okt 2026 Prognose: +4,5 Mio. € auf 166,0 Mio. € (Wirtschaftsboom Biopharma/IT)"),
        ("Steuererträge", "Gemeindeanteil an der Einkommensteuer", "EUR", 93599301, 99100000, 101456380, 104400000, 110400000, 111200000, 111200000, 115400000, 119900000, 124600000, "Zensus 2022 dämpft Schlüsselzahl ab 2025"),
        ("Steuererträge", "Grundsteuer B (ab 2025 Bodenwertmodell 190%)", "EUR", 34284304, 34400000, 34490339, 34400000, 34400000, 34400000, 34400000, 34400000, 34400000, 34400000, "Aufkommensneutrale Umsetzung Landesgrundsteuergesetz BW (Hebesatz 190% statt 400%)"),
        ("Steuererträge", "Gemeindeanteil an der Umsatzsteuer", "EUR", 19194420, 21900000, 19863201, 21100000, 21400000, 25500000, 25500000, 26500000, 27500000, 28500000, "1. Nachtrag 2026: +4,1 Mio. € durch höheren kommunalen Umsatzsteueranteil"),
        ("Steuererträge", "Grunderwerbsteueranteil", "EUR", 5642100, 6500000, 6120400, 6500000, 6500000, 6500000, 6500000, 6500000, 6500000, 6500000, "Abhängig von Immobilientransaktionen auf Gemarkung Heidelberg"),
        ("Steuererträge", "Übernachtungsteuer (ab 01.10.2025: 3,50 €/Nacht)", "EUR", 0, 0, 0, 4500000, 4500000, 4500000, 4500000, 4500000, 4500000, 4500000, "Neu eingeführt zum 01.10.2025 (3,50 € regulär / 1,50 € Jugendherbergen & Camping)"),
        ("Steuererträge", "Vergnügungsteuer", "EUR", 1685400, 1900000, 1842100, 3800000, 3800000, 3800000, 3800000, 3800000, 3800000, 3800000, "Erhöhung Steuersatz Spielautomaten im Doppelhaushalt 2025/2026"),
        ("Steuererträge", "Zweitwohnungsteuer", "EUR", 1650200, 1750000, 1618500, 2400000, 2400000, 2600000, 2600000, 2600000, 2600000, 2600000, "Anpassung im Rahmen der Haushaltskonsolidierung (+200 T€ im Nachtrag 2026)"),
        ("Steuererträge", "Tourismusabgabe Tagestouristen & Sonstige", "EUR", 0, 0, 0, 300000, 350000, 320000, 320000, 600000, 1500000, 1750000, "Beteiligung Reisebusse/Schiffsanleger an touristischer Infrastruktur"),
        ("Steuererträge", "Hundesteuer & Grundsteuer A", "EUR", 564266, 570000, 549093, 570000, 570000, 570000, 570000, 570000, 570000, 570000, "Hundesteuer (~510 T€) + Grundsteuer A Land-/Forstwirtschaft (~60 T€, Hebesatz 320%)"),
        ("Finanzausgleich (Erträge)", "Schlüsselzuweisungen vom Land (FAG)", "EUR", 180303000, 182000000, 186063000, 198600000, 207400000, 213500000, 213500000, 206500000, 226000000, 228500000, "Wichtigste Landeszuweisung (Nachtrag 2026: +6,1 Mio. € auf 213,5 Mio. €)"),
        ("Finanzausgleich (Erträge)", "Kommunaler Familienleistungsausgleich & Soziallasten", "EUR", 41250000, 42100000, 42890000, 43500000, 44200000, 46775530, 46775530, 47200000, 48100000, 49000000, "Landesausgleich für Kleinkindbetreuung / Kitas (+2,58 Mio. € im Nachtrag 2026)"),
        ("Finanzausgleich (Umlagen)", "Finanzausgleichsumlage (FAG-Umlage an Land)", "EUR", 67420000, 68500000, 69120000, 67200000, 65100000, 66700000, 66700000, 69500000, 69200000, 71800000, "Abhängig von der Steuerkraftsumme des Vorvorjahres"),
        ("Finanzausgleich (Umlagen)", "Gewerbesteuerumlage", "EUR", 14180000, 10900000, 11750000, 11800000, 13400000, 14200000, 14200000, 13000000, 13900000, 14200000, "Abführung an Bund und Land (Vervielfältiger 35% / Hebesatz 400%)"),
        ("Kennzahlen (je Einwohner)", "Steuerkraftsumme je Einwohner", "EUR/EW", 2450.96, 2575.27, 2699.39, 1820.57, 1796.20, 1796.20, 1796.20, 1890.23, 1898.78, 1954.91, "Amtliche Kennzahl lt. NH 2026 S. 53 (Basis 157.255 EW Zensus)"),
        ("Kennzahlen (je Einwohner)", "Ordentliches Ergebnis je Einwohner", "EUR/EW", -46.84, -365.40, -254.77, -628.55, -519.25, -258.29, -154.01, -428.78, -269.01, -234.76, "Verbesserung durch 1. Nachtrag von -519,25 €/EW auf -258,29 €/EW"),
        ("Kennzahlen (je Einwohner)", "Aufwandsdeckungsgrad", "Prozent", 99.06, 93.36, 95.43, 89.11, 91.17, 95.53, 97.34, 92.70, 95.48, 96.08, "Anteil der ordentlichen Aufwendungen, der durch ordentliche Erträge gedeckt ist"),
        ("Kennzahlen (je Einwohner)", "Zahlungsmittelüberschuss/-bedarf lfd. Verwaltung je EW", "EUR/EW", 512.64, -77.10, -155.47, -351.09, -189.79, 71.15, 175.44, -81.60, 88.06, 135.98, "Wieder positiver Cashflow (+71,15 €/EW) im 1. Nachtrag 2026!"),
        ("Kennzahlen (je Einwohner)", "Eigenkapitalquote (inkl. Sonderposten)", "Prozent", 71.14, 65.50, 68.50, 62.66, 56.85, 59.35, 60.10, 56.20, 54.40, 52.80, "Kapitalposition + Sonderposten im Verhältnis zur Bilanzsumme"),
        ("Kennzahlen (je Einwohner)", "Verschuldung Kernhaushalt je Einwohner", "EUR/EW", 1550.00, 2093.01, 2093.01, 2528.43, 2849.36, 2849.36, 2745.08, 3147.75, 3338.53, 3484.79, "Investitionskredite Kernhaushalt je Einwohner"),
    ]
    df_st = pd.DataFrame(
        steuern_kennzahlen,
        columns=[
            "Kategorie", "Position", "Einheit", "Ist_2023", "Plan_2024", "Ist_2024",
            "Plan_2025", "Bisher_2026", "Nachtrag_2026", "Prognose_Okt2026",
            "Plan_2027", "Plan_2028", "Plan_2029", "Hinweis",
        ],
    )
    df_st.to_csv(DATA_DIR / "heidelberg_steuern_kennzahlen.csv", index=False)
    print(f"[Steuern & Kennzahlen] Saved {len(df_st)} rows to heidelberg_steuern_kennzahlen.csv")

    # 8. Baden-Württemberg 9 Stadtkreise Tax Rate Comparison (Haushaltsplan 2025/2026 p. 1108-1109)
    hebesaetze_bw = [
        ("Heidelberg", 400, 190, 320, 400, 155902, "Niedrigster Grundsteuer-B-Hebesatz nach Reform (190% Bodenwertmodell); Gewerbesteuer seit 1995 stabil bei 400%"),
        ("Stuttgart", 520, 260, 360, 420, 613111, "Landeshauptstadt; Gewerbesteuer 420%"),
        ("Mannheim", 615, 370, 350, 430, 316256, "Nachbarstadt; höchster Gewerbesteuer-Hebesatz (430%) gemeinsam mit Karlsruhe"),
        ("Karlsruhe", 460, 310, 320, 430, 309964, "Gewerbesteuer 430%, Grundsteuer B 310%"),
        ("Freiburg im Breisgau", 600, 295, 350, 430, 237244, "Vergleichbare Universitätsstadt; Gewerbesteuer 430% (30 Punkte über Heidelberg)"),
        ("Ulm", 430, 290, 330, 390, 129942, "Starkes Pharmacluster; Gewerbesteuer 390%"),
        ("Heilbronn", 420, 250, 340, 380, 130093, "Niedrigster Gewerbesteuer-Hebesatz unter den Stadtkreisen (380%)"),
        ("Pforzheim", 550, 330, 350, 420, 128992, "Gewerbesteuer 420%"),
        ("Baden-Baden", 490, 240, 350, 410, 57420, "Kleinster Stadtkreis BW; Gewerbesteuer 410%"),
    ]
    df_heb = pd.DataFrame(
        hebesaetze_bw,
        columns=[
            "Stadtkreis", "Grundsteuer_B_Alt_2024_Prozent", "Grundsteuer_B_Neu_2025_Prozent",
            "Grundsteuer_A_Prozent", "Gewerbesteuer_Prozent", "Einwohner_Zensus", "Einordnung",
        ],
    )
    df_heb.to_csv(DATA_DIR / "heidelberg_hebesaetze_bw.csv", index=False)
    print(f"[Hebesätze BW] Saved {len(df_heb)} rows to heidelberg_hebesaetze_bw.csv")

    # 9. Major Capital Investment Program 2024-2029 (1. Nachtragshaushalt 2026 p. 36-43, in T€)
    investitionen = [
        # (TH, Amt, Projekt, Gesamtkosten_TEUR, Bisher_Bereitgestellt_TEUR, Ausz_2024_TEUR, Ausz_2025_TEUR, Ausz_2026_TEUR, Ausz_2027_TEUR, Ausz_2028_TEUR, Ausz_2029_TEUR, Zuschuss_Gesamt_TEUR, Status_Erlaeuterung)
        ("66", "TH 66 - Tiefbauamt", "Montpellierbrücke (Sanierung / Teilerneuerung)", 35560, 15060, 5000, 5000, 5000, 5500, 0, 0, 11000, "Schlüsselprojekt Brückensanierung Hauptbahnhof/Südstadt (Landeszuschuss 11,0 Mio. €)"),
        ("23", "TH 23 - Amt für Liegenschaften", "Verlagerung Karlstorbahnhof (Kulturzentrum Bahnstadt)", 24160, 20645, 231, 1870, 1414, 0, 0, 0, 0, "Restabwicklung Umbau/Neubau Kulturzentrum"),
        ("40", "TH 40 - Amt für Schule und Bildung", "Hölderlin-Gymnasium (Generalsanierung)", 22590, 22300, 290, 0, 0, 0, 0, 0, 1811, "Abschluss und Restabwicklung der Generalsanierung"),
        ("FW", "TH FW - Allgemeine Finanzwirtschaft", "Einlage Stammkapital Stadtwerke Heidelberg (SWH Wärmewende)", 91914, 0, 18300, 14714, 14700, 14400, 14700, 15100, 0, "Eigenkapitalstärkung SWH für Dekarbonisierung Fernwärme & ÖPNV (2024–2029: 91,9 Mio. €)"),
        ("FW", "TH FW - Allgemeine Finanzwirtschaft", "Erwerb beweglicher Sachen des Anlagevermögens (Gesamtstadt)", 64041, 0, 12855, 14097, 10089, 9000, 9000, 9000, 3529, "Fahrzeuge, IT-Ausstattung, Spezialgeräte Feuerwehr/Abfallwirtschaft"),
        ("FW", "TH FW - Allgemeine Finanzwirtschaft", "Investitionsförderungsmaßnahmen an Dritte", 34903, 0, 8102, 5133, 6668, 5000, 5000, 5000, 0, "Investitionszuschüsse für freie Träger (Kitas, Sportvereine, Kultur, Soziales)"),
        ("FW", "TH FW - Allgemeine Finanzwirtschaft", "Erwerb von Grundstücken und Gebäuden", 26000, 0, 8000, 6000, 3000, 3000, 3000, 3000, 34000, "Aktive Bodenpolitik; gegenläufig 34,0 Mio. € Grundstücksveräußerungserlöse"),
        ("66", "TH 66 - Tiefbauamt", "Straßenerneuerungsprogramm (insb. Fernwärmeausbau)", 24000, 0, 4000, 4000, 4000, 4000, 4000, 4000, 0, "Kontinuierliche Sanierung des Straßennetzes & Fernwärmetrassen SWH"),
        ("FW", "TH FW - Allgemeine Finanzwirtschaft", "Ausgleich Treuhandvermögen Erneuerungsgebiete (PHV/Hospital/Rohrbach)", 22985, 0, 4000, 3185, 3800, 4000, 4000, 4000, 0, "Städtischer Finanzierungsanteil Konversionsflächen & Sanierungsgebiete"),
        ("FW", "TH FW - Allgemeine Finanzwirtschaft", "Ausgleich Treuhandvermögen Bahnstadt (Abschluss 2027)", 21600, 0, 3000, 6200, 6200, 6200, 0, 0, 0, "Finanzierungsanteil Wirtschaftsplan Bahnstadt bis zum Abschluss am 31.12.2027"),
        ("81", "TH 81 - Amt für Mobilität", "Bauliche und technische Verbesserungen Verkehrsinfrastruktur", 20949, 0, 4317, 3932, 3700, 3000, 3000, 3000, 294, "Verkehrsknotenpunkte, Lichtsignalanlagen, Sicherheit"),
        ("66", "TH 66 - Tiefbauamt", "Dossenheimer Landstraße (Neugestaltung & Barrierefreiheit)", 15000, 1500, 1500, 4000, 4000, 4000, 0, 0, 4300, "Grunderneuerung gemeinsam mit rnv-Haltestellenausbau"),
        ("40", "TH 40 - Amt für Schule und Bildung", "Mönchhofschule (Verbesserung Essens- und Betreuungssituation)", 10650, 458, 100, 400, 2000, 4000, 3692, 0, 6780, "Umsetzung nach Eingang Förderbescheid Land (6,78 Mio. € Förderung)"),
        ("51", "TH 51 - Kinder- und Jugendamt", "Neubau Haus der Jugend", 10590, 10150, 150, 290, 0, 0, 0, 0, 0, "Fertigstellung und Restabwicklung Neubau Rohrbacher Straße"),
        ("81", "TH 81 - Amt für Mobilität", "Fahrradinfrastruktur (Radwegenetz & Radschnellwege)", 9700, 0, 100, 1000, 1700, 2000, 2000, 2000, 1430, "Ausbau Radwegenetz, Radschnellwege und Fahrradabstellanlagen"),
        ("65", "TH 65 - Hochbauamt", "Hauptbahnhof Nord: Unterirdisches Fahrradparkhaus & Stadtbalkon", 9400, -2832, 4500, 3000, 4000, 732, 0, 0, 6807, "Unterirdisches Fahrradparkhaus mit Außenanlage (6,81 Mio. € Bundes-/Landesförderung)"),
        ("40", "TH 40 - Amt für Schule und Bildung", "Geschwister-Scholl-Schule (Ersatzneubau Sporthalle)", 8570, 370, 2600, 3500, 1800, 300, 0, 0, 270, "Ersatzneubau Dreifeld-Sporthalle Kirchheim"),
        ("51", "TH 51 - Kinder- und Jugendamt", "Kindertagesstätte Stettiner Straße (Neubau)", 7860, 3796, 964, 2900, 200, 0, 0, 0, 451, "Ausbau Kinderbetreuung Kirchheim"),
        ("23", "TH 23 - Amt für Liegenschaften", "Kindertagesstätte Harbigweg (Neubau Holzmodulbauweise)", 7044, 5548, 1345, 151, 0, 0, 0, 0, 552, "Neubau in Holzmodulbauweise"),
        ("67", "TH 67 - Landschaftsamt", "Grün- und Parkanlagen, Stadtbegrünung, Plätze", 7042, 0, 2270, 1500, 1262, 1000, 1000, 1000, 12, "Providenzgarten, Kurfürstenanlage, Oasis, Baumpflanzungen, Entsiegelung"),
        ("66", "TH 66 - Tiefbauamt", "Östliche Zuführung Montpellierbrücke (Schere Ost / Czernyring)", 6700, 2400, 1500, 1000, 1800, 0, 0, 0, 3600, "Umbau Czernyring zwischen Montpellierbrücke und Hebelstraßenbrücke"),
        ("81", "TH 81 - Amt für Mobilität", "Infrastruktur ÖPNV (Barrierefreier Haltestellenausbau & INF)", 6750, 0, 750, 1500, 1500, 1000, 1000, 1000, 550, "Barrierefreier Ausbau Bushaltestellen & Verkehrsführung Im Neuenheimer Feld"),
        ("66", "TH 66 - Tiefbauamt", "Stützmauer Neue Schlossstraße (Sanierung)", 5160, 1260, 2000, 1000, 900, 0, 0, 0, 0, "Denkmalgerechte Hang- und Stützmauersanierung unterhalb des Schlosses"),
        ("40", "TH 40 - Amt für Schule und Bildung", "Albert-Schweitzer-Schule (Essens- und Betreuungssituation)", 4700, 0, 170, 200, 500, 2000, 1830, 0, 3101, "Umsetzung nach Eingang Förderbescheid Land (3,10 Mio. € Förderung)"),
        ("66", "TH 66 - Tiefbauamt", "Fuß- und Radverbindung über den Neckar (Planung Lph 1–5)", 4500, 1150, 550, 1000, 800, 500, 500, 0, 0, "Fachplanungsleistungen für den Abschluss der Leistungsphasen 1–5 HOAI"),
        ("37", "TH 37 - Feuerwehr", "Digitalisierung Leitstelle Berufsfeuerwehr", 3805, 2305, 750, 750, 0, 0, 0, 0, 120, "Austausch Leitstellentechnik und Funkinfrastruktur"),
        ("40", "TH 40 - Amt für Schule und Bildung", "Waldparkschule (Verbesserung Essenssituation)", 3550, 2320, 865, 365, 0, 0, 0, 0, 519, "Mensa- und Betreuungsausbau Boxberg"),
        ("40", "TH 40 - Amt für Schule und Bildung", "Schulcampus Mitte (Interimsmaßnahmen Grundschule Bahnstadt)", 3300, -1333, 500, 2233, 1900, 0, 0, 0, 0, "Temporäre Verlagerung von Klassen aus der Grundschule Bahnstadt"),
        ("40", "TH 40 - Amt für Schule und Bildung", "Carl-Bosch-Schule (Sanierung Toiletten Neubau)", 3100, 1490, 1200, 410, 0, 0, 0, 0, 949, "Sanierung sanitäre Anlagen Berufsschulzentrum"),
    ]
    df_inv = pd.DataFrame(
        investitionen,
        columns=[
            "TH", "Amt", "Projekt", "Gesamtkosten_TEUR", "Bisher_Bereitgestellt_TEUR",
            "Auszahlung_2024_TEUR", "Auszahlung_2025_TEUR", "Auszahlung_2026_TEUR",
            "Auszahlung_2027_TEUR", "Auszahlung_2028_TEUR", "Auszahlung_2029_TEUR",
            "Zuschuss_Gesamt_TEUR", "Erlaeuterung",
        ],
    )
    df_inv.to_csv(DATA_DIR / "heidelberg_investitionen_2024_2029.csv", index=False)
    print(f"[Investitionen 2024-2029] Saved {len(df_inv)} rows to heidelberg_investitionen_2024_2029.csv")


if __name__ == "__main__":
    extract_nachtrag_2026()
    extract_jahresabschluss_2024_aemter()
    extract_aenderungsantraege_2025_26()
    build_macro_and_bilanz_datasets()
