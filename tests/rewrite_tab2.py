import re

with open("app.py", "r", encoding="utf-8") as f:
    content = f.read()

# We need to replace the entire 'with tab2:' block.
# Let's find the start of 'with tab2:'
parts = content.split("with tab2:")
tab1_code = parts[0]

tab2_code = """with tab2:
    st.subheader("Größte prozentuale Veränderungen (2023 - 2026)")
    st.write("Dieser Chart zeigt die Top 30 Posten (über alle Ämter hinweg), die im Zeitraum von 2023 bis 2026 prozentual am stärksten gewachsen sind (nur Posten mit > 50.000 € Basis-Volumen).")
    
    top30_typ = st.radio("Fokus der Top 30:", ["Aufwendungen (Kosten)", "Erträge (Einnahmen)"])
    typ_filter = "Aufwendungen" if "Aufwendungen" in top30_typ else "Erträge"
    color_scale = "Reds" if typ_filter == "Aufwendungen" else "Greens"
    
    # Calculate global growth for the selected type
    growth_base_df = df[df["Typ"] == typ_filter].copy()
    
    # Pivot to get years as columns
    pivot_df = growth_base_df.groupby(["Amt", "Kategorie", "Sub_Kategorie", "Jahr"])["Betrag"].sum().unstack("Jahr").reset_index()
    
    if 2023 in pivot_df.columns and 2026 in pivot_df.columns:
        # Calculate % change
        pivot_df["Wachstum_%"] = ((pivot_df[2026] - pivot_df[2023]) / pivot_df[2023].abs()) * 100
        
        # Filter out inf / small base effects (> 50.000 EUR base)
        valid_growth = pivot_df[(pivot_df[2023].abs() > 50000) & pivot_df["Wachstum_%"].notna() & ~np.isinf(pivot_df["Wachstum_%"])]
        top_growth = valid_growth.sort_values("Wachstum_%", ascending=False).head(30)
        
        # Clean up labels for the chart
        top_growth["Pfad"] = top_growth["Amt"].str.slice(0, 15) + " / " + top_growth["Sub_Kategorie"].str.slice(0, 30)
        
        # Create Bar Chart
        fig_growth = px.bar(
            top_growth, 
            x="Wachstum_%", 
            y="Pfad", 
            orientation="h",
            color="Wachstum_%",
            color_continuous_scale=color_scale,
            title=f"Top 30 Steigerungen ({typ_filter})"
        )
        fig_growth.update_layout(yaxis={'categoryorder':'total ascending'}, height=800)
        st.plotly_chart(fig_growth, use_container_width=True)
    else:
        st.warning("Für die Jahre 2023 und 2026 liegen nicht ausreichend Datenpunkte für den Vergleich vor.")

    st.markdown("---")
    st.subheader("Zeitliche Entwicklung (Zeitreihe) eines spezifischen Einzelpostens")
    st.write("Wähle hier den Pfad aus (die Filter reagieren kaskadierend aufeinander).")
    
    c0, c1, c2, c3 = st.columns(4)
    with c0:
        ts_typ = st.selectbox("0. Typ", ["Aufwendungen", "Erträge"], key="ts_typ")
    
    ts_base_df = df[df["Typ"] == ts_typ]
    
    with c1:
        ts_amt = st.selectbox("1. Amt auswählen", sorted(ts_base_df["Amt"].unique().tolist()), key="ts_amt")
    with c2:
        cat_opts = sorted(ts_base_df[ts_base_df["Amt"] == ts_amt]["Kategorie"].unique().tolist())
        if not cat_opts: cat_opts = ["Keine"]
        ts_cat = st.selectbox("2. Kategorie", cat_opts, key="ts_cat")
    with c3:
        sub_opts = sorted(ts_base_df[(ts_base_df["Amt"] == ts_amt) & (ts_base_df["Kategorie"] == ts_cat)]["Sub_Kategorie"].unique().tolist())
        if not sub_opts: sub_opts = ["Keine"]
        ts_sub = st.selectbox("3. Einzelposten", sub_opts, key="ts_sub")
        
    ts_data = ts_base_df[(ts_base_df["Amt"] == ts_amt) & (ts_base_df["Kategorie"] == ts_cat) & (ts_base_df["Sub_Kategorie"] == ts_sub)]
    ts_data = ts_data.groupby("Jahr")["Betrag"].sum().reset_index()
    ts_data = ts_data.sort_values("Jahr")
    
    if len(ts_data) > 0:
        base_val = ts_data.iloc[0]["Betrag"]
        ts_data["Prozentuale_Entwicklung"] = ((ts_data["Betrag"] - base_val) / abs(base_val) * 100) if base_val != 0 else 0
        
        fig_ts = px.line(
            ts_data, 
            x="Jahr", 
            y="Betrag", 
            markers=True,
            text="Prozentuale_Entwicklung",
            title=f"Entwicklung: {ts_sub}"
        )
        
        # Format text on points
        fig_ts.update_traces(texttemplate='%{text:+.1f}%', textposition='top center')
        # Ensure x-axis shows only integer years
        fig_ts.update_layout(xaxis=dict(tickmode='linear', dtick=1))
        
        st.plotly_chart(fig_ts, use_container_width=True)
"""

with open("app.py", "w", encoding="utf-8") as f:
    f.write(tab1_code + tab2_code)
print("app.py rewritten successfully with Top 30 and red/green scales!")
