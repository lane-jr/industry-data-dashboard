# Fintech Credit Risk Dashboard

## Live Demo
[View the live dashboard](https://industry-data-dashboard-folnd6rhybvvdtxoexnfai.streamlit.app/
)

[![CI](https://github.com/lane-jr/industry-data-dashboard/actions/workflows/ci.yml/badge.svg)](https://github.com/lane-jr/industry-data-dashboard/actions/workflows/ci.yml)

An interactive data dashboard tracking credit risk indicators across US banks and macroeconomic conditions. Built as a portfolio project targeting fintech and lending companies.

## Problem Statement
Credit risk is the core challenge of any lending business. This dashboard surfaces key indicators — loan delinquency rates, charge-off trends, net interest margins, and macroeconomic context — to help identify regional stress patterns and rate sensitivity across thousands of US banks from 2010 to present.

## Data Sources
- [FDIC BankFind API](https://banks.data.fdic.gov/docs/) — bank-level financial data for ~4,500 US institutions
- [FRED API](https://fred.stlouisfed.org/docs/api/fred/) — Federal Reserve macroeconomic indicators (delinquency rates, federal funds rate, unemployment)

## Key Performance Indicators
- Loan delinquency rate over time
- Charge-off rate by bank and region
- Net interest margin vs federal funds rate
- Regional bank health score

## Tech Stack
- **Python 3.13** — data pipeline and dashboard
- **Pandas** — data cleaning and transformation
- **SQLite** — local data storage
- **Streamlit + Plotly** — interactive dashboard
- **Pandera + Pytest** — data validation and testing
- **Docker** — reproducible environment
- **GitHub Actions** — CI/CD pipeline

## Project Structure
```
fintech-credit-dashboard/
├── data/
│   ├── raw/          # original source data, never modified
│   └── cleaned/      # transformed data ready for SQL load
├── src/
│   ├── ingest/       # data ingestion scripts
│   ├── transform/    # cleaning and KPI computation
│   └── dashboard/    # Streamlit app
├── tests/            # schema validation tests
├── Dockerfile
└── requirements.txt
```

## Setup
1. Clone the repo
2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows
```
3. Install dependencies:
```bash
pip install -r requirements.txt
```
4. Create a `.env` file in the project root:
```
FRED_API_KEY=your_key_here
```
5. Run the ingestion pipeline:
```bash
python src/ingest/fred.py
python src/ingest/fdic.py
```
6. Run tests:
```bash
pytest tests/ -v
```
