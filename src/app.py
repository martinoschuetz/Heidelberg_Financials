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
    page_title="Haushalt Heidelberg Explorer (2017–2026)",
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
    return df


@st.cache_data
def load_macro_data() -> pd.DataFrame:
    try:
        df_real = pd.read_csv(DATA_DIR / "haushalt_heidelberg_real.csv", encoding="utf-8")
        df_real["Jahr"] = df_real["Jahr"].astype(int)
        df_real["Betrag"] = pd.to_numeric(df_real["Betrag"], errors="coerce").fillna(0.0)
        return df_real
    except Exception:
        return pd.DataFrame()


df = load_data()
df_macro = load_macro_data()

YEAR_STATUS = {
    2017: "Ergebnis",
    2018: "Plan",
    2019: "Ergebnis",
    2020: "Plan",
    2021: "Ergebnis",
    2022: "Plan",
    2023: "Ergebnis",
    2024: "Plan",
    2025: "Plan",
    2026: "Plan",
}

valid_years = sorted(df["Jahr"].unique(), reverse=True)
default_year_idx = valid_years.index(2025) if 2025 in valid_years else 0

# --- SIDEBAR FILTERS ---
st.sidebar.title("🏛️ Haushalt-Filter")
selected_year = st.sidebar.selectbox(
    "Haushaltsjahr auswählen",
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

all_aemter_for_year = sorted(df[df["Jahr"] == selected_year]["Amt"].unique().tolist())
selected_aemter = st.sidebar.multiselect(
    "Ämter / Teilhaushalte filtern (optional)",
    options=all_aemter_for_year,
    default=[],
    placeholder="Alle 41 Teilhaushalte",
)

search_query = st.sidebar.text_input(
    "🔍 Volltextsuche (Posten / Amt)",
    value="",
    placeholder="z.B. Gewerbesteuer, Jugend, Feuerwehr...",
)

st.sidebar.markdown("---")
st.sidebar.caption(
    f"**Datenbasis:** Offizielle Haushaltspläne der Stadt Heidelberg (2017–2026), "
    f"**{df['Amt'].nunique()} Teilhaushalte**, **{len(df):,} Einzelpositionen**."
)

# --- HEADER ---
st.title("🏛️ Haushalt der Stadt Heidelberg — Interaktiver Explorer (2017–2026)")
st.markdown(
    "Vollständig abgestimmte **Ergebnishaushalts- & Teilhaushalts-Analyse** aller **41 Ämter / Teilhaushalte** "
    "(`TH 01` bis `TH FW Allgemeine Finanzwirtschaft`) inklusive der detaillierten **Erläuterungs-Einzelposten** "
    "aus den offiziellen Haushaltsplänen der Stadt Heidelberg."
)

# --- GLOBAL KPI METRICS FOR SELECTED YEAR ---
year_df = df[df["Jahr"] == selected_year]
if selected_aemter:
    year_df = year_df[year_df["Amt"].isin(selected_aemter)]
if search_query.strip():
    q = search_query.strip().lower()
    year_df = year_df[
        year_df["Amt"].str.lower().str.contains(q, na=False)
        | year_df["Kategorie"].str.lower().str.contains(q, na=False)
        | year_df["Sub_Kategorie"].str.lower().str.contains(q, na=False)
    ]

prev_year = selected_year - 1
prev_df = df[df["Jahr"] == prev_year] if prev_year in valid_years else pd.DataFrame()
if not prev_df.empty and selected_aemter:
    prev_df = prev_df[prev_df["Amt"].isin(selected_aemter)]
if not prev_df.empty and search_query.strip():
    q = search_query.strip().lower()
    prev_df = prev_df[
        prev_df["Amt"].str.lower().str.contains(q, na=False)
        | prev_df["Kategorie"].str.lower().str.contains(q, na=False)
        | prev_df["Sub_Kategorie"].str.lower().str.contains(q, na=False)
    ]

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
tab1, tab2, tab3 = st.tabs(
    [
        "🧩 Kachel-Ansicht & Drill-Down (Jahres-Fokus)",
        "📈 Zeitliche Entwicklung & Kostentreiber (2017–2026)",
        "🏛️ Gesamthaushalt & Ämter-Saldo-Vergleich",
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

        # Separate positive positions from negative global adjustments (e.g. Globaler Minderaufwand = -3.000.000 €)
        # so Treemap/Sunburst areas and percentages are never distorted by .abs() on negative offsets.
        neg_df = grouped_df[grouped_df["Betrag"] < 0]
        pos_df = grouped_df[grouped_df["Betrag"] > 0].copy()

        if not neg_df.empty:
            neg_sum = neg_df["Betrag"].sum()
            neg_items = ", ".join(f"{r['Amt']}: {r['Sub_Kategorie']} ({fmt_eur(r['Betrag'], 0)})" for _, r in neg_df.iterrows())
            st.caption(
                f"ℹ️ **Hinweis zur Kachel-Darstellung:** Im Gesamtsaldo ({fmt_eur(filtered_df['Betrag'].sum(), 0)}) "
                f"sind pauschale Minderaufwendungen in Höhe von **{fmt_eur(neg_sum, 0)}** enthalten ({neg_items}). "
                f"Die Flächenanteile im Diagramm zeigen die positiven Brutto-Ansätze ({fmt_eur(pos_df['Betrag'].sum(), 0)})."
            )

        # Prevent parent-child label collisions in Plotly hierarchy
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

        # Format Euro values directly from fig.data[0].values (never splitting node_id on '/')
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

        # --- INTERACTIVE AGGRID TABLE (WITH TRUE NUMERIC SORTING & SUM AGGREGATION) ---
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

        eur_formatter = JsCode(
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
        pct_formatter = JsCode(
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

        gb = GridOptionsBuilder.from_dataframe(display_df)
        gb.configure_column("Amt", rowGroup=True, hide=True)
        gb.configure_column("Kategorie", rowGroup=True, hide=True)
        gb.configure_column("Sub_Kategorie", header_name="Einzelposten (Erläuterung)", flex=2, filter=True)
        gb.configure_column(
            "Betrag",
            header_name="Betrag (EUR)",
            type=["numericColumn", "numberColumnFilter"],
            aggFunc="sum",
            valueFormatter=eur_formatter,
            sort="desc",
            flex=1,
        )
        gb.configure_column(
            "Anteil_%",
            header_name="Anteil (%)",
            type=["numericColumn", "numberColumnFilter"],
            aggFunc="sum",
            valueFormatter=pct_formatter,
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
# TAB 2: ZEITLICHE ENTWICKLUNG & KOSTENTREIBER (2017 - 2026)
# ==============================================================================
with tab2:
    st.subheader("📈 Größte Veränderungen & Treiber-Analyse")

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
        default_start = all_years_sorted.index(2023) if 2023 in all_years_sorted else 0
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
        st.warning("Bitte wähle ein Basisjahr, das vor dem Zieljahr liegt (z.B. 2023 bis 2026).")
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

            # Build unique, readable labels without truncation collisions
            def make_unique_label(row, idx):
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

            raw_labels = [make_unique_label(r, i) for i, (_, r) in enumerate(top_growth.iterrows())]
            # Disambiguate any identical labels so Plotly never stacks distinct bars
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

    # --- TIME SERIES EXPLORER (2017 - 2026) ---
    st.markdown("---")
    st.subheader("⏱️ Mehrjahres-Zeitreihe (2017–2026) nach Amt, Kategorie & Einzelposten")
    st.caption("Kaskadierende Auswahl: Wähle *Alle* auf einer Ebene, um die aggregierte Entwicklung zu betrachten.")

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
        # Use first non-zero value as baseline so percentage evolution never divides by zero
        non_zero = ts_data[ts_data["Betrag"] != 0]
        base_val = non_zero.iloc[0]["Betrag"] if not non_zero.empty else 0.0
        base_yr = int(non_zero.iloc[0]["Jahr"]) if not non_zero.empty else int(ts_data.iloc[0]["Jahr"])

        ts_data["Entwicklung_gg_Basis_%"] = (
            ((ts_data["Betrag"] - base_val) / abs(base_val) * 100.0) if base_val != 0 else 0.0
        )
        ts_data["YoY_%"] = ts_data["Betrag"].pct_change() * 100.0
        ts_data["Status"] = ts_data["Jahr"].map(lambda y: YEAR_STATUS.get(int(y), "Plan"))
        ts_data["Label_Text"] = ts_data.apply(
            lambda r: f"{fmt_mio(r['Betrag'])}\n({r['Entwicklung_gg_Basis_%']:+.1f}%)"
            if abs(r["Betrag"]) >= 1e6
            else f"{fmt_eur(r['Betrag'], 0)}\n({r['Entwicklung_gg_Basis_%']:+.1f}%)",
            axis=1,
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
# TAB 3: GESAMTHAUSHALT & ÄMTER-SALDO-VERGLEICH (2017 - 2026)
# ==============================================================================
with tab3:
    st.subheader("🏛️ Langfristige Entwicklung des Gesamthaushalts (2017–2026)")
    st.write(
        "Gegenüberstellung der **Ordentlichen Erträge**, **Ordentlichen Aufwendungen** und des "
        "**Ordentlichen Ergebnisses (Saldo)** der Stadt Heidelberg von 2017 bis 2026."
    )

    yearly_tot = (
        df.groupby(["Jahr", "Typ"], as_index=False)["Betrag"]
        .sum()
        .pivot(index="Jahr", columns="Typ", values="Betrag")
        .fillna(0.0)
        .reset_index()
    )
    yearly_tot["Saldo"] = yearly_tot.get("Erträge", 0.0) - yearly_tot.get("Aufwendungen", 0.0)
    yearly_tot["Status"] = yearly_tot["Jahr"].map(lambda y: f"{y} ({YEAR_STATUS.get(int(y), 'Plan')})")

    fig_macro = go.Figure()
    fig_macro.add_trace(
        go.Bar(
            x=yearly_tot["Status"],
            y=yearly_tot["Erträge"],
            name="Ordentliche Erträge",
            marker_color="#16a34a",
            text=yearly_tot["Erträge"].apply(fmt_mio),
            textposition="outside",
        )
    )
    fig_macro.add_trace(
        go.Bar(
            x=yearly_tot["Status"],
            y=yearly_tot["Aufwendungen"],
            name="Ordentliche Aufwendungen",
            marker_color="#dc2626",
            text=yearly_tot["Aufwendungen"].apply(fmt_mio),
            textposition="outside",
        )
    )
    fig_macro.add_trace(
        go.Scatter(
            x=yearly_tot["Status"],
            y=yearly_tot["Saldo"],
            name="Ordentliches Ergebnis (Saldo)",
            mode="lines+markers+text",
            line=dict(color="#1d4ed8", width=3, dash="dot"),
            marker=dict(size=9),
            text=yearly_tot["Saldo"].apply(fmt_mio),
            textposition="bottom center",
        )
    )
    fig_macro.update_layout(
        barmode="group",
        title="Ordentliche Erträge vs. Aufwendungen & Ordentliches Ergebnis (2017–2026)",
        xaxis_title="Haushaltsjahr",
        yaxis_title="Betrag (€)",
        height=520,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        template="plotly_white",
    )
    st.plotly_chart(fig_macro, use_container_width=True)

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
