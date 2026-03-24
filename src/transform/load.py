import sqlite3
import pandas as pd
import os


DB_PATH = "data/fintech.db"


def create_connection() -> sqlite3.Connection:
    """Create a connection to the SQLite database."""
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    print(f"  ✓ Connected to {DB_PATH}")
    return conn


def create_schema(conn: sqlite3.Connection):
    """Create tables if they don't exist."""
    print("Creating schema...")

    conn.executescript("""
        CREATE TABLE IF NOT EXISTS macro_indicators (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            date        TEXT NOT NULL,
            federal_funds_rate      REAL,
            unemployment_rate       REAL,
            loan_delinquency_rate   REAL,
            fed_funds_3mo_avg       REAL,
            delinquency_3mo_avg     REAL,
            rising_rate_env         INTEGER
        );

        CREATE TABLE IF NOT EXISTS bank_metrics (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            date                TEXT NOT NULL,
            bank_id             INTEGER,
            state               TEXT,
            total_assets        INTEGER,
            gross_loans         INTEGER,
            charge_offs         INTEGER,
            charge_off_rate     REAL,
            net_interest_margin REAL,
            bank_size           TEXT,
            state_avg_charge_off REAL,
            state_avg_nim        REAL,
            credit_stress_score  REAL,
            loan_delinquency_rate REAL,
            federal_funds_rate    REAL,
            unemployment_rate     REAL
        );

        CREATE INDEX IF NOT EXISTS idx_bank_metrics_date
            ON bank_metrics(date);
        CREATE INDEX IF NOT EXISTS idx_bank_metrics_state
            ON bank_metrics(state);
        CREATE INDEX IF NOT EXISTS idx_macro_date
            ON macro_indicators(date);
    """)

    print("  ✓ Schema created")


def load_macro(conn: sqlite3.Connection):
    """Load FRED cleaned data into macro_indicators table."""
    print("Loading FRED data into macro_indicators...")

    df = pd.read_csv("data/cleaned/fred_cleaned.csv", parse_dates=["date"])
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")

    # Select only columns that match the schema
    cols = [
        "date", "federal_funds_rate", "unemployment_rate",
        "loan_delinquency_rate", "fed_funds_3mo_avg",
        "delinquency_3mo_avg", "rising_rate_env"
    ]
    df[cols].to_sql(
        "macro_indicators",
        conn,
        if_exists="replace",
        index=False
    )
    print(f"  ✓ Loaded {len(df)} rows into macro_indicators")


def load_bank_metrics(conn: sqlite3.Connection):
    """Load merged data into bank_metrics table."""
    print("Loading merged data into bank_metrics...")

    df = pd.read_csv("data/cleaned/merged.csv", parse_dates=["date"])
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")

    # Select only columns that match the schema
    cols = [
        "date", "bank_id", "state", "total_assets", "gross_loans",
        "charge_offs", "charge_off_rate", "net_interest_margin",
        "bank_size", "state_avg_charge_off", "state_avg_nim",
        "credit_stress_score", "loan_delinquency_rate",
        "federal_funds_rate", "unemployment_rate"
    ]

    # Only keep columns that exist in the dataframe
    cols = [c for c in cols if c in df.columns]

    df[cols].to_sql(
        "bank_metrics",
        conn,
        if_exists="replace",
        index=False,
        chunksize=10000  # load in chunks for large dataset
    )
    print(f"  ✓ Loaded {len(df)} rows into bank_metrics")


def verify(conn: sqlite3.Connection):
    """Quick sanity check on loaded data."""
    print("\nVerifying loaded data...")

    for table in ["macro_indicators", "bank_metrics"]:
        cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"  ✓ {table}: {count} rows")

    # Sample query — avg charge off rate by year
    query = """
        SELECT strftime('%Y', date) as year,
               ROUND(AVG(charge_off_rate), 4) as avg_charge_off
        FROM bank_metrics
        GROUP BY year
        ORDER BY year
        LIMIT 5
    """
    print("\nSample query — avg charge off rate by year:")
    df = pd.read_sql(query, conn)
    print(df.to_string(index=False))


def run():
    conn = create_connection()
    create_schema(conn)
    load_macro(conn)
    load_bank_metrics(conn)
    verify(conn)
    conn.close()
    print(f"\n✓ Database ready at {DB_PATH}")


if __name__ == "__main__":
    run()