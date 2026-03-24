import pandas as pd

print("script started")
def load_fdic() -> pd.DataFrame:
    """Load raw FDIC data from CSV."""
    df = pd.read_csv("data/raw/fdic_raw.csv", parse_dates=["date"])
    print(f"  ✓ Loaded {len(df)} rows from fdic_raw.csv")
    return df


def transform_fdic(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and enrich FDIC data with computed columns."""
    print("Transforming FDIC data...")

    # Sort by bank and date
    df = df.sort_values(["bank_id", "date"]).reset_index(drop=True)

    # Drop rows missing critical fields
    df = df.dropna(subset=["total_assets", "date"])

    # Month-over-month change in charge-off rate per bank
    df["charge_off_rate_mom"] = (
        df.groupby("bank_id")["charge_off_rate"]
        .pct_change()
        .round(4)
    )

    # Month-over-month change in net interest margin per bank
    df["nim_mom"] = (
        df.groupby("bank_id")["net_interest_margin"]
        .pct_change()
        .round(4)
    )

    # Bank size category based on total assets
    df["bank_size"] = pd.cut(
        df["total_assets"],
        bins=[0, 100_000, 1_000_000, 10_000_000, float("inf")],
        labels=["small", "mid", "large", "mega"]
    )

    # State-level aggregations (useful for choropleth map)
    state_avg = (
        df.groupby(["state", "date"])[["charge_off_rate", "net_interest_margin"]]
        .mean()
        .round(4)
        .reset_index()
        .rename(columns={
            "charge_off_rate": "state_avg_charge_off",
            "net_interest_margin": "state_avg_nim"
        })
    )
    df = df.merge(state_avg, on=["state", "date"], how="left")

    print(f"  ✓ Transformed — {len(df)} rows, {len(df.columns)} columns")
    return df


def run():
    df = load_fdic()
    df = transform_fdic(df)

    output_path = "data/cleaned/fdic_cleaned.csv"
    df.to_csv(output_path, index=False)
    print(f"\n✓ Saved to {output_path}")
    print(df.head())


if __name__ == "__main__":
    run()