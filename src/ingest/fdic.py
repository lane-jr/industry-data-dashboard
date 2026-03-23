import requests
import pandas as pd

BASE_URL = "https://banks.data.fdic.gov/api/financials"

FIELDS = [
    "REPDTE", "CERT", "INTINC", "EINTEXP",
    "LNLSNET", "LNLSDEPR", "LNLSGR", "ASSET", "DEP", "STNAME"
]


def fetch_fdic_data(limit: int = 10000) -> pd.DataFrame:
    print("Fetching FDIC bank financial data...")

    params = {
        "filters":    "REPDTE:[20100101 TO 99991231]",
        "fields":     ",".join(FIELDS),
        "limit":      limit,
        "offset":     0,
        "sort_by":    "REPDTE",
        "sort_order": "ASC",
        "output":     "json",
    }

    response = requests.get(BASE_URL, params=params)
    response.raise_for_status()

    data = response.json()
    records = [item["data"] for item in data.get("data", [])]

    if not records:
        raise ValueError("No data returned from FDIC API")

    df = pd.DataFrame(records)
    print("Columns from API:", df.columns.tolist())
    print(f"  ✓ {len(df)} records fetched")
    return df


def clean_fdic_data(df: pd.DataFrame) -> pd.DataFrame:
    print("Cleaning FDIC data...")
    print("Columns received:", df.columns.tolist())

    # Lowercase all column names
    df.columns = df.columns.str.lower()
    print("Columns after lowercase:", df.columns.tolist())

    df = df.rename(columns={
        "repdte":   "date",
        "cert":     "bank_id",
        "intinc":   "interest_income",
        "eintexp":  "interest_expense",
        "lnlsnet":  "net_loans",
        "lnlsdepr": "charge_offs",
        "lnlsgr":   "gross_loans",
        "asset":    "total_assets",
        "dep":      "total_deposits",
        "stname":   "state",
    })

    df["date"] = pd.to_datetime(df["date"], format="%Y%m%d")

    numeric_cols = [
        "interest_income", "interest_expense", "net_loans",
        "charge_offs", "gross_loans", "total_assets", "total_deposits"
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["net_interest_margin"] = (
        (df["interest_income"] - df["interest_expense"]) / df["total_assets"]
    ).round(4)

    df["charge_off_rate"] = (
        df["charge_offs"] / df["gross_loans"]
    ).round(4)

    print(f"  ✓ Cleaned and computed KPI columns")
    return df


def run():
    df = fetch_fdic_data()
    df = clean_fdic_data(df)

    output_path = "data/raw/fdic_raw.csv"
    df.to_csv(output_path, index=False)
    print(f"\n✓ Saved {len(df)} rows to {output_path}")
    print(df.head())


if __name__ == "__main__":
    run()