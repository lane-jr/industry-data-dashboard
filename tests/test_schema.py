import pandas as pd
import pandera.pandas as pa
from pandera.pandas import Column, DataFrameSchema, Check
import pytest


# Schema for FRED data
fred_schema = DataFrameSchema({
    "date": Column(pa.DateTime),
    "loan_delinquency_rate": Column(pa.Float, nullable=True),
    "federal_funds_rate": Column(pa.Float, nullable=True),
    "unemployment_rate": Column(pa.Float, Check.greater_than(0), nullable=True),
})

# Schema for FDIC data
fdic_schema = DataFrameSchema({
    "date": Column(pa.DateTime),
    "bank_id": Column(pa.Int),
    "state": Column(pa.String, nullable=True),
    "total_assets": Column(pa.Int, Check.greater_than(0), nullable=True),
    "gross_loans": Column(pa.Int, nullable=True),
    "charge_off_rate": Column(pa.Float, nullable=True),
    "net_interest_margin": Column(pa.Float, nullable=True),
})


def test_fred_schema():
    df = pd.read_csv("data/raw/fred_raw.csv", parse_dates=["date"])
    fred_schema.validate(df)
    assert len(df) > 0, "FRED data should not be empty"
    print(f"  ✓ FRED schema valid — {len(df)} rows")


def test_fdic_schema():
    df = pd.read_csv("data/raw/fdic_raw.csv", parse_dates=["date"])
    fdic_schema.validate(df)
    assert len(df) > 0, "FDIC data should not be empty"
    print(f"  ✓ FDIC schema valid — {len(df)} rows")


def test_fred_date_range():
    df = pd.read_csv("data/raw/fred_raw.csv", parse_dates=["date"])
    assert df["date"].min().year >= 2010, "Data should start from 2010"
    assert df["date"].max().year >= 2020, "Data should include recent years"


def test_fdic_date_range():
    df = pd.read_csv("data/raw/fdic_raw.csv", parse_dates=["date"])
    assert df["date"].min().year >= 2010, "Data should start from 2010"
    assert df["date"].max().year >= 2020, "Data should include recent years"