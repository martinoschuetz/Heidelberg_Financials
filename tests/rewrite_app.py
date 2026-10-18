import re

with open("app.py", "r", encoding="utf-8") as f:
    content = f.read()

# We need to indent everything after st.title and st.markdown into tab1
# But actually, we can just insert the tabs creation after the title.

tab_creation_code = """
tab1, tab2 = st.tabs(["🧩 Kachel-Ansicht (Jahres-Fokus)", "📈 Zeitliche Entwicklung & Kostentreiber"])

with tab1:
"""

# Find where to split
split_marker = 'st.markdown("Dies ist eine **interaktive Tile-Chart'
parts = content.split(split_marker)

header = parts[0] + split_marker + parts[1].split('\n')[0] + '\n'
rest_of_code = '\n'.join(parts[1].split('\n')[1:])

# Indent rest of code for tab1
indented_rest = '\n'.join(['    ' + line if line.strip() else line for line in rest_of_code.split('\n')])

# Now append tab2 code
tab2_code = """
with tab2:
    st.subheader("Größte prozentuale Kostensteigerungen (2023 - 2026)")
    st.write("Dieser Chart zeigt die Top 15 Ausgaben-Posten (über alle Ämter hinweg), die im Zeitraum von 2023 bis 2026 prozentual am stärksten gewachsen sind (nur Posten mit > 50.000 € Basis-Volumen).")
    
    # Calculate global growth
    aufw_df = df[df["Typ"] == "Aufwendungen"].copy()
    
    # Pivot to get years as columns
    pivot_df = aufw_df.groupby(["Amt", "Kategorie", "Sub_Kategorie"])["Betrag"].sum().reset_index()
    # Wait, we need Jahr as columns. Let's do it properly:
    pivot_df = aufw_df.groupby(["Amt", "Kategorie", "Sub_Kategorie", "Jahr"])["Betrag"].sum().unstack("Jahr").reset_index()
    
    if 2023 in pivot_df.columns and 2026 in pivot_df.columns:
        # Calculate % change
        pivot_df["Wachstum_%"] = ((pivot_df[2026] - pivot_df[2023]) / pivot_df[2023].abs()) * 100
        
        # Filter out inf / small base effects
        valid_growth = pivot_df[(pivot_df[2023].abs() > 50000) & pivot_df["Wachstum_%"].notna() & ~np.isinf(pivot_df["Wachstum_%"])]
        top_growth = valid_growth.sort_values("Wachstum_%", ascending=False).head(15)
        
        top_growth["Pfad"] = top_growth["Amt"].str.slice(0, 15) + " / " + top_growth["Sub_Kategorie"].str.slice(0, 30)
        
        # Create Bar Chart
        fig_growth = px.bar(
            top_growth, 
            x="Wachstum_%", 
            y="Pfad", 
            orientation="h",
            color="Wachstum_%",
            color_continuous_scale="Reds",
            title="Top 15 Kostentreiber (2023 -> 2026) in %"
        )
        fig_growth.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_growth, use_container_width=True)
    else:
        st.warning("Für die Jahre 2023 und 2026 liegen nicht ausreichend Datenpunkte für den Vergleich vor.")

    st.markdown("---")
    st.subheader("Zeitliche Entwicklung (Zeitreihe) eines spezifischen Einzelpostens")
    st.write("Wähle hier genau den Drill-Down-Pfad aus, den du analysieren möchtest. Das Diagramm zeigt dir dann die Entwicklung über die Jahre.")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        ts_amt = st.selectbox("1. Amt auswählen", sorted(aufw_df["Amt"].unique().tolist()), key="ts_amt")
    with c2:
        cat_opts = sorted(aufw_df[aufw_df["Amt"] == ts_amt]["Kategorie"].unique().tolist())
        ts_cat = st.selectbox("2. Kategorie", cat_opts, key="ts_cat")
    with c3:
        sub_opts = sorted(aufw_df[(aufw_df["Amt"] == ts_amt) & (aufw_df["Kategorie"] == ts_cat)]["Sub_Kategorie"].unique().tolist())
        ts_sub = st.selectbox("3. Einzelposten", sub_opts, key="ts_sub")
        
    ts_data = aufw_df[(aufw_df["Amt"] == ts_amt) & (aufw_df["Kategorie"] == ts_cat) & (aufw_df["Sub_Kategorie"] == ts_sub)]
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
            title=f"Ausgaben-Entwicklung: {ts_sub}"
        )
        
        # Format text on points
        fig_ts.update_traces(texttemplate='%{text:+.1f}%', textposition='top center')
        # Ensure x-axis shows only integer years
        fig_ts.update_layout(xaxis=dict(tickmode='linear', dtick=1))
        
        st.plotly_chart(fig_ts, use_container_width=True)
"""

new_content = header + "\nimport numpy as np\n" + tab_creation_code + indented_rest + "\n" + tab2_code

with open("app.py", "w", encoding="utf-8") as f:
    f.write(new_content)
print("app.py rewritten successfully!")
