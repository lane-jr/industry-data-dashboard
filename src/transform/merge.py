import pandas as pd


def load_cleaned() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load both cleaned datasets."""
    fred = pd.read_csv("data/cleaned/fred_cleaned.csv", parse_dates=["date"])
    fdic = pd.read_csv("data/cleaned/fdic_cleaned.csv", parse_dates=["date"])
    print(f"  ✓ Loaded FRED: {len(fred)} rows")
    print(f"  ✓ Loaded FDIC: {len(fdic)} rows")
    return fred, fdic


def merge_datasets(fred: pd.DataFrame, fdic: pd.DataFrame) -> pd.DataFrame:
    """Merge FDIC bank data with FRED macro indicators on date."""
    print("Merging datasets...")

    # Normalize FRED dates to end of month to match FDIC quarterly dates
    fred["date"] = fred["date"] + pd.offsets.MonthEnd(0)

    # Merge FDIC bank records with FRED macro indicators
    merged = pd.merge(fdic, fred, on="date", how="left")

    # Add a credit stress score — composite of delinquency and charge-off rate
    # Higher score = more stress
    merged["credit_stress_score"] = (
        (merged["charge_off_rate"].fillna(0) * 0.5) +
        (merged["loan_delinquency_rate"].fillna(0) * 0.5)
    ).round(4)

    print(f"  ✓ Merged — {len(merged)} rows, {len(merged.columns)} columns")
    return merged


def run():
    fred, fdic = load_cleaned()
    merged = merge_datasets(fred, fdic)

    output_path = "data/cleaned/merged.csv"
    merged.to_csv(output_path, index=False)
    print(f"\n✓ Saved to {output_path}")
    print(merged[["date", "bank_id", "state", "charge_off_rate",
                  "loan_delinquency_rate", "credit_stress_score"]].head())


if __name__ == "__main__":
    run()