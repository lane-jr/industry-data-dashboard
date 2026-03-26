import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Fintech Credit Risk Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("Fintech Credit Risk Dashboard")
#st.caption("Loan delinquency, charge-off trends, and bank health across the US (2010–present)")

# ── Data loading ───────────────────────────────────────────────────────────────
@st.cache_data
def load_bank_metrics() -> pd.DataFrame:
    conn = sqlite3.connect("data/fintech.db")
    df = pd.read_sql("""
        SELECT date, bank_id, state, total_assets, gross_loans,
               charge_off_rate, net_interest_margin, bank_size,
               state_avg_charge_off, state_avg_nim,
               credit_stress_score, loan_delinquency_rate,
               federal_funds_rate, unemployment_rate
        FROM bank_metrics
    """, conn, parse_dates=["date"])
    conn.close()
    return df


@st.cache_data
def load_macro() -> pd.DataFrame:
    conn = sqlite3.connect("data/fintech.db")
    df = pd.read_sql("""
        SELECT date, federal_funds_rate, unemployment_rate,
               loan_delinquency_rate, fed_funds_3mo_avg,
               delinquency_3mo_avg, rising_rate_env
        FROM macro_indicators
    """, conn, parse_dates=["date"])
    conn.close()
    return df


# Load data
bank_df = load_bank_metrics()
macro_df = load_macro()

# ── Sidebar filters ────────────────────────────────────────────────────────────
st.sidebar.header("Filters")

# Date range filter
min_date = bank_df["date"].min().to_pydatetime()
max_date = bank_df["date"].max().to_pydatetime()

years = sorted(bank_df["date"].dt.year.unique().tolist())

col_from, col_to = st.sidebar.columns(2)
with col_from:
    start_year = st.selectbox("From", years, index=0)
with col_to:
    end_year = st.selectbox("To", years, index=len(years)-1)

import datetime
date_range = (
    datetime.datetime(start_year, 1, 1),
    datetime.datetime(end_year, 12, 31)
)

# State filter
states = sorted(bank_df["state"].dropna().unique().tolist())
selected_states = st.sidebar.multiselect(
    "State",
    options=states,
    default=[],
    placeholder="All states"
)

# Bank size filter
sizes = ["small", "mid", "large", "mega"]
selected_sizes = st.sidebar.multiselect(
    "Bank size",
    options=sizes,
    default=[],
    placeholder="All sizes"
)

# ── Apply filters ──────────────────────────────────────────────────────────────
filtered_df = bank_df[
    (bank_df["date"] >= date_range[0]) &
    (bank_df["date"] <= date_range[1])
]

if selected_states:
    filtered_df = filtered_df[filtered_df["state"].isin(selected_states)]

if selected_sizes:
    filtered_df = filtered_df[filtered_df["bank_size"].isin(selected_sizes)]

filtered_macro = macro_df[
    (macro_df["date"] >= date_range[0]) &
    (macro_df["date"] <= date_range[1])
]

# ── Export button ──────────────────────────────────────────────────────────────
st.sidebar.divider()
st.sidebar.download_button(
    label="Export filtered data (CSV)",
    data=filtered_df.to_csv(index=False),
    file_name="filtered_credit_data.csv",
    mime="text/csv"
)

st.sidebar.caption(f"{len(filtered_df):,} records loaded")

# ── KPI Cards ──────────────────────────────────────────────────────────────────
st.divider()

avg_charge_off = filtered_df["charge_off_rate"].mean()
avg_delinquency = filtered_df["loan_delinquency_rate"].mean()
avg_nim = filtered_df["net_interest_margin"].mean()
avg_stress = filtered_df["credit_stress_score"].mean()

# Calculate deltas vs prior period
mid_date = date_range[0] + (date_range[1] - date_range[0]) / 2
prior_df = filtered_df[filtered_df["date"] <= mid_date]
recent_df = filtered_df[filtered_df["date"] > mid_date]

col1, col2, col3, col4 = st.columns(4)

with col1:
    delta = recent_df["charge_off_rate"].mean() - prior_df["charge_off_rate"].mean()
    st.metric(
        label="Avg charge-off rate",
        value=f"{avg_charge_off:.4f}",
        delta=f"{delta:.4f}",
        delta_color="inverse"  # higher charge-off = bad = red
    )

with col2:
    delta = recent_df["loan_delinquency_rate"].mean() - prior_df["loan_delinquency_rate"].mean()
    st.metric(
        label="Avg delinquency rate",
        value=f"{avg_delinquency:.2f}%",
        delta=f"{delta:.2f}%",
        delta_color="inverse"
    )

with col3:
    delta = recent_df["net_interest_margin"].mean() - prior_df["net_interest_margin"].mean()
    st.metric(
        label="Avg net interest margin",
        value=f"{avg_nim:.4f}",
        delta=f"{delta:.4f}"
    )

with col4:
    delta = recent_df["credit_stress_score"].mean() - prior_df["credit_stress_score"].mean()
    st.metric(
        label="Credit stress score",
        value=f"{avg_stress:.3f}",
        delta=f"{delta:.3f}",
        delta_color="inverse"
    )


    # ── Charts Row 1 ───────────────────────────────────────────────────────────────
st.divider()
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.subheader("Delinquency vs fed funds rate")

    macro_grouped = filtered_macro.groupby("date").agg({
        "loan_delinquency_rate": "mean",
        "federal_funds_rate": "mean"
    }).reset_index()

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=macro_grouped["date"],
        y=macro_grouped["loan_delinquency_rate"],
        name="Delinquency rate",
        line=dict(color="#185FA5", width=2)
    ))

    fig.add_trace(go.Scatter(
        x=macro_grouped["date"],
        y=macro_grouped["federal_funds_rate"],
        name="Fed funds rate",
        line=dict(color="#D85A30", width=2)
    ))

    fig.update_layout(
        height=340,
        margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        xaxis_title=None,
        yaxis_title="Rate (%)",
        hovermode="x unified"
    )

    st.plotly_chart(fig, use_container_width=True, key="timeseries")
    st.caption("Insight: delinquency rates peaked post-2008 crisis and declined as the fed funds rate approached zero.")

with chart_col2:
    st.subheader("Charge-off rate by state")

    state_abbrev = {
        "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR",
        "California": "CA", "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE",
        "Florida": "FL", "Georgia": "GA", "Hawaii": "HI", "Idaho": "ID",
        "Illinois": "IL", "Indiana": "IN", "Iowa": "IA", "Kansas": "KS",
        "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME", "Maryland": "MD",
        "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN", "Mississippi": "MS",
        "Missouri": "MO", "Montana": "MT", "Nebraska": "NE", "Nevada": "NV",
        "New Hampshire": "NH", "New Jersey": "NJ", "New Mexico": "NM", "New York": "NY",
        "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK",
        "Oregon": "OR", "Pennsylvania": "PA", "Rhode Island": "RI", "South Carolina": "SC",
        "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX", "Utah": "UT",
        "Vermont": "VT", "Virginia": "VA", "Washington": "WA", "West Virginia": "WV",
        "Wisconsin": "WI", "Wyoming": "WY", "District of Columbia": "DC"
    }
    state_df = filtered_df.groupby("state")["charge_off_rate"].mean().reset_index()
    state_df.columns = ["state", "avg_charge_off_rate"]
    state_df["state_code"] = state_df["state"].str.title().map(state_abbrev)
    state_df = state_df.dropna(subset=["state_code"])
    
    fig2 = px.choropleth(
        state_df,
        locations="state_code",
        locationmode="USA-states",
        color="avg_charge_off_rate",
        scope="usa",
        color_continuous_scale="Blues",
        labels={"avg_charge_off_rate": "Avg charge-off rate"},
        hover_name="state"
    )

    fig2.update_layout(
        height=340,
        margin=dict(l=0, r=0, t=10, b=0),
        coloraxis_colorbar=dict(title="Rate")
    )

    st.caption("Insight: southern and midwestern states show higher average charge-off rates across the period.")

    fig2.update_layout(
        height=340,
        margin=dict(l=0, r=0, t=10, b=0),
        coloraxis_colorbar=dict(title="Rate")
    )

    st.plotly_chart(fig2, use_container_width=True, key="choropleth")
    st.caption("Insight: southern and midwestern states show higher average charge-off rates across the period.")



# ── Charts Row 2 ───────────────────────────────────────────────────────────────
st.divider()
chart_col3, chart_col4 = st.columns(2)

with chart_col3:
    st.subheader("Avg charge-off rate by bank size")

    size_order = ["small", "mid", "large", "mega"]
    size_df = (
        filtered_df.groupby("bank_size")["charge_off_rate"]
        .mean()
        .reset_index()
    )
    size_df.columns = ["bank_size", "avg_charge_off_rate"]
    size_df["bank_size"] = pd.Categorical(
        size_df["bank_size"], categories=size_order, ordered=True
    )
    size_df = size_df.sort_values("bank_size")

    fig3 = px.bar(
        size_df,
        x="bank_size",
        y="avg_charge_off_rate",
        color="avg_charge_off_rate",
        color_continuous_scale="Blues",
        labels={
            "bank_size": "Bank size",
            "avg_charge_off_rate": "Avg charge-off rate"
        }
    )

    fig3.update_layout(
        height=340,
        margin=dict(l=0, r=0, t=10, b=0),
        coloraxis_showscale=False,
        xaxis_title=None
    )

    st.plotly_chart(fig3, use_container_width=True, key="barchart")
    st.caption("Insight: smaller banks tend to have higher charge-off rates, reflecting less diversified loan portfolios.")

with chart_col4:
    st.subheader("NIM vs credit stress score")

    scatter_df = filtered_df[
        filtered_df["net_interest_margin"].notna() &
        filtered_df["credit_stress_score"].notna()
    ].sample(min(5000, len(filtered_df)), random_state=42)

    fig4 = px.scatter(
        scatter_df,
        x="credit_stress_score",
        y="net_interest_margin",
        color="bank_size",
        opacity=0.4,
        labels={
            "credit_stress_score": "Credit stress score",
            "net_interest_margin": "Net interest margin",
            "bank_size": "Bank size"
        },
        category_orders={"bank_size": size_order}
    )

    fig4.update_layout(
        height=340,
        margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=1.02)
    )

    st.plotly_chart(fig4, use_container_width=True, key="scatter")
    st.caption("Insight: banks with higher credit stress scores tend to show compressed net interest margins.")

# ── Insight callout ─────────────────────────────────────────────────────────────
st.divider()
st.info(
    "**Key insight:** Charge-off rates peaked in 2011 post-crisis and declined steadily "
    "as the fed funds rate approached zero. Smaller banks consistently show higher "
    "credit stress scores, while rising rate environments compress net interest margins "
    "across all bank sizes."
)

