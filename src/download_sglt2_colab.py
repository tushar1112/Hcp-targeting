# Run this in Google Colab, not locally.
# data.cms.gov blocked direct access from India, so the download runs on Colab's servers.
# It downloads the CMS Part D files for 2021-2024, keeps only SGLT2 rows
# (generic name contains "gliflozin") and writes two Parquet files.


import os, glob, requests, subprocess, sys
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "duckdb"], check=True)
import duckdb

HEADERS = {"User-Agent": "Mozilla/5.0"}
RAW = "/content/cms_raw"
OUT = "/content/out"
os.makedirs(RAW, exist_ok=True)
os.makedirs(OUT, exist_ok=True)

# clear any leftovers from the crashed run (they might be partial downloads)
for f in glob.glob(f"{RAW}/*"):
    os.remove(f)

DRUG_URLS = {
    2021: "https://data.cms.gov/sites/default/files/2024-05/43359391-e7fa-40b9-9bd4-5dc295e18712/MUP_DPR_RY24_P04_V10_DY21_NPIBN.csv",
    2022: "https://data.cms.gov/sites/default/files/2024-05/18f82097-61a6-4889-9941-9a0b6ad7523c/MUP_DPR_RY24_P04_V10_DY22_NPIBN.csv",
    2023: "https://data.cms.gov/sites/default/files/2025-04/0d5915ce-002c-4d87-bde8-24ffb08bb6cc/MUP_DPR_RY25_P04_V10_DY23_NPIBN.csv",
    2024: "https://data.cms.gov/sites/default/files/2026-05/0ae165f4-eb44-495d-8cac-67f4571b6b83/MUP_DPR_RY26_P04_V10_DY24_NPIBN.csv",
}
PROV_URLS = {
    2021: "https://data.cms.gov/sites/default/files/2026-08/a8cb773f-4a79-42de-b7ad-83da254416bf/mup_dpr_ry23_p04_v20_dy21_npi.csv",
    2022: "https://data.cms.gov/sites/default/files/2026-08/0cdbfc0d-257d-4eb0-bcc8-71e5462ec320/mup_dpr_ry24_p04_v20_dy22_npi.csv",
    2023: "https://data.cms.gov/sites/default/files/2026-08/7f74c86e-ca81-4255-8951-3275c4361241/mup_dpr_ry25_p04_v20_dy23_npi.csv",
    2024: "https://data.cms.gov/sites/default/files/2026-08/373e45e5-33ec-452c-9302-a4bdbc203459/mup_dpr_ry26_p04_v20_dy24_npi.csv",
}

def download(url, path):
    tmp = path + ".part"
    with requests.get(url, headers=HEADERS, stream=True, timeout=120) as r:
        r.raise_for_status()
        with open(tmp, "wb") as f:
            for block in r.iter_content(chunk_size=1024 * 1024):
                f.write(block)
    os.rename(tmp, path)

con = duckdb.connect()
con.execute("SET memory_limit='4GB'")

# ---------- Part 1: drug-level files -> SGLT2 rows, one parquet per year ----------
for year, url in DRUG_URLS.items():
    out = f"{OUT}/drug_sglt2_{year}.parquet"
    if os.path.exists(out):
        print(f"[{year}] drug-level already done, skipping")
        continue
    path = f"{RAW}/drug_{year}.csv"
    print(f"[{year}] downloading drug-level file ...")
    download(url, path)
    con.execute(f"""
        COPY (
            SELECT *, {year} AS Year
            FROM read_csv('{path}', header=true, all_varchar=true)
            WHERE lower(Gnrc_Name) LIKE '%gliflozin%'
        ) TO '{out}' (FORMAT PARQUET)
    """)
    os.remove(path)
    n = con.execute(f"SELECT count(*) FROM read_parquet('{out}')").fetchone()[0]
    print(f"[{year}] SGLT2 rows kept: {n:,}")

# ---------- Part 2: by-Provider files -> only prescribers seen in the SGLT2 data ----------
con.execute(f"""
    CREATE TEMP TABLE sglt2_npis AS
    SELECT DISTINCT Prscrbr_NPI FROM read_parquet('{OUT}/drug_sglt2_*.parquet')
""")
print("Unique SGLT2 prescribers:", f"{con.execute('SELECT count(*) FROM sglt2_npis').fetchone()[0]:,}")

for year, url in PROV_URLS.items():
    out = f"{OUT}/prov_sglt2_{year}.parquet"
    if os.path.exists(out):
        print(f"[{year}] by-provider already done, skipping")
        continue
    path = f"{RAW}/prov_{year}.csv"
    print(f"[{year}] downloading by-provider file ...")
    download(url, path)
    con.execute(f"""
        COPY (
            SELECT p.*, {year} AS Year
            FROM read_csv('{path}', header=true, all_varchar=true) p
            WHERE p.Prscrbr_NPI IN (SELECT Prscrbr_NPI FROM sglt2_npis)
        ) TO '{out}' (FORMAT PARQUET)
    """)
    os.remove(path)
    n = con.execute(f"SELECT count(*) FROM read_parquet('{out}')").fetchone()[0]
    print(f"[{year}] by-provider rows kept: {n:,}")

# ---------- Combine into two final files ----------
drug_file = f"{OUT}/sglt2_by_provider_and_drug_2021_2024.parquet"
prov_file = f"{OUT}/partd_by_provider_sglt2_prescribers_2021_2024.parquet"
con.execute(f"COPY (SELECT * FROM read_parquet('{OUT}/drug_sglt2_*.parquet', union_by_name=true)) TO '{drug_file}' (FORMAT PARQUET)")
con.execute(f"COPY (SELECT * FROM read_parquet('{OUT}/prov_sglt2_*.parquet', union_by_name=true)) TO '{prov_file}' (FORMAT PARQUET)")

# ---------- Summary to review ----------
print("\nRows and prescribers per year (drug-level):")
print(con.execute(f"""
    SELECT Year, count(*) AS rows, count(DISTINCT Prscrbr_NPI) AS prescribers
    FROM read_parquet('{drug_file}') GROUP BY Year ORDER BY Year
""").df().to_string(index=False))
print("\nGeneric / brand combinations found:")
print(con.execute(f"""
    SELECT Gnrc_Name, Brnd_Name, count(*) AS rows
    FROM read_parquet('{drug_file}') GROUP BY 1, 2 ORDER BY rows DESC
""").df().to_string(index=False))
print("\nFinal file sizes (MB):", round(os.path.getsize(drug_file)/1e6, 1), round(os.path.getsize(prov_file)/1e6, 1))