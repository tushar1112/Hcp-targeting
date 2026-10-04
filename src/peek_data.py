import pandas as pd

files = {
    "drug-level": "data/raw/sglt2_by_provider_and_drug_2021_2024.parquet",
    "by-provider": "data/raw/partd_by_provider_sglt2_prescribers_2021_2024.parquet",
}

for name, path in files.items():
    df = pd.read_parquet(path)
    print("=" * 70)
    print(name, "| rows:", f"{len(df):,}", "| columns:", df.shape[1])
    print(list(df.columns))
    print(df.head(3).T)
    print("Rows per year:")
    print(df["Year"].value_counts().sort_index())

drug = pd.read_parquet(files["drug-level"])
print("=" * 70)
print("Generic / brand combinations:")
print(drug.groupby(["Gnrc_Name", "Brnd_Name"]).size().sort_values(ascending=False).to_string())