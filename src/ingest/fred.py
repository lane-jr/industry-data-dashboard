import os
import requests
import pandas as pd
from dotenv import load_dotenv

# Load API key from .env file
load_dotenv()
API_KEY = os.getenv("FRED_API_KEY")

# Base URL for FRED API
BASE_URL = "https://api.stlouisfed.org/fred/series/observations"

# The 3 FRED series we need for credit risk KPIs
SERIES = {
    "loan_delinquency_rate": "DRALACBS",   # Delinquency rate on all loans
    "federal_funds_rate":    "FEDFUNDS",    # Federal funds rate
    "unemployment_rate":     "UNRATE",      # Unemployment rate
}


def fetch_series(series_id: str, series_name: str) -> pd.DataFrame:
    """Fetch a single FRED series and return it as a DataFrame."""
    print(f"Fetching {series_name} ({series_id})...")

    params = {
        "series_id":         series_id,
        "api_key":           API_KEY,
        "file_type":         "json",
        "observation_start": "2010-01-01",  # 15 years of history
        "observation_end":   "9999-12-31",  # up to today
    }

    response = requests.get(BASE_URL, params=params)
    response.raise_for_status()  # raises an error if the request failed

    data = response.json()
    observations = data.get("observations", [])

    if not observations:
        raise ValueError(f"No data returned for series {series_id}")

    df = pd.DataFrame(observations)[["date", "value"]]
    df = df.rename(columns={"value": series_name})
    df["date"] = pd.to_datetime(df["date"])

    # FRED uses "." for missing values — replace with NaN
    df[series_name] = pd.to_numeric(df[series_name], errors="coerce")

    print(f"  ✓ {len(df)} observations fetched")
    return df


def run():
    """Fetch all series, merge into one DataFrame, and save to data/raw/."""
    if not API_KEY:
        raise EnvironmentError("FRED_API_KEY not found — check your .env file")

    # Fetch each series individually
    dataframes = []
    for series_name, series_id in SERIES.items():
        df = fetch_series(series_id, series_name)
        dataframes.append(df)

    # Merge all series on date using outer join to keep all dates
    merged = dataframes[0]
    for df in dataframes[1:]:
        merged = pd.merge(merged, df, on="date", how="outer")

    merged = merged.sort_values("date").reset_index(drop=True)

    # Save to data/raw/
    output_path = "data/raw/fred_raw.csv"
    merged.to_csv(output_path, index=False)
    print(f"\n✓ Saved {len(merged)} rows to {output_path}")
    print(merged.head())


if __name__ == "__main__":
    run()