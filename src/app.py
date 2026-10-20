from pathlib import Path
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from st_aggrid import AgGrid, ColumnsAutoSizeMode, GridOptionsBuilder, JsCode

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"

st.set_page_config(
    page_title="Haushalt Heidelberg Explorer (2013–2029)",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom styling for KPI cards and clean layout
st.markdown(
    """
    <style>
    div[data-testid="stMetric"] {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 14px 18px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.03);
    }
    .block-container {
        padding-top: 1.8rem;
        padding-bottom: 2rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def fmt_eur(val: float, decimals: int = 0) -> str:
    """Format a number in German Euro notation (e.g., 907.753.195 €)."""
    if pd.isna(val):
        return "0 €"
    s = f"{val:,.{decimals}f}"
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{s} €"


def fmt_mio(val: float) -> str:
    """Format a large Euro figure in millions (e.g., 907,75 Mio. €)."""
    if pd.isna(val):
        return "0,00 Mio. €"
    s = f"{val / 1e6:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{s} Mio. €"


def short_amt(amt: str) -> str:
    """Create a concise, unambiguous Amt label for bar chart axes."""
    s = str(amt).strip()
    if len(s) <= 38:
        return s
    return s[:36] + "…"


EUR_FORMATTER = JsCode(
    """
    function(params) {
        if (params.value === undefined || params.value === null) return '';
        return Number(params.value).toLocaleString('de-DE', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }) + ' €';
    }
    """
)
PCT_FORMATTER = JsCode(
    """
    function(params) {
        if (params.value === undefined || params.value === null) return '';
        return Number(params.value).toLocaleString('de-DE', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }) + ' %';
    }
    """
)


@st.cache_data
def load_data() -> pd.DataFrame:
    try:
        df = pd.read_csv(DATA_DIR / "haushalt_heidelberg_deep.csv", encoding="utf-8")
    except Exception:
        df = pd.read_csv(DATA_DIR / "haushalt_heidelberg_aemter.csv", encoding="utf-8")
        if "Sub_Kategorie" not in df.columns:
            df["Sub_Kategorie"] = df["Kategorie"]

    df = df[df["Amt"].notna() & (df["Amt"] != "Unbekanntes Amt")].copy()
    df["Jahr"] = df["Jahr"].astype(int)
    df["Betrag"] = pd.to_numeric(df["Betrag"], errors="coerce").fillna(0.0)
    df["Kategorie"] = (
        df["Kategorie"]
        .fillna("Sonstige")
        .astype(str)
        .str.strip()
        .replace({"": "Sonstige"})
    )
    df["Sub_Kategorie"] = (
        df["Sub_Kategorie"]
        .fillna("Allgemein")
        .astype(str)
        .str.strip()
        .replace({"": "Allgemein"})
    )
    # Pre-compute derived string columns once in cache for O(1) filtering & rendering
    df["Amt_Kurz"] = df["Amt"].map(short_amt)
    df["Sub_Label"] = np.where(
        df["Sub_Kategorie"] == df["Kategorie"],
        df["Sub_Kategorie"] + " (Gesamtposition)",
        df["Sub_Kategorie"],
    )
    df["Search_Blob"] = (
        df["Amt"].str.lower()
        + " "
        + df["Kategorie"].str.lower()
        + " "
        + df["Sub_Kategorie"].str.lower()
    )
    return df


@st.cache_data
def load_data_by_year() -> dict[int, pd.DataFrame]:
    base_df = load_data()
    return {int(yr): grp.copy() for yr, grp in base_df.groupby("Jahr")}


@st.cache_data
def load_supplementary_datasets() -> dict:
    datasets = {}
    csv_files = {
        "real": "haushalt_heidelberg_real.csv",
        "macro": "heidelberg_macro_2013_2029.csv",
        "nh_gesamt": "heidelberg_nachtrag_2026_gesamt.csv",
        "nh_aemter": "heidelberg_nachtrag_2026_aemter.csv",
        "nh_massnahmen": "heidelberg_nachtrag_2026_massnahmen.csv",
        "ja2024_aemter": "heidelberg_jahresabschluss_2024_aemter.csv",
        "personal": "heidelberg_personal_stellen.csv",
        "bilanz": "heidelberg_bilanz_2015_2024.csv",
        "vorbelastungen": "heidelberg_vorbelastungen.csv",
        "beteiligungen": "heidelberg_beteiligungen.csv",
        "steuern": "heidelberg_steuern_kennzahlen.csv",
        "hebesaetze": "heidelberg_hebesaetze_bw.csv",
        "investitionen": "heidelberg_investitionen_2024_2029.csv",
        "antraege": "heidelberg_aenderungsantraege_2025_26.csv",
    }
    for key, fname in csv_files.items():
        fpath = DATA_DIR / fname
        if fpath.exists():
            datasets[key] = pd.read_csv(fpath, encoding="utf-8")
        else:
            datasets[key] = pd.DataFrame()
    return datasets


df = load_data()
df_by_year = load_data_by_year()
supp = load_supplementary_datasets()

YEAR_STATUS = {
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
    2026: "Plan (HH 25/26) / 1. Nachtrag in Tab 4",
}

valid_years = sorted(df_by_year.keys(), reverse=True)
default_year_idx = valid_years.index(2025) if 2025 in valid_years else 0

# --- SIDEBAR FILTERS ---
st.sidebar.title("🏛️ Haushalt-Filter")
selected_year = st.sidebar.selectbox(
    "Haushaltsjahr auswählen (Teilhaushalte)",
    valid_years,
    index=default_year_idx,
    format_func=lambda y: f"{y} ({YEAR_STATUS.get(y, 'Plan')})",
)
selected_type = st.sidebar.radio(
    "Haushaltsseite (Typ)",
    ["Aufwendungen", "Erträge"],
    format_func=lambda t: "Aufwendungen (Ausgaben)" if t == "Aufwendungen" else "Erträge (Einnahmen)",
)
hierarchy_mode = st.sidebar.radio(
    "Hierarchie-Gruppierung",
    ["Amt ➔ Kategorie ➔ Einzelposten", "Kategorie ➔ Amt ➔ Einzelposten"],
)
chart_type = st.sidebar.segmented_control(
    "Diagramm-Typ",
    ["Treemap (Kacheln)", "Sunburst (Ring)"],
    default="Treemap (Kacheln)",
)

year_base_df = df_by_year.get(selected_year, pd.DataFrame())
all_aemter_for_year = sorted(year_base_df["Amt"].unique().tolist()) if not year_base_df.empty else []
selected_aemter = st.sidebar.multiselect(
    "Ämter / Teilhaushalte filtern (optional)",
    options=all_aemter_for_year,
    default=[],
    placeholder="Alle Teilhaushalte",
)

search_query = st.sidebar.text_input(
    "🔍 Volltextsuche (Posten / Amt)",
    value="",
    placeholder="z.B. Gewerbesteuer, Jugend, Feuerwehr...",
)

st.sidebar.markdown("---")
st.sidebar.caption(
    f"**Datenbasis (15 PDFs & heidelberg.de, 2013–2029):**\n"
    f"- Doppelhaushalte **2013–2026** (**{df['Amt'].nunique()} Teilhaushalte**, **{len(df):,} Einzelpositionen**)\n"
    f"- **1. Nachtragshaushalt 2026** (Beschluss 18.12.2025 + Okt-2026-Prognose & Finanzplan **bis 2029**)\n"
    f"- **Jahresabschlüsse 2023 & 2024** inkl. **10-Jahres-Bilanz (2015–2024)**, Stellenplan (2.658 VZÄ), Investitionsprogramm & 359 Gemeinderat-Anträge."
)

# --- HEADER ---
st.title("🏛️ Haushalt & Finanzen der Stadt Heidelberg — Explorer (2013–2029)")
st.markdown(
    "Umfassende Analyse aller **Teilhaushalte (2013–2026)**, des **1. Nachtragshaushalts 2026 (+42,04 Mio. € Konsolidierung & Okt-2026-Prognose)**, "
    "der **Mittelfristigen Finanzplanung bis 2029**, des geprüften **Jahresabschlusses 2024**, der **10-Jahres-Schlussbilanz (1,78 Mrd. €)**, "
    "des **Investitionsprogramms 2024–2029**, der **Hebesätze im BW-Städtevergleich** sowie aller **359 Gemeinderat-Änderungsanträge**."
)

# --- GLOBAL KPI METRICS FOR SELECTED YEAR ---
year_df = year_base_df
if selected_aemter:
    year_df = year_df[year_df["Amt"].isin(selected_aemter)]
if search_query.strip():
    q = search_query.strip().lower()
    year_df = year_df[year_df["Search_Blob"].str.contains(q, regex=False, na=False)]

prev_year = selected_year - 1
prev_df = df_by_year.get(prev_year, pd.DataFrame())
if not prev_df.empty and selected_aemter:
    prev_df = prev_df[prev_df["Amt"].isin(selected_aemter)]
if not prev_df.empty and search_query.strip():
    q = search_query.strip().lower()
    prev_df = prev_df[prev_df["Search_Blob"].str.contains(q, regex=False, na=False)]

aufw_cur = year_df[year_df["Typ"] == "Aufwendungen"]["Betrag"].sum()
ertr_cur = year_df[year_df["Typ"] == "Erträge"]["Betrag"].sum()
saldo_cur = ertr_cur - aufw_cur
deckung_cur = (ertr_cur / aufw_cur * 100.0) if aufw_cur > 0 else 0.0

aufw_delta_str = None
ertr_delta_str = None
saldo_delta_str = None
if not prev_df.empty:
    aufw_prev = prev_df[prev_df["Typ"] == "Aufwendungen"]["Betrag"].sum()
    ertr_prev = prev_df[prev_df["Typ"] == "Erträge"]["Betrag"].sum()
    saldo_prev = ertr_prev - aufw_prev
    if aufw_prev != 0:
        d_a = aufw_cur - aufw_prev
        p_a = (d_a / abs(aufw_prev)) * 100.0
        aufw_delta_str = f"{d_a / 1e6:+.2f} Mio. € ({p_a:+.1f}%) ggü. {prev_year}".replace(".", ",")
    if ertr_prev != 0:
        d_e = ertr_cur - ertr_prev
        p_e = (d_e / abs(ertr_prev)) * 100.0
        ertr_delta_str = f"{d_e / 1e6:+.2f} Mio. € ({p_e:+.1f}%) ggü. {prev_year}".replace(".", ",")
    d_s = saldo_cur - saldo_prev
    saldo_delta_str = f"{d_s / 1e6:+.2f} Mio. € ggü. {prev_year}".replace(".", ",")

k1, k2, k3, k4 = st.columns(4)
with k1:
    st.metric(
        label=f"Ordentliche Aufwendungen ({selected_year})",
        value=fmt_eur(aufw_cur, 0),
        delta=aufw_delta_str,
        delta_color="inverse",
    )
with k2:
    st.metric(
        label=f"Ordentliche Erträge ({selected_year})",
        value=fmt_eur(ertr_cur, 0),
        delta=ertr_delta_str,
        delta_color="normal",
    )
with k3:
    st.metric(
        label=f"Ordentliches Ergebnis / Saldo ({selected_year})",
        value=fmt_eur(saldo_cur, 0),
        delta=saldo_delta_str,
        delta_color="normal",
    )
with k4:
    st.metric(
        label=f"Kostendeckungsgrad ({selected_year})",
        value=f"{deckung_cur:.1f} %".replace(".", ","),
        delta=f"{year_df['Amt'].nunique()} Teilhaushalte aktiv",
        delta_color="off",
    )

# --- TABS ---
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    [
        "🧩 Kacheln & Drill-Down (2013–26)",
        "📈 Zeitreihen & Treiber (2013–26)",
        "🏛️ Gesamthaushalt (2013–29)",
        "🚨 1. Nachtrag 2026 & Finanzplan",
        "🏦 Bilanz, JA 2024 & Konzern",
        "🏗️ Investitionen, Steuern & Gemeinderat",
    ]
)

# ==============================================================================
# TAB 1: TREEMAP / SUNBURST + BREAKDOWN CHARTS + AGGRID DRILL-DOWN TABLE
# ==============================================================================
with tab1:
    filtered_df = year_df[year_df["Typ"] == selected_type].copy()

    if filtered_df.empty:
        st.warning(f"Keine Daten für {selected_type} im Jahr {selected_year} mit den aktuellen Filtern gefunden.")
    else:
        filtered_df = filtered_df.sort_values(by="Betrag", ascending=False)

        # Group by hierarchy
        grouped_df = filtered_df.groupby(["Amt", "Kategorie", "Sub_Kategorie"], as_index=False)["Betrag"].sum()

        neg_df = grouped_df[grouped_df["Betrag"] < 0]
        pos_df = grouped_df[grouped_df["Betrag"] > 0].copy()

        if not neg_df.empty:
            neg_sum = neg_df["Betrag"].sum()
            neg_items = ", ".join(
                f"{r['Amt']}: {r['Sub_Kategorie']} ({fmt_eur(r['Betrag'], 0)})" for _, r in neg_df.iterrows()
            )
            st.caption(
                f"ℹ️ **Hinweis zur Kachel-Darstellung:** Im Gesamtsaldo ({fmt_eur(filtered_df['Betrag'].sum(), 0)}) "
                f"sind pauschale Minderaufwendungen/Absetzungen in Höhe von **{fmt_eur(neg_sum, 0)}** enthalten ({neg_items}). "
                f"Die Flächenanteile im Diagramm zeigen die positiven Brutto-Ansätze ({fmt_eur(pos_df['Betrag'].sum(), 0)})."
            )

        pos_df["Sub_Label"] = np.where(
            pos_df["Sub_Kategorie"] == pos_df["Kategorie"],
            pos_df["Sub_Kategorie"] + " (Gesamtposition)",
            pos_df["Sub_Kategorie"],
        )

        if hierarchy_mode.startswith("Amt"):
            path_cols = [px.Constant(f"Gesamt {selected_type} ({selected_year})"), "Amt", "Kategorie", "Sub_Label"]
            color_col = "Amt"
        else:
            path_cols = [px.Constant(f"Gesamt {selected_type} ({selected_year})"), "Kategorie", "Amt", "Sub_Label"]
            color_col = "Kategorie"

        if chart_type == "Sunburst (Ring)":
            fig = px.sunburst(
                pos_df,
                path=path_cols,
                values="Betrag",
                color=color_col,
                title=f"Interaktives Sunburst-Diagramm der {selected_type} im Jahr {selected_year} ({YEAR_STATUS.get(selected_year, '')})",
                color_discrete_sequence=px.colors.qualitative.Prism,
            )
        else:
            fig = px.treemap(
                pos_df,
                path=path_cols,
                values="Betrag",
                color=color_col,
                title=f"Drillable Tile-Chart (Treemap) der {selected_type} im Jahr {selected_year} ({YEAR_STATUS.get(selected_year, '')})",
                color_discrete_sequence=px.colors.qualitative.Prism,
            )

        if fig.data:
            vals = fig.data[0].values
            formatted_vals = [fmt_eur(float(v), 0) for v in vals]
            fig.data[0].customdata = formatted_vals
            fig.data[0].texttemplate = "<b>%{label}</b><br>%{customdata}<br>%{percentParent:.1%} (v. Überkat.)"
            fig.data[0].hovertemplate = (
                "<b>%{label}</b><br>"
                "Betrag: <b>%{customdata}</b><br>"
                "Anteil an Überkategorie: <b>%{percentParent:.2%}</b><br>"
                "Anteil am Gesamthaushalt: <b>%{percentRoot:.2%}</b>"
                "<extra></extra>"
            )

        fig.update_layout(
            margin=dict(t=55, l=15, r=15, b=15),
            height=720,
            title_font_size=20,
            font_family="Arial, sans-serif",
            template="plotly_white",
        )
        st.plotly_chart(fig, use_container_width=True)

        # --- SUMMARY BAR CHARTS BELOW TREEMAP ---
        col_left, col_right = st.columns(2)
        with col_left:
            amt_sum = (
                filtered_df.groupby("Amt", as_index=False)["Betrag"]
                .sum()
                .sort_values("Betrag", ascending=False)
                .head(15)
            )
            amt_sum["Amt_Kurz"] = amt_sum["Amt"].apply(short_amt)
            amt_sum["Betrag_Text"] = amt_sum["Betrag"].apply(fmt_mio)
            fig_amt = px.bar(
                amt_sum,
                x="Betrag",
                y="Amt_Kurz",
                orientation="h",
                text="Betrag_Text",
                color="Betrag",
                color_continuous_scale="Reds" if selected_type == "Aufwendungen" else "Greens",
                title=f"Top 15 Ämter / Teilhaushalte — {selected_type} ({selected_year})",
            )
            max_amt_val = float(amt_sum["Betrag"].max()) if not amt_sum.empty else 1.0
            fig_amt.update_traces(
                textposition="outside",
                cliponaxis=False,
                hovertemplate="<b>%{y}</b><br>Betrag: %{x:,.0f} €<extra></extra>",
            )
            fig_amt.update_layout(
                yaxis={"categoryorder": "total ascending", "title": ""},
                xaxis=dict(title="Betrag (€)", range=[0, max_amt_val * 1.24]),
                coloraxis_showscale=False,
                height=460,
                margin=dict(t=45, l=10, r=30, b=20),
                template="plotly_white",
            )
            st.plotly_chart(fig_amt, use_container_width=True)

        with col_right:
            kat_sum = (
                filtered_df.groupby("Kategorie", as_index=False)["Betrag"]
                .sum()
                .sort_values("Betrag", ascending=False)
            )
            kat_sum["Betrag_Text"] = kat_sum["Betrag"].apply(fmt_mio)
            fig_kat = px.bar(
                kat_sum,
                x="Betrag",
                y="Kategorie",
                orientation="h",
                text="Betrag_Text",
                color="Betrag",
                color_continuous_scale="OrRd" if selected_type == "Aufwendungen" else "Tealgrn",
                title=f"Verteilung nach Kategorie — {selected_type} ({selected_year})",
            )
            max_kat_val = float(kat_sum["Betrag"].max()) if not kat_sum.empty else 1.0
            fig_kat.update_traces(
                textposition="outside",
                cliponaxis=False,
                hovertemplate="<b>%{y}</b><br>Betrag: %{x:,.0f} €<extra></extra>",
            )
            fig_kat.update_layout(
                yaxis={"categoryorder": "total ascending", "title": ""},
                xaxis=dict(title="Betrag (€)", range=[0, max_kat_val * 1.24]),
                coloraxis_showscale=False,
                height=460,
                margin=dict(t=45, l=10, r=30, b=20),
                template="plotly_white",
            )
            st.plotly_chart(fig_kat, use_container_width=True)

        # --- INTERACTIVE AGGRID TABLE ---
        st.markdown("---")
        t_head_l, t_head_r = st.columns([3, 1])
        with t_head_l:
            st.subheader(f"📋 Extrahierte Positionen ({selected_type} {selected_year} — {len(filtered_df):,} Zeilen)")
            st.caption(
                "Interaktive Drill-Down-Tabelle mit **echter numerischer Sortierung** und **automatischer Summenbildung** "
                "auf Amts- und Kategorie-Ebene."
            )
        with t_head_r:
            csv_bytes = filtered_df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
            st.download_button(
                label="📥 Als CSV herunterladen",
                data=csv_bytes,
                file_name=f"haushalt_heidelberg_{selected_type.lower()}_{selected_year}.csv",
                mime="text/csv",
                use_container_width=True,
            )

        display_df = filtered_df[["Amt", "Kategorie", "Sub_Kategorie", "Betrag"]].reset_index(drop=True).copy()
        total_sel = display_df["Betrag"].sum()
        display_df["Anteil_%"] = np.where(total_sel != 0, (display_df["Betrag"] / total_sel) * 100.0, 0.0)

        gb = GridOptionsBuilder.from_dataframe(display_df)
        gb.configure_column("Amt", rowGroup=True, hide=True)
        gb.configure_column("Kategorie", rowGroup=True, hide=True)
        gb.configure_column("Sub_Kategorie", header_name="Einzelposten (Erläuterung)", flex=2, filter=True)
        gb.configure_column(
            "Betrag",
            header_name="Betrag (EUR)",
            type=["numericColumn", "numberColumnFilter"],
            aggFunc="sum",
            valueFormatter=EUR_FORMATTER,
            sort="desc",
            flex=1,
        )
        gb.configure_column(
            "Anteil_%",
            header_name="Anteil (%)",
            type=["numericColumn", "numberColumnFilter"],
            aggFunc="sum",
            valueFormatter=PCT_FORMATTER,
            flex=1,
        )

        grid_options = gb.build()
        grid_options["autoGroupColumnDef"] = {
            "headerName": "Amt / Kategorie (Aufklappen für Details)",
            "minWidth": 340,
            "flex": 2,
            "cellRendererParams": {"suppressCount": False},
        }
        grid_options["groupDefaultExpanded"] = 0
        grid_options["suppressAggFuncInHeader"] = True

        AgGrid(
            display_df,
            gridOptions=grid_options,
            columns_auto_size_mode=ColumnsAutoSizeMode.FIT_ALL_COLUMNS_TO_VIEW,
            height=520,
            theme="streamlit",
            allow_unsafe_jscode=True,
            enable_enterprise_modules=True,
        )


# ==============================================================================
# TAB 2: ZEITLICHE ENTWICKLUNG & KOSTENTREIBER (2013 - 2026)
# ==============================================================================
with tab2:
    st.subheader("📈 Größte Veränderungen & Treiber-Analyse (2013–2026)")

    ctrl1, ctrl2, ctrl3, ctrl4, ctrl5 = st.columns([1.3, 1, 1, 1.4, 1.2])
    all_years_sorted = sorted(df["Jahr"].unique())
    with ctrl1:
        top_typ_label = st.radio(
            "Haushaltsseite:",
            ["Aufwendungen (Kosten)", "Erträge (Einnahmen)"],
            key="tab2_typ",
        )
        typ_filter = "Aufwendungen" if "Aufwendungen" in top_typ_label else "Erträge"
    with ctrl2:
        default_start = all_years_sorted.index(2013) if 2013 in all_years_sorted else 0
        start_yr = st.selectbox("Basisjahr (Von)", all_years_sorted, index=default_start, key="tab2_start")
    with ctrl3:
        default_end = all_years_sorted.index(2026) if 2026 in all_years_sorted else len(all_years_sorted) - 1
        end_yr = st.selectbox("Zieljahr (Bis)", all_years_sorted, index=default_end, key="tab2_end")
    with ctrl4:
        rank_mode = st.radio(
            "Sortierung der Top 30:",
            ["Absolute Steigerung (€)", "Prozentuales Wachstum (%)"],
            key="tab2_rank",
        )
    with ctrl5:
        agg_level = st.selectbox(
            "Analyse-Ebene",
            ["Einzelposten (Sub_Kategorie)", "Amt × Kategorie", "Teilhaushalt (Amt gesamt)"],
            key="tab2_level",
        )
        min_base = st.number_input(
            "Mindestvolumen Basisjahr (€)",
            min_value=0,
            max_value=10_000_000,
            value=50_000,
            step=25_000,
            key="tab2_minbase",
        )

    if start_yr >= end_yr:
        st.warning("Bitte wähle ein Basisjahr, das vor dem Zieljahr liegt (z.B. 2013 bis 2026).")
    else:
        growth_base_df = df[df["Typ"] == typ_filter].copy()
        if selected_aemter:
            growth_base_df = growth_base_df[growth_base_df["Amt"].isin(selected_aemter)]

        if agg_level == "Teilhaushalt (Amt gesamt)":
            grp_cols = ["Amt"]
        elif agg_level == "Amt × Kategorie":
            grp_cols = ["Amt", "Kategorie"]
        else:
            grp_cols = ["Amt", "Kategorie", "Sub_Kategorie"]

        pivot_df = (
            growth_base_df[growth_base_df["Jahr"].isin([start_yr, end_yr])]
            .groupby(grp_cols + ["Jahr"])["Betrag"]
            .sum()
            .unstack("Jahr")
            .reset_index()
        )

        if start_yr in pivot_df.columns and end_yr in pivot_df.columns:
            pivot_df[start_yr] = pivot_df[start_yr].fillna(0.0)
            pivot_df[end_yr] = pivot_df[end_yr].fillna(0.0)
            pivot_df["Delta_EUR"] = pivot_df[end_yr] - pivot_df[start_yr]
            pivot_df["Wachstum_%"] = np.where(
                pivot_df[start_yr].abs() > 0,
                (pivot_df["Delta_EUR"] / pivot_df[start_yr].abs()) * 100.0,
                np.nan,
            )

            valid_growth = pivot_df[pivot_df[start_yr].abs() >= min_base].copy()
            if rank_mode == "Absolute Steigerung (€)":
                top_growth = valid_growth.sort_values("Delta_EUR", ascending=False).head(30).copy()
                x_col = "Delta_EUR"
                x_title = f"Absolute Veränderung {start_yr} ➔ {end_yr} (in €)"
            else:
                valid_pct = valid_growth[valid_growth["Wachstum_%"].notna() & ~np.isinf(valid_growth["Wachstum_%"])]
                top_growth = valid_pct.sort_values("Wachstum_%", ascending=False).head(30).copy()
                x_col = "Wachstum_%"
                x_title = f"Prozentuale Veränderung {start_yr} ➔ {end_yr} (in %)"

            def make_unique_label(row):
                amt_code = str(row["Amt"]).split(" ")[1] if str(row["Amt"]).startswith("TH ") else str(row["Amt"])[:12]
                if agg_level == "Teilhaushalt (Amt gesamt)":
                    return str(row["Amt"])
                elif agg_level == "Amt × Kategorie":
                    return f"TH {amt_code} | {row['Kategorie']}"
                else:
                    sub = str(row["Sub_Kategorie"])
                    if len(sub) > 52:
                        sub = sub[:50] + "…"
                    return f"TH {amt_code} | {sub}"

            raw_labels = [make_unique_label(r) for _, r in top_growth.iterrows()]
            seen = {}
            unique_labels = []
            for lbl in raw_labels:
                if lbl not in seen:
                    seen[lbl] = 1
                    unique_labels.append(lbl)
                else:
                    seen[lbl] += 1
                    unique_labels.append(f"{lbl} (#{seen[lbl]})")
            top_growth["Pfad"] = unique_labels
            top_growth["Start_Text"] = top_growth[start_yr].apply(lambda v: fmt_eur(v, 0))
            top_growth["End_Text"] = top_growth[end_yr].apply(lambda v: fmt_eur(v, 0))
            top_growth["Delta_Text"] = top_growth["Delta_EUR"].apply(lambda v: ("+" if v >= 0 else "") + fmt_eur(v, 0))
            top_growth["Pct_Text"] = top_growth["Wachstum_%"].apply(
                lambda v: f"{v:+.1f} %".replace(".", ",") if pd.notna(v) else "neu"
            )

            color_scale = "Reds" if typ_filter == "Aufwendungen" else "Greens"
            fig_growth = px.bar(
                top_growth,
                x=x_col,
                y="Pfad",
                orientation="h",
                color=x_col,
                color_continuous_scale=color_scale,
                custom_data=["Amt", "Start_Text", "End_Text", "Delta_Text", "Pct_Text"],
                title=f"Top {len(top_growth)} Treiber ({typ_filter}: {start_yr} ➔ {end_yr}, Basis ≥ {fmt_eur(min_base, 0)})",
            )
            fig_growth.update_traces(
                hovertemplate=(
                    "<b>%{y}</b><br>"
                    "Amt: %{customdata[0]}<br>"
                    f"Wert {start_yr}: <b>%{{customdata[1]}}</b><br>"
                    f"Wert {end_yr}: <b>%{{customdata[2]}}</b><br>"
                    "Veränderung (€): <b>%{customdata[3]}</b><br>"
                    "Veränderung (%): <b>%{customdata[4]}</b>"
                    "<extra></extra>"
                )
            )
            fig_growth.update_layout(
                yaxis={"categoryorder": "total ascending", "title": ""},
                xaxis_title=x_title,
                height=max(500, len(top_growth) * 26 + 100),
                margin=dict(t=50, l=20, r=30, b=30),
                template="plotly_white",
            )
            st.plotly_chart(fig_growth, use_container_width=True)
        else:
            st.warning(f"Für die Jahre {start_yr} und {end_yr} liegen keine Vergleichsdaten vor.")

    # --- TIME SERIES EXPLORER (2013 - 2026) ---
    st.markdown("---")
    st.subheader("⏱️ Mehrjahres-Zeitreihe (2013–2026) nach Amt, Kategorie & Einzelposten")
    st.caption("Kaskadierende Auswahl: Wähle *Alle* auf einer Ebene, um die aggregierte 14-Jahres-Entwicklung zu betrachten.")

    c0, c1, c2, c3 = st.columns(4)
    with c0:
        ts_typ = st.selectbox("1. Haushaltsseite", ["Aufwendungen", "Erträge"], key="ts_typ")

    ts_base_df = df[df["Typ"] == ts_typ]

    with c1:
        amt_list = ["Alle Ämter (Gesamthaushalt)"] + sorted(ts_base_df["Amt"].unique().tolist())
        ts_amt = st.selectbox("2. Amt / Teilhaushalt", amt_list, key="ts_amt")

    if ts_amt != "Alle Ämter (Gesamthaushalt)":
        ts_base_df = ts_base_df[ts_base_df["Amt"] == ts_amt]

    with c2:
        cat_list = ["Alle Kategorien"] + sorted(ts_base_df["Kategorie"].unique().tolist())
        ts_cat = st.selectbox("3. Kategorie", cat_list, key="ts_cat")

    if ts_cat != "Alle Kategorien":
        ts_base_df = ts_base_df[ts_base_df["Kategorie"] == ts_cat]

    with c3:
        sub_list = ["Alle Einzelposten (Summe)"] + sorted(ts_base_df["Sub_Kategorie"].unique().tolist())
        ts_sub = st.selectbox("4. Einzelposten", sub_list, key="ts_sub")

    if ts_sub != "Alle Einzelposten (Summe)":
        ts_base_df = ts_base_df[ts_base_df["Sub_Kategorie"] == ts_sub]

    ts_data = ts_base_df.groupby("Jahr", as_index=False)["Betrag"].sum().sort_values("Jahr")

    if not ts_data.empty:
        non_zero = ts_data[ts_data["Betrag"] != 0]
        base_val = non_zero.iloc[0]["Betrag"] if not non_zero.empty else 0.0
        base_yr = int(non_zero.iloc[0]["Jahr"]) if not non_zero.empty else int(ts_data.iloc[0]["Jahr"])

        ts_data["Entwicklung_gg_Basis_%"] = (
            ((ts_data["Betrag"] - base_val) / abs(base_val) * 100.0) if base_val != 0 else 0.0
        )

        title_parts = [ts_typ, ts_amt]
        if ts_cat != "Alle Kategorien":
            title_parts.append(ts_cat)
        if ts_sub != "Alle Einzelposten (Summe)":
            title_parts.append(ts_sub)

        fig_ts = px.line(
            ts_data,
            x="Jahr",
            y="Betrag",
            markers=True,
            text="Entwicklung_gg_Basis_%",
            title=f"Zeitreihe ({ts_data['Jahr'].min()}–{ts_data['Jahr'].max()}): {' ➔ '.join(title_parts)} (Basis: {base_yr})",
        )
        fig_ts.update_traces(
            line=dict(width=3, color="#dc2626" if ts_typ == "Aufwendungen" else "#16a34a"),
            marker=dict(size=10),
            texttemplate="%{text:+.1f}%",
            textposition="top center",
            hovertemplate="<b>Jahr %{x}</b><br>Betrag: <b>%{y:,.0f} €</b><br>Veränderung ggü. "
            + str(base_yr)
            + ": <b>%{text:+.1f}%</b><extra></extra>",
        )
        fig_ts.update_layout(
            xaxis=dict(tickmode="linear", dtick=1, title="Haushaltsjahr"),
            yaxis_title="Betrag (€)",
            height=460,
            margin=dict(t=55, l=20, r=20, b=30),
            template="plotly_white",
        )
        st.plotly_chart(fig_ts, use_container_width=True)


# ==============================================================================
# TAB 3: GESAMTHAUSHALT (2013 - 2029) & ÄMTER-SALDO-VERGLEICH
# ==============================================================================
with tab3:
    st.subheader("🏛️ 17-Jahres-Entwicklung des Gesamthaushalts (2013–2029)")
    st.markdown(
        "Kombiniert die **geprüften Ist-Ergebnisse 2013–2024** (aus dem *Jahresabschluss 2024*, Teil VI Statistiken) "
        "mit dem **Haushaltsplan 2025**, dem **1. Nachtragshaushalt 2026** und der **Mittelfristigen Finanzplanung 2027–2029**."
    )

    df_macro = supp.get("macro", pd.DataFrame())
    if not df_macro.empty:
        df_m = df_macro.copy()
        df_m["Ertraege_EUR"] = df_m["Ordentliche_Ertraege_TEUR"] * 1000.0
        df_m["Aufwendungen_EUR"] = df_m["Ordentliche_Aufwendungen_TEUR"] * 1000.0
        df_m["Saldo_EUR"] = df_m["Ordentliches_Ergebnis_TEUR"] * 1000.0
        df_m["Label"] = df_m["Jahr"].astype(str) + " (" + df_m["Status"].str.split(" ").str[0] + ")"

        fig_macro = go.Figure()
        fig_macro.add_trace(
            go.Bar(
                x=df_m["Label"],
                y=df_m["Ertraege_EUR"],
                name="Ordentliche Erträge",
                marker_color="#16a34a",
                text=df_m["Ertraege_EUR"].apply(fmt_mio),
                textposition="outside",
            )
        )
        fig_macro.add_trace(
            go.Bar(
                x=df_m["Label"],
                y=df_m["Aufwendungen_EUR"],
                name="Ordentliche Aufwendungen",
                marker_color="#dc2626",
                text=df_m["Aufwendungen_EUR"].apply(fmt_mio),
                textposition="outside",
            )
        )
        fig_macro.add_trace(
            go.Scatter(
                x=df_m["Label"],
                y=df_m["Saldo_EUR"],
                name="Ordentliches Ergebnis (Saldo)",
                mode="lines+markers+text",
                line=dict(color="#1d4ed8", width=3, dash="dot"),
                marker=dict(size=9),
                text=df_m["Saldo_EUR"].apply(fmt_mio),
                textposition="bottom center",
            )
        )
        fig_macro.update_layout(
            barmode="group",
            title="Ordentliche Erträge vs. Aufwendungen & Ordentliches Ergebnis (2013–2029, Ist & Finanzplanung)",
            xaxis_title="Haushaltsjahr",
            yaxis_title="Betrag (€)",
            height=540,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            template="plotly_white",
        )
        st.plotly_chart(fig_macro, use_container_width=True)

        # Cashflow & Reserves vs. Debt Chart (2013-2029)
        c_m1, c_m2 = st.columns(2)
        with c_m1:
            fig_cf = go.Figure()
            fig_cf.add_trace(
                go.Bar(
                    x=df_m["Jahr"],
                    y=df_m["Cashflow_Laufend_TEUR"] / 1000.0,
                    name="Zahlungsmittelüberschuss/-bedarf lfd. Verwaltung (Mio. €)",
                    marker_color=np.where(df_m["Cashflow_Laufend_TEUR"] >= 0, "#0d9488", "#e11d48"),
                )
            )
            fig_cf.add_trace(
                go.Scatter(
                    x=df_m["Jahr"],
                    y=df_m["Investitionsauszahlungen_TEUR"] / 1000.0,
                    name="Investitionsauszahlungen (Mio. €)",
                    mode="lines+markers",
                    line=dict(color="#f59e0b", width=3),
                )
            )
            fig_cf.update_layout(
                title="Laufender Cashflow vs. Investitionsauszahlungen (2013–2029, in Mio. €)",
                xaxis=dict(tickmode="linear", dtick=2),
                yaxis_title="Mio. €",
                height=420,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                template="plotly_white",
            )
            st.plotly_chart(fig_cf, use_container_width=True)

        with c_m2:
            fig_debt = go.Figure()
            fig_debt.add_trace(
                go.Scatter(
                    x=df_m["Jahr"],
                    y=df_m["Schulden_Kernhaushalt_TEUR"] / 1000.0,
                    name="Schulden Kernhaushalt (Mio. €)",
                    mode="lines+markers",
                    line=dict(color="#dc2626", width=3),
                    fill="tozeroy",
                )
            )
            fig_debt.add_trace(
                go.Scatter(
                    x=df_m["Jahr"],
                    y=df_m["Ergebnisruecklagen_TEUR"] / 1000.0,
                    name="Ergebnisrücklagen / Fehlbetrag (Mio. €)",
                    mode="lines+markers",
                    line=dict(color="#2563eb", width=3, dash="dash"),
                )
            )
            fig_debt.update_layout(
                title="Schuldenstand Kernhaushalt vs. Ergebnisrücklagen (2013–2029, in Mio. €)",
                xaxis=dict(tickmode="linear", dtick=2),
                yaxis_title="Mio. €",
                height=420,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                template="plotly_white",
            )
            st.plotly_chart(fig_debt, use_container_width=True)

    st.markdown("---")
    st.subheader(f"⚖️ Netto-Ressourcen-/Zuschussbedarf je Teilhaushalt im Jahr {selected_year}")
    st.write(
        "Zeigt für jedes Amt das **Ordentliche Ergebnis (`Erträge − Aufwendungen`)**: "
        "**Rot** = Netto-Zuschussbedarf (Ausgaben übersteigen eigene Einnahmen), "
        "**Grün** = Netto-Überschuss (insb. `TH FW Allgemeine Finanzwirtschaft` durch Steuern & Schlüsselzuweisungen)."
    )

    amt_piv = (
        year_df.groupby(["Amt", "Typ"], as_index=False)["Betrag"]
        .sum()
        .pivot(index="Amt", columns="Typ", values="Betrag")
        .fillna(0.0)
        .reset_index()
    )
    if "Erträge" not in amt_piv.columns:
        amt_piv["Erträge"] = 0.0
    if "Aufwendungen" not in amt_piv.columns:
        amt_piv["Aufwendungen"] = 0.0
    amt_piv["Ordentliches_Ergebnis"] = amt_piv["Erträge"] - amt_piv["Aufwendungen"]
    amt_piv["Richtung"] = np.where(amt_piv["Ordentliches_Ergebnis"] >= 0, "Überschuss (+)", "Zuschussbedarf (-)")
    amt_piv = amt_piv.sort_values("Ordentliches_Ergebnis", ascending=True)

    exclude_fw = st.checkbox(
        "TH FW (Allgemeine Finanzwirtschaft) im Saldo-Chart ausblenden, um Fachämter besser zu skalieren",
        value=True,
    )
    plot_amt_piv = amt_piv[~amt_piv["Amt"].str.startswith("TH FW")].copy() if exclude_fw else amt_piv.copy()

    fig_saldo = px.bar(
        plot_amt_piv,
        x="Ordentliches_Ergebnis",
        y="Amt",
        orientation="h",
        color="Richtung",
        color_discrete_map={"Überschuss (+)": "#16a34a", "Zuschussbedarf (-)": "#dc2626"},
        custom_data=["Erträge", "Aufwendungen"],
        title=f"Ordentliches Ergebnis (Erträge − Aufwendungen) je Teilhaushalt ({selected_year})",
    )
    fig_saldo.update_traces(
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Ordentliches Ergebnis: <b>%{x:,.0f} €</b><br>"
            "Ordentliche Erträge: %{customdata[0]:,.0f} €<br>"
            "Ordentliche Aufwendungen: %{customdata[1]:,.0f} €"
            "<extra></extra>"
        )
    )
    fig_saldo.update_layout(
        yaxis={"categoryorder": "total descending", "title": ""},
        xaxis_title="Ordentliches Ergebnis: Erträge − Aufwendungen (€)",
        height=max(550, len(plot_amt_piv) * 22 + 100),
        template="plotly_white",
    )
    st.plotly_chart(fig_saldo, use_container_width=True)


# ==============================================================================
# TAB 4: 1. NACHTRAGSHAUSHALT 2026 & FINANZPLANUNG BIS 2029
# ==============================================================================
with tab4:
    st.subheader("🚨 1. Nachtragshaushalt 2026 (Beschluss 18.12.2025) — Konsolidierungspaket")
    st.info(
        "**Hintergrund:** Nach Beanstandungen des Regierungspräsidiums Karlsruhe zum Doppelhaushalt 2025/2026 hat der "
        "Gemeinderat am **18. Dezember 2025** den **1. Nachtragshaushalt 2026** (`20_pdf_nachtragshaushalt_2026.pdf`, 238 Seiten) "
        "beschlossen. Durch **+25,20 Mio. € höhere Erträge** (u.a. Beibehaltung Gewerbesteuer-Hebesatz auf 400%, höhere Schlüsselzuweisungen) "
        "und **-16,84 Mio. € geringere Aufwendungen** (u.a. 5%-Kürzung freiwilliger Zuschüsse, Sachkostenreduktion, höherer globaler Minderaufwand) "
        "verbessert sich das veranschlagte Ordentliche Ergebnis 2026 um **+42,04 Mio. €** (von **-82,65 Mio. €** auf **-40,62 Mio. €**), "
        "und der Zahlungsmittelsaldo im Ergebnishaushalt dreht von **-28,93 Mio. €** auf **+11,19 Mio. € Überschuss**."
    )

    nh1, nh2, nh3, nh4 = st.columns(4)
    nh1.metric("Ordentliche Erträge 2026 (Neu)", "868.460.060 €", "+25,20 Mio. € (+3,0%) ggü. Ursprungsplan")
    nh2.metric(
        "Ordentliche Aufwendungen 2026 (Neu)",
        "909.078.188 €",
        "-16,84 Mio. € (-1,8%) Einsparung",
        delta_color="inverse",
    )
    nh3.metric("Ordentliches Ergebnis 2026 (Neu)", "-40.618.128 €", "+42,04 Mio. € Verbesserung")
    nh4.metric("Cashflow Ergebnishaushalt 2026", "+11.188.802 €", "+40,12 Mio. € (von -28,93 Mio. €)")

    df_nh_ges = supp.get("nh_gesamt", pd.DataFrame())
    df_nh_aemter = supp.get("nh_aemter", pd.DataFrame())
    df_nh_mass = supp.get("nh_massnahmen", pd.DataFrame())

    if not df_nh_ges.empty:
        col_nh_l, col_nh_r = st.columns(2)
        with col_nh_l:
            df_nh_delta = df_nh_ges[df_nh_ges["Aenderung_2026_EUR"] != 0].copy()
            df_nh_delta["Wirksamkeit_EUR"] = np.where(
                df_nh_delta["Typ"] == "Erträge",
                df_nh_delta["Aenderung_2026_EUR"],
                -df_nh_delta["Aenderung_2026_EUR"],
            )
            df_nh_delta["Delta_Text"] = df_nh_delta["Aenderung_2026_EUR"].apply(
                lambda v: ("+" if v >= 0 else "") + fmt_mio(v)
            )
            fig_nh_cat = px.bar(
                df_nh_delta.sort_values("Wirksamkeit_EUR", ascending=True),
                x="Wirksamkeit_EUR",
                y="Position",
                color="Typ",
                orientation="h",
                text="Delta_Text",
                color_discrete_map={"Erträge": "#16a34a", "Aufwendungen": "#2563eb"},
                custom_data=["Bisher_2026_EUR", "Neu_2026_EUR", "Haupttreiber"],
                title=" Ergebnisverbesserung (+42,04 Mio. €) nach Position im 1. Nachtrag 2026",
            )
            fig_nh_cat.update_traces(
                textposition="outside",
                cliponaxis=False,
                hovertemplate=(
                    "<b>%{y}</b><br>"
                    "Entlastungsbeitrag: <b>%{x:,.0f} €</b><br>"
                    "Bisher 2026: %{customdata[0]:,.0f} €<br>"
                    "Neu 2026: %{customdata[1]:,.0f} €<br>"
                    "Treiber: %{customdata[2]}<extra></extra>"
                ),
            )
            fig_nh_cat.update_layout(
                xaxis_title="Verbesserung des Ordentlichen Ergebnisses 2026 (€)",
                yaxis_title="",
                height=460,
                margin=dict(t=45, l=10, r=40, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                template="plotly_white",
            )
            st.plotly_chart(fig_nh_cat, use_container_width=True)

        with col_nh_r:
            if not df_nh_aemter.empty:
                amt_erg = df_nh_aemter[
                    df_nh_aemter["Position"].str.contains("Anteiliges ordentliches Ergebnis", case=False, na=False)
                ].copy()
                amt_erg = amt_erg[amt_erg["Aenderung_2026"] != 0].sort_values("Aenderung_2026", ascending=False)
                amt_erg["Amt_Kurz"] = amt_erg["Amt"].apply(short_amt)
                amt_erg["Delta_Text"] = amt_erg["Aenderung_2026"].apply(
                    lambda v: ("+" if v >= 0 else "") + fmt_mio(v)
                )
                fig_nh_amt = px.bar(
                    amt_erg.head(18),
                    x="Aenderung_2026",
                    y="Amt_Kurz",
                    orientation="h",
                    text="Delta_Text",
                    color="Aenderung_2026",
                    color_continuous_scale="Tealgrn",
                    custom_data=["Amt", "Bisher_2026", "Neu_2026"],
                    title="Top 18 Teilhaushalte nach Ergebnisverbesserung im 1. Nachtrag 2026",
                )
                fig_nh_amt.update_traces(
                    textposition="outside",
                    cliponaxis=False,
                    hovertemplate=(
                        "<b>%{customdata[0]}</b><br>"
                        "Ergebnis-Verbesserung: <b>%{x:+,.0f} €</b><br>"
                        "Bisheriges Ergebnis 2026: %{customdata[1]:,.0f} €<br>"
                        "Neues Ergebnis 2026: %{customdata[2]:,.0f} €<extra></extra>"
                    ),
                )
                fig_nh_amt.update_layout(
                    yaxis={"categoryorder": "total ascending", "title": ""},
                    xaxis_title="Verbesserung des anteiligen ordentlichen Ergebnisses (€)",
                    coloraxis_showscale=False,
                    height=460,
                    margin=dict(t=45, l=10, r=40, b=20),
                    template="plotly_white",
                )
                st.plotly_chart(fig_nh_amt, use_container_width=True)

    # --- STRUCTURAL CAUSES FROM OFFICIAL CITY GRAPHICS ---
    st.markdown("---")
    st.subheader("📊 Strukturelle Ursachen des Haushaltsdefizits (Städtische Analysedokumente 2025/2026)")
    c_cause1, c_cause2 = st.columns(2)
    with c_cause1:
        df_bund = pd.DataFrame([
            {"Bereich": "Sozial- & Jugendhilfe (u.a. BTHG Eingliederungshilfe)", "Jahr": "2025", "Mehrkosten_Mio": 39.1},
            {"Bereich": "Sozial- & Jugendhilfe (u.a. BTHG Eingliederungshilfe)", "Jahr": "2026", "Mehrkosten_Mio": 44.5},
            {"Bereich": "Betreuung in Kindertageseinrichtungen (Kita)", "Jahr": "2025", "Mehrkosten_Mio": 28.7},
            {"Bereich": "Betreuung in Kindertageseinrichtungen (Kita)", "Jahr": "2026", "Mehrkosten_Mio": 32.7},
            {"Bereich": "Bildung (u.a. Rechtsanspruch Ganztagsförderung Grundschule)", "Jahr": "2025", "Mehrkosten_Mio": 11.6},
            {"Bereich": "Bildung (u.a. Rechtsanspruch Ganztagsförderung Grundschule)", "Jahr": "2026", "Mehrkosten_Mio": 12.2},
        ])
        fig_bund = px.bar(
            df_bund,
            x="Jahr",
            y="Mehrkosten_Mio",
            color="Bereich",
            text="Mehrkosten_Mio",
            title="Ausgabensteigerungen durch Bundesbeschlüsse (+80 Mio. € in 2025 / +90 Mio. € in 2026 ggü. 2021)",
            color_discrete_sequence=["#dc2626", "#f97316", "#eab308"],
        )
        fig_bund.update_traces(texttemplate="+%{text:.1f} Mio. €", textposition="inside")
        fig_bund.update_layout(
            yaxis_title="Mehrkosten ggü. 2021 (in Mio. €)",
            height=400,
            legend=dict(orientation="h", yanchor="bottom", y=-0.35, xanchor="left", x=0),
            template="plotly_white",
        )
        st.plotly_chart(fig_bund, use_container_width=True)

    with c_cause2:
        df_rev_loss = pd.DataFrame([
            {"Ursache": "Gewerbesteuer-Einbruch 2024 (135 statt 158 Mio. € Prognose)", "Verlust_Mio": -23.0},
            {"Ursache": "Schlüsselzuweisungen 2025/26 (Einwohnerkorrektur durch Zensus 2022)", "Verlust_Mio": -30.0},
        ])
        fig_loss = px.bar(
            df_rev_loss,
            x="Verlust_Mio",
            y="Ursache",
            orientation="h",
            text="Verlust_Mio",
            color="Ursache",
            color_discrete_sequence=["#be123c", "#9f1239"],
            title="Besondere strukturelle Einnahmeverluste (-53 Mio. € durch Wirtschaftskrise & Zensus)",
        )
        fig_loss.update_traces(texttemplate="%{text:.0f} Mio. €", textposition="inside")
        fig_loss.update_layout(
            xaxis_title="Einnahmeverlust (in Mio. €)",
            yaxis_title="",
            showlegend=False,
            height=400,
            template="plotly_white",
        )
        st.plotly_chart(fig_loss, use_container_width=True)

    # --- LINE-ITEM CONSOLIDATION TABLE FROM 1. NACHTRAG 2026 ---
    if not df_nh_mass.empty:
        st.markdown("---")
        st.subheader(f"✂️ Alle {len(df_nh_mass)} Einzel-Änderungsmaßnahmen im 1. Nachtragshaushalt 2026")
        st.caption(
            "Durchsuche alle konkreten Kürzungen, 5%-Zuschussreduzierungen (`Kuerzung_5_Prozent_Freiwillig = True`), "
            "Investitionsverschiebungen und Einnahmeerhöhungen aus den Teilhaushalten (`Seiten 67–236`)."
        )
        f_c1, f_c2 = st.columns([2, 1])
        with f_c1:
            nh_search = st.text_input(
                "🔍 Maßnahme oder Amt im Nachtragshaushalt filtern:",
                value="",
                placeholder="z.B. Stadtteilbudget, Kultur, Zuschuss, Schwimmbad, Gewerbesteuer...",
            )
        with f_c2:
            only_5pct = st.checkbox("Nur 5%-Kürzungen freiwilliger Zuschüsse (*) anzeigen", value=False)

        view_mass = df_nh_mass.copy()
        if nh_search.strip():
            q_nh = nh_search.strip().lower()
            view_mass = view_mass[
                view_mass["Amt"].str.lower().str.contains(q_nh, na=False)
                | view_mass["Massnahme"].str.lower().str.contains(q_nh, na=False)
                | view_mass["Kategorie"].str.lower().str.contains(q_nh, na=False)
            ]
        if only_5pct:
            view_mass = view_mass[view_mass["Kuerzung_5_Prozent_Freiwillig"] == True]

        view_mass = view_mass.sort_values("Aenderung_2026", ascending=True)
        st.dataframe(
            view_mass,
            use_container_width=True,
            height=420,
            column_config={
                "Bisher_2026": st.column_config.NumberColumn("Bisher 2026 (€)", format="%.0f €"),
                "Aenderung_2026": st.column_config.NumberColumn("Änderung (+/- €)", format="%+.0f €"),
                "Neu_2026": st.column_config.NumberColumn("Neu 2026 (€)", format="%.0f €"),
            },
        )


# ==============================================================================
# TAB 5: BILANZ (2015-2024), JAHRESABSCHLUSS 2024, STELLENPLAN & KONZERN
# ==============================================================================
with tab5:
    st.subheader("🏦 10-Jahres-Schlussbilanz (2015–2024) & Vorbelastungen (Jahresabschluss 2024)")
    df_bilanz = supp.get("bilanz", pd.DataFrame())
    df_vorb = supp.get("vorbelastungen", pd.DataFrame())
    df_ja24 = supp.get("ja2024_aemter", pd.DataFrame())
    df_pers = supp.get("personal", pd.DataFrame())
    df_bet = supp.get("beteiligungen", pd.DataFrame())

    b1, b2, b3, b4 = st.columns(4)
    b1.metric("Bilanzsumme (31.12.2024)", "1.780,06 Mio. €", "+22,43 Mio. € (+1,3%) ggü. 2023")
    b2.metric("Eigenkapital / Kapitalposition (2024)", "1.006,93 Mio. €", "-37,47 Mio. € (Eigenkapitalquote 56,6%)")
    b3.metric(
        "Verbindlichkeiten Bilanz (2024)",
        "431,15 Mio. €",
        "+79,47 Mio. € (+22,6%) ggü. 2023",
        delta_color="inverse",
    )
    b4.metric(
        "Vorbelastungen künftiger Jahre (2024)",
        "1.220,57 Mio. €",
        "Bürgschaften 634 Mio. € + Pensionen/Beihilfe 542 Mio. €",
        delta_color="off",
    )

    if not df_bilanz.empty:
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            akt_df = df_bilanz[df_bilanz["Seite"] == "Aktiva"].copy()
            fig_akt = px.area(
                akt_df,
                x="Jahr",
                y="Betrag_TEUR",
                color="Position",
                title="Aktiva-Entwicklung 2015–2024 (in T€, Bilanzsumme 1,78 Mrd. €)",
            )
            fig_akt.update_layout(
                xaxis=dict(tickmode="linear", dtick=1),
                yaxis_title="Betrag (in T€)",
                height=450,
                legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="left", x=0, font=dict(size=10)),
                template="plotly_white",
            )
            st.plotly_chart(fig_akt, use_container_width=True)

        with col_b2:
            pas_df = df_bilanz[df_bilanz["Seite"] == "Passiva"].copy()
            fig_pas = px.area(
                pas_df,
                x="Jahr",
                y="Betrag_TEUR",
                color="Position",
                title="Passiva-Entwicklung 2015–2024 (Eigenkapital, Rücklagen, Schulden in T€)",
            )
            fig_pas.update_layout(
                xaxis=dict(tickmode="linear", dtick=1),
                yaxis_title="Betrag (in T€)",
                height=450,
                legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="left", x=0, font=dict(size=10)),
                template="plotly_white",
            )
            st.plotly_chart(fig_pas, use_container_width=True)

    # --- VORBELASTUNGEN & KONZERNVERSCHULDUNG ---
    st.markdown("---")
    col_v1, col_v2 = st.columns(2)
    with col_v1:
        st.subheader("⚠️ Außerbilanzielle Vorbelastungen (1,221 Mrd. €)")
        if not df_vorb.empty:
            fig_vorb = px.bar(
                df_vorb.sort_values("Stand_2024_TEUR", ascending=True),
                x="Stand_2024_TEUR",
                y="Kategorie",
                orientation="h",
                color="Stand_2024_TEUR",
                color_continuous_scale="OrRd",
                custom_data=["Stand_2023_TEUR", "Erlaeuterung"],
                title="Vorbelastungen künftiger Haushaltsjahre zum 31.12.2024 (in T€)",
            )
            fig_vorb.update_traces(
                hovertemplate=(
                    "<b>%{y}</b><br>"
                    "Stand 31.12.2024: <b>%{x:,.0f} T€</b><br>"
                    "Stand 31.12.2023: %{customdata[0]:,.0f} T€<br>"
                    "Info: %{customdata[1]}<extra></extra>"
                )
            )
            fig_vorb.update_layout(
                yaxis_title="",
                xaxis_title="Betrag (in T€)",
                coloraxis_showscale=False,
                height=400,
                template="plotly_white",
            )
            st.plotly_chart(fig_vorb, use_container_width=True)

    with col_v2:
        st.subheader("🏢 Städtische Gesellschaften, Eigenbetriebe & Schulden 2026")
        if not df_bet.empty:
            st.dataframe(
                df_bet,
                use_container_width=True,
                height=400,
                column_config={
                    "Ertraege_2026_TEUR": st.column_config.NumberColumn("Erträge 2026 (T€)", format="%.0f T€"),
                    "Aufwendungen_2026_TEUR": st.column_config.NumberColumn("Aufwendungen 2026 (T€)", format="%.0f T€"),
                    "Jahresergebnis_2026_TEUR": st.column_config.NumberColumn("Ergebnis 2026 (T€)", format="%+.0f T€"),
                    "Schulden_Ende_2026_TEUR": st.column_config.NumberColumn("Schulden Ende 2026 (T€)", format="%.0f T€"),
                },
            )

    # --- JAHRESABSCHLUSS 2024 PLAN VS IST & STELLENPLAN ---
    st.markdown("---")
    col_j1, col_j2 = st.columns(2)
    with col_j1:
        st.subheader("📊 Jahresabschluss 2024: Plan vs. Ist-Ergebnis je Amt")
        if not df_ja24.empty:
            ja_erg = df_ja24[
                df_ja24["Position"].str.contains("Anteiliges ordentliches Ergebnis", case=False, na=False)
            ].copy()
            ja_erg = ja_erg[~ja_erg["TH"].astype(str).isin(["FW"])].sort_values("Abweichung_2024", ascending=True)
            ja_erg["Amt_Kurz"] = ja_erg["Amt"].apply(short_amt)
            fig_ja = px.bar(
                ja_erg.head(20),
                x="Abweichung_2024",
                y="Amt_Kurz",
                orientation="h",
                color="Abweichung_2024",
                color_continuous_scale="RdYlGn",
                custom_data=["Amt", "Plan_2024", "Ist_2024"],
                title="Größte Budgetabweichungen 2024 (Ist vs. Fortgeschriebener Plan, in €)",
            )
            fig_ja.update_traces(
                hovertemplate=(
                    "<b>%{customdata[0]}</b><br>"
                    "Abweichung 2024: <b>%{x:+,.0f} €</b><br>"
                    "Plan 2024: %{customdata[1]:,.0f} €<br>"
                    "Ist 2024: %{customdata[2]:,.0f} €<extra></extra>"
                )
            )
            fig_ja.update_layout(
                yaxis_title="",
                xaxis_title="Abweichung Ist 2024 ggü. Plan 2024 (€)",
                coloraxis_showscale=False,
                height=480,
                template="plotly_white",
            )
            st.plotly_chart(fig_ja, use_container_width=True)

    with col_j2:
        st.subheader("👥 Personal & Stellenplan nach Amt (2.658 Stellen in 2025/26)")
        if not df_pers.empty:
            pers_25 = df_pers[df_pers["Jahr"] == 2025].sort_values("Planstellen", ascending=False).head(20).copy()
            pers_25["Amt_Kurz"] = pers_25["Amt"].apply(short_amt)
            fig_pers = go.Figure()
            fig_pers.add_trace(
                go.Bar(
                    y=pers_25["Amt_Kurz"],
                    x=pers_25["Beamte_Stellen"],
                    name="Beamtinnen & Beamte (733,75 gesamt)",
                    orientation="h",
                    marker_color="#1d4ed8",
                )
            )
            fig_pers.add_trace(
                go.Bar(
                    y=pers_25["Amt_Kurz"],
                    x=pers_25["Tarif_Stellen"],
                    name="Tarifbeschäftigte (1.924,25 gesamt)",
                    orientation="h",
                    marker_color="#0d9488",
                )
            )
            fig_pers.update_layout(
                barmode="stack",
                yaxis={"categoryorder": "total ascending", "title": ""},
                xaxis_title="Planstellen 2025/2026 (Vollzeitäquivalente)",
                title="Top 20 Ämter nach Planstellen 2025/2026 (Beamte vs. Tarifbeschäftigte)",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                height=480,
                template="plotly_white",
            )
            st.plotly_chart(fig_pers, use_container_width=True)


# ==============================================================================
# TAB 6: INVESTITIONSPROGRAMM, STEUERN/HEBESÄTZE, GEMEINDERAT & KONSISTENZ-CHECK
# ==============================================================================
with tab6:
    st.subheader("🏗️ Investitionsprogramm (2024–2029), Steuern & Hebesätze im BW-Städtevergleich & Gemeinderat-Anträge")
    st.info(
        "**Aktuelles Update (Pressemitteilung Stadt Heidelberg vom 16.10.2026):** Die Kämmerei prognostiziert für das "
        "laufende Haushaltsjahr 2026 ein **Gewerbesteuer-Aufkommen von 166,0 Mio. €** (+4,5 Mio. € über dem 1. Nachtragshaushalt). "
        "Im Finanzhaushalt verbessert sich der Gesamtkapitalbedarf um **+16,4 Mio. €**, wodurch die benötigte **Netto-Neuverschuldung "
        "2026 von 71,8 Mio. € auf 55,4 Mio. €** sinkt!"
    )

    df_steuern = supp.get("steuern", pd.DataFrame())
    df_hebesaetze = supp.get("hebesaetze", pd.DataFrame())
    df_invest = supp.get("investitionen", pd.DataFrame())
    df_antraege = supp.get("antraege", pd.DataFrame())

    i1, i2, i3, i4 = st.columns(4)
    i1.metric("Gewerbesteuer 2026 (Okt-Prognose)", "166,00 Mio. €", "+4,50 Mio. € ggü. 1. Nachtrag (Hebesatz 400%)")
    i2.metric("Grundsteuer B Hebesatz (ab 2025)", "190 v.H.", "Niedrigster Satz aller 9 BW-Stadtkreise (vorher 400%)")
    i3.metric("Kreditbedarf 2026 (Okt-Prognose)", "55,40 Mio. €", "-16,40 Mio. € geringer als im Nachtrag (71,8 Mio. €)", delta_color="inverse")
    i4.metric("Investitionsprogramm 2024–2029", "494,68 Mio. €", "29 Schwerpunktprojekte + SWH Wärmewende")

    col_s1, col_s2 = st.columns(2)
    with col_s1:
        if not df_steuern.empty:
            st_rows = df_steuern[df_steuern["Kategorie"] == "Steuererträge"].copy()
            fig_st = go.Figure()
            fig_st.add_trace(
                go.Bar(
                    y=st_rows["Position"],
                    x=st_rows["Ist_2024"] / 1e6,
                    name="Ist 2024",
                    orientation="h",
                    marker_color="#64748b",
                )
            )
            fig_st.add_trace(
                go.Bar(
                    y=st_rows["Position"],
                    x=st_rows["Nachtrag_2026"] / 1e6,
                    name="1. Nachtrag 2026",
                    orientation="h",
                    marker_color="#2563eb",
                )
            )
            fig_st.add_trace(
                go.Bar(
                    y=st_rows["Position"],
                    x=st_rows["Prognose_Okt2026"] / 1e6,
                    name="Okt-Prognose 2026",
                    orientation="h",
                    marker_color="#16a34a",
                )
            )
            fig_st.update_layout(
                barmode="group",
                yaxis={"categoryorder": "total ascending", "title": ""},
                xaxis_title="Mio. €",
                title="Steuererträge der Stadt Heidelberg (Ist 2024 vs. Nachtrag 2026 vs. Okt-Prognose 2026)",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                height=440,
                template="plotly_white",
            )
            st.plotly_chart(fig_st, use_container_width=True)

    with col_s2:
        if not df_hebesaetze.empty:
            fig_heb = go.Figure()
            fig_heb.add_trace(
                go.Bar(
                    x=df_hebesaetze["Stadtkreis"],
                    y=df_hebesaetze["Gewerbesteuer_Prozent"],
                    name="Gewerbesteuer (v.H.)",
                    marker_color="#1d4ed8",
                    text=df_hebesaetze["Gewerbesteuer_Prozent"],
                    textposition="outside",
                )
            )
            fig_heb.add_trace(
                go.Bar(
                    x=df_hebesaetze["Stadtkreis"],
                    y=df_hebesaetze["Grundsteuer_B_Neu_2025_Prozent"],
                    name="Grundsteuer B neu ab 2025 (v.H.)",
                    marker_color="#0d9488",
                    text=df_hebesaetze["Grundsteuer_B_Neu_2025_Prozent"],
                    textposition="outside",
                )
            )
            fig_heb.add_trace(
                go.Scatter(
                    x=df_hebesaetze["Stadtkreis"],
                    y=df_hebesaetze["Grundsteuer_B_Alt_2024_Prozent"],
                    name="Grundsteuer B alt bis 2024 (v.H.)",
                    mode="markers+lines",
                    line=dict(color="#dc2626", dash="dot", width=2),
                    marker=dict(size=8),
                )
            )
            fig_heb.update_layout(
                barmode="group",
                yaxis_title="Hebesatz in v.H. (%)",
                xaxis_title="",
                title="Hebesatz-Vergleich der 9 Stadtkreise in Baden-Württemberg (HP 2025/26 S. 1108)",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                height=440,
                template="plotly_white",
            )
            st.plotly_chart(fig_heb, use_container_width=True)

    if not df_steuern.empty:
        with st.expander("📊 Alle Steuerpositionen, Finanzausgleich & amtliche Pro-Kopf-Kennzahlen (€/EW) anzeigen", expanded=False):
            st.dataframe(df_steuern, use_container_width=True, height=380)

    # --- INVESTITIONSPROGRAMM 2024 - 2029 ---
    st.markdown("---")
    st.subheader("🏗️ Schwerpunktprojekte im Investitionsprogramm 2024–2029 (1. Nachtrag 2026 S. 36–43)")
    if not df_invest.empty:
        col_i1, col_i2 = st.columns([1.2, 1.3])
        with col_i1:
            bau_df = df_invest[~df_invest["TH"].isin(["FW"])].sort_values("Gesamtkosten_TEUR", ascending=True).tail(18)
            fig_inv = px.bar(
                bau_df,
                x="Gesamtkosten_TEUR",
                y="Projekt",
                orientation="h",
                color="Amt",
                custom_data=["Zuschuss_Gesamt_TEUR", "Erlaeuterung"],
                title="Top 18 Hoch- & Tiefbauprojekte nach Gesamtkosten (in T€)",
            )
            fig_inv.update_traces(
                hovertemplate="<b>%{y}</b><br>Gesamtkosten: <b>%{x:,.0f} T€</b><br>Förderung/Zuschuss: %{customdata[0]:,.0f} T€<br>%{customdata[1]}<extra></extra>"
            )
            fig_inv.update_layout(
                yaxis_title="",
                xaxis_title="Gesamtkosten (in T€)",
                legend=dict(orientation="h", yanchor="top", y=-0.18, xanchor="left", x=0, font=dict(size=10)),
                height=500,
                template="plotly_white",
            )
            st.plotly_chart(fig_inv, use_container_width=True)

        with col_i2:
            st.dataframe(
                df_invest.sort_values("Gesamtkosten_TEUR", ascending=False),
                use_container_width=True,
                height=500,
                column_config={
                    "Gesamtkosten_TEUR": st.column_config.NumberColumn("Gesamtkosten (T€)", format="%.0f T€"),
                    "Auszahlung_2025_TEUR": st.column_config.NumberColumn("2025 (T€)", format="%.0f T€"),
                    "Auszahlung_2026_TEUR": st.column_config.NumberColumn("2026 (T€)", format="%.0f T€"),
                    "Zuschuss_Gesamt_TEUR": st.column_config.NumberColumn("Zuschuss (T€)", format="%.0f T€"),
                },
            )

    # --- GEMEINDERAT ÄNDERUNGSANTRÄGE 2025/2026 ---
    st.markdown("---")
    st.subheader("🗳️ Gemeinderat-Änderungsanträge zum Doppelhaushalt 2025/2026 (359 Anträge)")
    if not df_antraege.empty:
        a_c1, a_c2, a_c3 = st.columns([1.2, 1.5, 1])
        with a_c1:
            fraktionen = ["Alle Fraktionen"] + sorted(df_antraege["Fraktion"].unique().tolist())
            sel_frak = st.selectbox("Fraktion / Partei filtern:", fraktionen, key="ant_frak")
        with a_c2:
            ant_search = st.text_input(
                "🔍 Antragstext, Maßnahme oder Teilhaushalt durchsuchen:",
                value="",
                placeholder="z.B. Kultur, Radweg, Tourismusabgabe, Schule, Gewerbesteuer...",
                key="ant_q",
            )
        with a_c3:
            hide_satire = st.checkbox("Satire-Anträge (Rathauscasino 360 Mio. €) ausblenden", value=True, key="ant_sat")

        view_ant = df_antraege.copy()
        if hide_satire:
            view_ant = view_ant[view_ant["Ist_Satire"] == False]
        if sel_frak != "Alle Fraktionen":
            view_ant = view_ant[view_ant["Fraktion"] == sel_frak]
        if ant_search.strip():
            qa = ant_search.strip().lower()
            view_ant = view_ant[
                view_ant["Titel"].fillna("").str.lower().str.contains(qa, regex=False)
                | view_ant["Beschreibung"].fillna("").str.lower().str.contains(qa, regex=False)
                | view_ant["TH"].fillna("").str.lower().str.contains(qa, regex=False)
            ]

        frak_cnt = (
            df_antraege[df_antraege["Ist_Satire"] == False]
            .groupby("Fraktion", as_index=False)
            .agg(Antraege=("Nr", "count"), Netto_25_26=("Netto_Entlastung_2025_26_EUR", "sum"))
            .sort_values("Antraege", ascending=True)
        )
        col_a_chart, col_a_tbl = st.columns([1, 1.6])
        with col_a_chart:
            fig_ant = px.bar(
                frak_cnt,
                x="Antraege",
                y="Fraktion",
                orientation="h",
                color="Antraege",
                color_continuous_scale="Blues",
                title="Anzahl der Haushalts-Änderungsanträge nach Fraktion",
            )
            fig_ant.update_layout(yaxis_title="", coloraxis_showscale=False, height=380, template="plotly_white")
            st.plotly_chart(fig_ant, use_container_width=True)
        with col_a_tbl:
            st.dataframe(
                view_ant[
                    [
                        "Nr", "Fraktion", "TH", "Haushaltstyp", "Titel",
                        "Ertrag_Aenderung_2025_EUR", "Aufwand_Aenderung_2025_EUR",
                        "Ertrag_Aenderung_2026_EUR", "Aufwand_Aenderung_2026_EUR",
                        "Stellungnahme_Verwaltung",
                    ]
                ],
                use_container_width=True,
                height=380,
            )

    # --- LIVE INTERNAL CONSISTENCY AUDIT PANEL ---
    st.markdown("---")
    st.subheader("✅ Automatisierte Interne Finanz-Konsistenzprüfung (Reconciliation Matrix)")
    st.caption(
        "Prüft in Echtzeit die mathematische Übereinstimmung zwischen Einzelposten, Teilhaushalten, Gesamtergebnishaushalt, "
        "Schlussbilanz und Stellenplan über alle Datenquellen hinweg."
    )
    df_aemter_check = pd.read_csv(DATA_DIR / "haushalt_heidelberg_aemter.csv", encoding="utf-8")
    diff_deep_aemter = abs(df["Betrag"].sum() - df_aemter_check["Betrag"].sum())

    nh_ges_e = df_nh_ges[df_nh_ges["Typ"] == "Erträge"]["Neu_2026_EUR"].sum() if not df_nh_ges.empty else 0.0
    nh_amt_e = (
        df_nh_aemter[df_nh_aemter["Position"] == "Anteilige ordentliche Erträge"]["Neu_2026"].sum()
        if not df_nh_aemter.empty
        else 0.0
    )
    nh_ges_a = df_nh_ges[df_nh_ges["Typ"] == "Aufwendungen"]["Neu_2026_EUR"].sum() if not df_nh_ges.empty else 0.0
    nh_amt_a = (
        df_nh_aemter[df_nh_aemter["Position"] == "Anteilige ordentliche Aufwendungen"]["Neu_2026"].sum()
        if not df_nh_aemter.empty
        else 0.0
    )

    akt_24 = df_bilanz[(df_bilanz["Jahr"] == 2024) & (df_bilanz["Seite"] == "Aktiva")]["Betrag_TEUR"].sum() if not df_bilanz.empty else 0.0
    pas_24 = df_bilanz[(df_bilanz["Jahr"] == 2024) & (df_bilanz["Seite"] == "Passiva")]["Betrag_TEUR"].sum() if not df_bilanz.empty else 0.0

    pers_25_sum = df_pers[df_pers["Jahr"] == 2025]["Planstellen"].sum() if not df_pers.empty else 0.0

    reconcil_rows = [
        {
            "Prüfregel (Accounting Identity)": "1. Teilhaushalte Deep (8.539 Posten) == Ämter-Summen (2013–2026)",
            "Soll-Wert (Referenz)": fmt_eur(df_aemter_check["Betrag"].sum(), 2),
            "Ist-Wert (Aggregiert)": fmt_eur(df["Betrag"].sum(), 2),
            "Differenz": fmt_eur(diff_deep_aemter, 2),
            "Status": "✅ 100% Konsistent" if diff_deep_aemter < 0.01 else "❌ Abweichung",
        },
        {
            "Prüfregel (Accounting Identity)": "2. 1. Nachtrag 2026: Summe 41 Teilhaushalte Erträge == Gesamtergebnishaushalt",
            "Soll-Wert (Referenz)": fmt_eur(nh_ges_e, 2),
            "Ist-Wert (Aggregiert)": fmt_eur(nh_amt_e, 2),
            "Differenz": fmt_eur(abs(nh_ges_e - nh_amt_e), 2),
            "Status": "✅ 100% Konsistent" if abs(nh_ges_e - nh_amt_e) < 0.01 else "❌ Abweichung",
        },
        {
            "Prüfregel (Accounting Identity)": "3. 1. Nachtrag 2026: Summe 41 Teilhaushalte Aufwendungen == Gesamtergebnishaushalt",
            "Soll-Wert (Referenz)": fmt_eur(nh_ges_a, 2),
            "Ist-Wert (Aggregiert)": fmt_eur(nh_amt_a, 2),
            "Differenz": fmt_eur(abs(nh_ges_a - nh_amt_a), 2),
            "Status": "✅ 100% Konsistent" if abs(nh_ges_a - nh_amt_a) < 0.01 else "❌ Abweichung",
        },
        {
            "Prüfregel (Accounting Identity)": "4. Schlussbilanz 2015–2024: Aktiva == Passiva == Bilanzsumme (2024: 1.780.058 T€)",
            "Soll-Wert (Referenz)": f"{akt_24:,.0f} T€".replace(",", "."),
            "Ist-Wert (Aggregiert)": f"{pas_24:,.0f} T€".replace(",", "."),
            "Differenz": f"{abs(akt_24 - pas_24):,.2f} T€",
            "Status": "✅ 100% Konsistent" if abs(akt_24 - pas_24) < 0.01 else "❌ Abweichung",
        },
        {
            "Prüfregel (Accounting Identity)": "5. Stellenplan 2025/2026: Beamte (733,75) + Tarif (1.924,25) == 2.658,00 VZÄ",
            "Soll-Wert (Referenz)": "2.658,00 VZÄ",
            "Ist-Wert (Aggregiert)": f"{pers_25_sum:,.2f} VZÄ".replace(",", "X").replace(".", ",").replace("X", "."),
            "Differenz": f"{abs(2658.0 - pers_25_sum):.2f} VZÄ",
            "Status": "✅ 100% Konsistent" if abs(2658.0 - pers_25_sum) < 0.01 else "❌ Abweichung",
        },
    ]
    st.dataframe(pd.DataFrame(reconcil_rows), use_container_width=True, hide_index=True)

