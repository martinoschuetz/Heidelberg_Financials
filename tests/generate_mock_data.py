import pandas as pd
import numpy as np

# Generate a plausible mock dataset for a municipal budget
years = [2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026]
dezernate = [
    "D1: Bürgermeisteramt",
    "D2: Finanzen & Sicherheit",
    "D3: Kultur & Bürgerservice",
    "D4: Soziales, Bildung & Familie",
    "D5: Bauen & Verkehr",
    "D6: Umwelt & Klimaschutz"
]

aemter = {
    "D1: Bürgermeisteramt": ["Personal", "Organisation", "Presse"],
    "D2: Finanzen & Sicherheit": ["Kämmerei", "Feuerwehr", "Bürgeramt"],
    "D3: Kultur & Bürgerservice": ["Kulturamt", "Theater", "Musikschule"],
    "D4: Soziales, Bildung & Familie": ["Sozialamt", "Jugendamt", "Schulverwaltungsamt"],
    "D5: Bauen & Verkehr": ["Stadtplanungsamt", "Tiefbauamt", "Gebäudemanagement"],
    "D6: Umwelt & Klimaschutz": ["Umweltamt", "Grünflächenamt", "Abfallwirtschaft"]
}

typen = ["Erträge", "Aufwendungen"]

data = []
for y in years:
    for d in dezernate:
        for a in aemter[d]:
            for t in typen:
                # Random amount between 1M and 100M
                base = np.random.uniform(1e6, 100e6)
                if t == "Erträge" and "Kämmerei" in a:
                    base *= 10 # Taxes
                elif t == "Aufwendungen" and "Sozialamt" in a:
                    base *= 5
                
                # Inflation / Trend
                base *= (1 + (y - 2017) * 0.03)
                
                data.append({
                    "Jahr": y,
                    "Dezernat": d,
                    "Amt": a,
                    "Typ": t,
                    "Betrag": round(base, 2)
                })

df = pd.DataFrame(data)
df.to_csv("haushalt_modell.csv", index=False)
print("Mock-Datenmodell haushalt_modell.csv erstellt.")
