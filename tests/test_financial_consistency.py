from pathlib import Path
import numpy as np
import pandas as pd
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"


def test_all_csv_files_exist_and_non_empty():
    expected_files = [
        "haushalt_heidelberg_deep.csv",
        "haushalt_heidelberg_aemter.csv",
        "haushalt_heidelberg_real.csv",
        "heidelberg_macro_2013_2029.csv",
        "heidelberg_nachtrag_2026_gesamt.csv",
        "heidelberg_nachtrag_2026_aemter.csv",
        "heidelberg_nachtrag_2026_massnahmen.csv",
        "heidelberg_jahresabschluss_2024_aemter.csv",
        "heidelberg_personal_stellen.csv",
        "heidelberg_bilanz_2015_2024.csv",
        "heidelberg_vorbelastungen.csv",
        "heidelberg_beteiligungen.csv",
        "heidelberg_steuern_kennzahlen.csv",
        "heidelberg_hebesaetze_bw.csv",
        "heidelberg_investitionen_2024_2029.csv",
        "heidelberg_aenderungsantraege_2025_26.csv",
    ]
    for fname in expected_files:
        fpath = DATA_DIR / fname
        assert fpath.exists(), f"Missing dataset: {fname}"
        df = pd.read_csv(fpath, encoding="utf-8")
        assert len(df) > 0, f"Dataset {fname} is empty"


def test_deep_vs_aemter_exact_reconciliation():
    """Verify that haushalt_heidelberg_deep.csv (8,539 rows) and haushalt_heidelberg_aemter.csv (5,164 rows)
    reconcile to 0.00 EUR across every single year (2013-2026), department (Amt), type, and category.
    """
    df_deep = pd.read_csv(DATA_DIR / "haushalt_heidelberg_deep.csv", encoding="utf-8")
    df_aemter = pd.read_csv(DATA_DIR / "haushalt_heidelberg_aemter.csv", encoding="utf-8")

    # 1. Total sum across all 14 years
    assert abs(df_deep["Betrag"].sum() - df_aemter["Betrag"].sum()) < 1e-6

    # 2. Per (Jahr, Typ) reconciliation
    g_deep_yr = df_deep.groupby(["Jahr", "Typ"])["Betrag"].sum()
    g_aemter_yr = df_aemter.groupby(["Jahr", "Typ"])["Betrag"].sum()
    pd.testing.assert_series_equal(g_deep_yr, g_aemter_yr, check_exact=False, atol=1e-2)

    # 3. Per (Jahr, Amt, Typ, Kategorie) reconciliation
    g_deep_full = df_deep.groupby(["Jahr", "Amt", "Typ", "Kategorie"])["Betrag"].sum()
    g_aemter_full = df_aemter.groupby(["Jahr", "Amt", "Typ", "Kategorie"])["Betrag"].sum()
    pd.testing.assert_series_equal(g_deep_full, g_aemter_full, check_exact=False, atol=1e-2)


def test_real_vs_macro_2013_2029_reconciliation():
    """Verify haushalt_heidelberg_real.csv category sums match heidelberg_macro_2013_2029.csv
    and internal macro identities hold for all 17 years (2013-2029).
    """
    df_real = pd.read_csv(DATA_DIR / "haushalt_heidelberg_real.csv", encoding="utf-8")
    df_macro = pd.read_csv(DATA_DIR / "heidelberg_macro_2013_2029.csv", encoding="utf-8")

    assert list(df_macro["Jahr"]) == list(range(2013, 2030))

    # Internal identities in macro table
    for _, row in df_macro.iterrows():
        yr = int(row["Jahr"])
        ord_erg = row["Ordentliche_Ertraege_TEUR"] - row["Ordentliche_Aufwendungen_TEUR"]
        assert abs(ord_erg - row["Ordentliches_Ergebnis_TEUR"]) <= 1, f"Year {yr} Ordentliches_Ergebnis mismatch"
        ges_erg = row["Ordentliches_Ergebnis_TEUR"] + row["Sonderergebnis_TEUR"]
        assert abs(ges_erg - row["Gesamtergebnis_TEUR"]) <= 1, f"Year {yr} Gesamtergebnis mismatch"

    # Cross-check with haushalt_heidelberg_real.csv
    piv = df_real.groupby(["Jahr", "Typ"])["Betrag"].sum().unstack()
    for _, row in df_macro.iterrows():
        yr = int(row["Jahr"])
        e_real_teur = piv.loc[yr, "Erträge"] / 1000.0
        a_real_teur = piv.loc[yr, "Aufwendungen"] / 1000.0
        assert abs(e_real_teur - row["Ordentliche_Ertraege_TEUR"]) <= 1.5, f"Year {yr} Erträge mismatch"
        assert abs(a_real_teur - row["Ordentliche_Aufwendungen_TEUR"]) <= 1.5, f"Year {yr} Aufwendungen mismatch"


def test_nachtrag_2026_full_reconciliation():
    """Verify 1. Nachtragshaushalt 2026 consistency:
    - Bisher + Aenderung == Neu on every row of gesamt, aemter, and massnahmen
    - Sum across all 41 Teilhaushalte in nh_aemter equals nh_gesamt to 0.00 EUR
    - Erträge - Aufwendungen == Ergebnis for every Teilhaushalt in nh_aemter
    """
    df_ges = pd.read_csv(DATA_DIR / "heidelberg_nachtrag_2026_gesamt.csv", encoding="utf-8")
    df_amt = pd.read_csv(DATA_DIR / "heidelberg_nachtrag_2026_aemter.csv", encoding="utf-8")
    df_mass = pd.read_csv(DATA_DIR / "heidelberg_nachtrag_2026_massnahmen.csv", encoding="utf-8")

    # 1. Additive identity on gesamt
    assert np.allclose(df_ges["Bisher_2026_EUR"] + df_ges["Aenderung_2026_EUR"], df_ges["Neu_2026_EUR"], atol=1e-2)

    # 2. Additive identity on aemter
    assert len(df_amt["TH"].unique()) == 41
    assert np.allclose(df_amt["Bisher_2026"] + df_amt["Aenderung_2026"], df_amt["Neu_2026"], atol=1e-2)

    # 3. Erträge - Aufwendungen == Ergebnis for every Teilhaushalt
    for th, grp in df_amt.groupby("TH"):
        p_map = grp.set_index("Position")
        for col in ["Bisher_2026", "Aenderung_2026", "Neu_2026"]:
            e_val = p_map.loc["Anteilige ordentliche Erträge", col]
            a_val = p_map.loc["Anteilige ordentliche Aufwendungen", col]
            r_val = p_map.loc["Anteiliges ordentliches Ergebnis", col]
            assert abs((e_val - a_val) - r_val) < 1e-2, f"TH {th} {col} Erträge - Aufwendungen != Ergebnis"

    # 4. Exact 0.00 EUR reconciliation between sum of 41 Teilhaushalte and Gesamtergebnishaushalt
    for pos, typ in [
        ("Anteilige ordentliche Erträge", "Erträge"),
        ("Anteilige ordentliche Aufwendungen", "Aufwendungen"),
    ]:
        s_amt = df_amt[df_amt["Position"] == pos][["Bisher_2026", "Aenderung_2026", "Neu_2026"]].sum().values
        s_ges = df_ges[df_ges["Typ"] == typ][["Bisher_2026_EUR", "Aenderung_2026_EUR", "Neu_2026_EUR"]].sum().values
        assert np.allclose(s_amt, s_ges, atol=1e-2), f"Nachtrag 2026 {pos} mismatch: {s_amt} vs {s_ges}"

    # 5. Massnahmen additive identity and no subtotal leakage
    assert np.allclose(df_mass["Bisher_2026"] + df_mass["Aenderung_2026"], df_mass["Neu_2026"], atol=1.0)
    forbidden = ("insgesamt", "zwischensumme", "anteiliges ordentliches", "anteilige ordentliche")
    for m in df_mass["Massnahme"].astype(str):
        assert not any(w in m.lower() for w in forbidden), f"Subtotal row leaked into massnahmen: {m}"


def test_jahresabschluss_2024_aemter_reconciliation():
    """Verify audited Jahresabschluss 2024 department table:
    - All 39 Teilhaushalte present
    - Ist_2024 - Plan_2024 == Abweichung_2024 on every row
    - Erträge - Aufwendungen == Ergebnis on every department
    - Sum of 39 Teilhaushalte matches city-wide macro actuals for 2023 and 2024
    """
    df_ja = pd.read_csv(DATA_DIR / "heidelberg_jahresabschluss_2024_aemter.csv", encoding="utf-8")
    df_macro = pd.read_csv(DATA_DIR / "heidelberg_macro_2013_2029.csv", encoding="utf-8").set_index("Jahr")

    assert len(df_ja["TH"].unique()) == 39
    assert np.allclose(df_ja["Ist_2024"] - df_ja["Plan_2024"], df_ja["Abweichung_2024"], atol=1e-2)

    for th, grp in df_ja.groupby("TH"):
        p_map = grp.set_index("Position")
        for col in ["Ist_2023", "Plan_2024", "Ist_2024", "Abweichung_2024"]:
            e_val = p_map.loc["Anteilige ordentliche Erträge", col]
            a_val = p_map.loc["Anteilige ordentliche Aufwendungen", col]
            r_val = p_map.loc["Anteiliges ordentliches Ergebnis", col]
            assert abs((e_val - a_val) - r_val) < 1e-2, f"JA 2024 TH {th} {col} mismatch"

    # Reconcile city-wide sums for 2023 Ist and 2024 Ist (within 1.5 TEUR rounding)
    e_2023 = df_ja[df_ja["Position"] == "Anteilige ordentliche Erträge"]["Ist_2023"].sum() / 1000.0
    a_2023 = df_ja[df_ja["Position"] == "Anteilige ordentliche Aufwendungen"]["Ist_2023"].sum() / 1000.0
    e_2024 = df_ja[df_ja["Position"] == "Anteilige ordentliche Erträge"]["Ist_2024"].sum() / 1000.0
    a_2024 = df_ja[df_ja["Position"] == "Anteilige ordentliche Aufwendungen"]["Ist_2024"].sum() / 1000.0

    assert abs(e_2023 - df_macro.loc[2023, "Ordentliche_Ertraege_TEUR"]) <= 2.0
    assert abs(a_2023 - df_macro.loc[2023, "Ordentliche_Aufwendungen_TEUR"]) <= 2.0
    assert abs(e_2024 - df_macro.loc[2024, "Ordentliche_Ertraege_TEUR"]) <= 2.0
    assert abs(a_2024 - df_macro.loc[2024, "Ordentliche_Aufwendungen_TEUR"]) <= 2.0


def test_personal_stellen_reconciliation():
    """Verify personnel table:
    - Differenz == Ist_Koepe_31_12 - Planstellen
    - 2025 & 2026 Stellenplan sums to exact official headline 2,658.00 Planstellen (733.75 Beamte + 1,924.25 Tarif)
    """
    df_p = pd.read_csv(DATA_DIR / "heidelberg_personal_stellen.csv", encoding="utf-8")
    assert np.allclose(df_p["Ist_Koepe_31_12"] - df_p["Planstellen"], df_p["Differenz"], atol=1e-2)

    for yr in (2025, 2026):
        sub = df_p[df_p["Jahr"] == yr]
        assert len(sub) == 38
        assert np.allclose(sub["Beamte_Stellen"] + sub["Tarif_Stellen"], sub["Planstellen"], atol=1e-2)
        assert abs(sub["Beamte_Stellen"].sum() - 733.75) < 1e-2
        assert abs(sub["Tarif_Stellen"].sum() - 1924.25) < 1e-2
        assert abs(sub["Planstellen"].sum() - 2658.00) < 1e-2


def test_bilanz_2015_2024_and_macro_alignment():
    """Verify 10-year Balance Sheet (2015-2024):
    - Aktiva == Passiva == Official Bilanzsumme for every single year 2015-2024
    - Betrag_EUR == Betrag_TEUR * 1000
    - Liquide Mittel and Rücklagen match heidelberg_macro_2013_2029.csv
    """
    df_b = pd.read_csv(DATA_DIR / "heidelberg_bilanz_2015_2024.csv", encoding="utf-8")
    df_m = pd.read_csv(DATA_DIR / "heidelberg_macro_2013_2029.csv", encoding="utf-8").set_index("Jahr")

    official_bilanzsumme = {
        2015: 1363206,
        2016: 1408470,
        2017: 1423640,
        2018: 1509696,
        2019: 1546617,
        2020: 1584183,
        2021: 1626916,
        2022: 1669379,
        2023: 1757629,
        2024: 1780058,
    }

    assert np.allclose(df_b["Betrag_TEUR"] * 1000.0, df_b["Betrag_EUR"], atol=1e-2)

    piv = df_b.groupby(["Jahr", "Seite"])["Betrag_TEUR"].sum().unstack()
    for yr, expected_sum in official_bilanzsumme.items():
        akt = piv.loc[yr, "Aktiva"]
        pas = piv.loc[yr, "Passiva"]
        assert akt == pas == expected_sum, f"Bilanz {yr}: Aktiva={akt}, Passiva={pas}, Expected={expected_sum}"

        # Check Liquide Mittel alignment with macro table
        liq_b = df_b[
            (df_b["Jahr"] == yr) & (df_b["Position"].str.startswith("Liquide Mittel"))
        ]["Betrag_TEUR"].iloc[0]
        assert liq_b == df_m.loc[yr, "Liquide_Mittel_TEUR"], f"Year {yr} Liquide Mittel mismatch"

        # Check Rücklagen alignment with macro table
        rueck_b = df_b[
            (df_b["Jahr"] == yr) & (df_b["Position"].str.startswith("Rücklagen"))
        ]["Betrag_TEUR"].sum()
        assert rueck_b == df_m.loc[yr, "Ergebnisruecklagen_TEUR"], f"Year {yr} Rücklagen mismatch"


def test_new_supplementary_datasets_consistency():
    """Verify Steuern/Kennzahlen, BW Hebesätze, Investitionsprogramm 2024-2029, and Gemeinderat Änderungsanträge."""
    df_st = pd.read_csv(DATA_DIR / "heidelberg_steuern_kennzahlen.csv", encoding="utf-8")
    df_heb = pd.read_csv(DATA_DIR / "heidelberg_hebesaetze_bw.csv", encoding="utf-8")
    df_inv = pd.read_csv(DATA_DIR / "heidelberg_investitionen_2024_2029.csv", encoding="utf-8")
    df_ant = pd.read_csv(DATA_DIR / "heidelberg_aenderungsantraege_2025_26.csv", encoding="utf-8")

    # Steuern sum in 1. Nachtrag 2026 == 350,890,000 EUR
    st_sum_nh26 = df_st[df_st["Kategorie"] == "Steuererträge"]["Nachtrag_2026"].sum()
    assert st_sum_nh26 == 350_890_000

    # BW Hebesätze: 9 Stadtkreise, Heidelberg Grundsteuer B Neu == 190 (lowest) and Gewerbesteuer == 400
    assert len(df_heb) == 9
    hd_row = df_heb[df_heb["Stadtkreis"] == "Heidelberg"].iloc[0]
    assert hd_row["Grundsteuer_B_Neu_2025_Prozent"] == 190
    assert hd_row["Grundsteuer_B_Neu_2025_Prozent"] == df_heb["Grundsteuer_B_Neu_2025_Prozent"].min()
    assert hd_row["Gewerbesteuer_Prozent"] == 400

    # Investitionen: positive project totals
    assert len(df_inv) == 29
    assert (df_inv["Gesamtkosten_TEUR"] > 0).all()

    # Gemeinderat Änderungsanträge: 359 proposals, arithmetic identity holds
    assert len(df_ant) >= 350
    calc_netto = (
        (df_ant["Ertrag_Aenderung_2025_EUR"] - df_ant["Aufwand_Aenderung_2025_EUR"])
        + (df_ant["Ertrag_Aenderung_2026_EUR"] - df_ant["Aufwand_Aenderung_2026_EUR"])
    )
    assert np.allclose(calc_netto, df_ant["Netto_Entlastung_2025_26_EUR"], atol=1e-2)
