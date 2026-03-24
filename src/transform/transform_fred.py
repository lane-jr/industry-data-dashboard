import pandas as pd

def load_fred() -> pd.DataFrame:
    """Load raw FRED data from CSV."""
    df = pd.read_csv("data/raw/fred_raw.csv", parse_dates=["date"])
    print(f"  ✓ Loaded {len(df)} rows from fred_raw.csv")
    return df


def transform_fred(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and enrich FRED data with computed columns."""
    print("Transforming FRED data...")

    # Sort by date
    df = df.sort_values("date").reset_index(drop=True)

    # Forward fill nulls — quarterly delinquency rate gets filled monthly
    df["loan_delinquency_rate"] = df["loan_delinquency_rate"].ffill()

    # Month-over-month % change for each indicator
    df["fed_funds_rate_mom"] = df["federal_funds_rate"].pct_change().round(4)
    df["unemployment_mom"] = df["unemployment_rate"].pct_change().round(4)
    df["delinquency_mom"] = df["loan_delinquency_rate"].pct_change().round(4)

    # Rolling 3-month averages (smooths out noise)
    df["fed_funds_3mo_avg"] = (
        df["federal_funds_rate"].rolling(window=3).mean().round(4)
    )
    df["delinquency_3mo_avg"] = (
        df["loan_delinquency_rate"].rolling(window=3).mean().round(4)
    )

    # Flag periods of rising rates (useful for dashboard filters)
    df["rising_rate_env"] = (
        df["federal_funds_rate"] > df["federal_funds_rate"].shift(3)
    ).astype(int)

    print(f"  ✓ Transformed — {len(df)} rows, {len(df.columns)} columns")
    return df


def run():
    df = load_fred()
    df = transform_fred(df)

    output_path = "data/cleaned/fred_cleaned.csv"
    df.to_csv(output_path, index=False)
    print(f"\n✓ Saved to {output_path}")
    print(df.head())


if __name__ == "__main__":
    run()