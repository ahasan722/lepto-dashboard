
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO

# Load data
@st.cache_data
def load_data():
    return pd.read_csv("final_cleaned_lepto_bed_occupancy_corrected.csv", parse_dates=["Date"])

df = load_data()

# Sidebar - Filters
st.sidebar.title("Filters")
province_filter = st.sidebar.multiselect("Select Province", sorted(df["Province"].unique()), default=None)
city_filter = st.sidebar.multiselect("Select City/Mun", sorted(df["City/Mun"].unique()), default=None)
disease_filter = st.sidebar.selectbox("Disease Type", ["All", "Lepto", "Other"])
week_agg = st.sidebar.selectbox("Aggregation", ["ISO Week", "7-Day Moving Average"])

# Filter data
filtered_df = df.copy()
if province_filter:
    filtered_df = filtered_df[filtered_df["Province"].isin(province_filter)]
if city_filter:
    filtered_df = filtered_df[filtered_df["City/Mun"].isin(city_filter)]

# Date Aggregation
filtered_df["ISO_Week"] = filtered_df["Date"].dt.isocalendar().week
filtered_df["Year"] = filtered_df["Date"].dt.year
filtered_df["Week"] = filtered_df["Year"].astype(str) + "-W" + filtered_df["ISO_Week"].astype(str)

# Header
st.title("Leptospirosis Bed Occupancy Dashboard")

# Summary Panel
col1, col2 = st.columns(2)
with col1:
    total_icu = filtered_df["Total ICU beds occupied"].sum()
    st.metric("Total ICU Beds Occupied", total_icu)
with col2:
    total_mortality = filtered_df["% Died"].mean()
    st.metric("Average Mortality Rate (%)", f"{total_mortality:.2f}")

# Trends
st.subheader("ICU and Non-ICU Bed Occupancy Over Time")
if week_agg == "ISO Week":
    trends = filtered_df.groupby("Week")[["Total ICU beds occupied", "Total Non-ICU beds occupied"]].sum().reset_index()
    fig = px.line(trends, x="Week", y=["Total ICU beds occupied", "Total Non-ICU beds occupied"])
else:
    ma = filtered_df.set_index("Date").sort_index().rolling("7D").sum()[["Total ICU beds occupied", "Total Non-ICU beds occupied"]]
    ma.reset_index(inplace=True)
    fig = px.line(ma, x="Date", y=["Total ICU beds occupied", "Total Non-ICU beds occupied"])

fig.update_layout(xaxis_title="Time", yaxis_title="Beds Occupied", hovermode="x unified")
st.plotly_chart(fig, use_container_width=True)

# Deaths
st.subheader("Deaths Over Time")
if week_agg == "ISO Week":
    deaths = filtered_df.groupby("Week")["Died"].sum().reset_index()
    fig2 = px.bar(deaths, x="Week", y="Died", title="Deaths per ISO Week")
else:
    death_ma = filtered_df.set_index("Date").sort_index().rolling("7D").sum()["Died"].reset_index()
    fig2 = px.line(death_ma, x="Date", y="Died", title="7-Day Moving Average of Deaths")

fig2.update_layout(xaxis_title="Time", yaxis_title="Deaths", hovermode="x unified")
st.plotly_chart(fig2, use_container_width=True)

# Data Table
st.subheader("Filtered Data Table")
st.dataframe(filtered_df)

# Export Option
def convert_df(df):
    return df.to_csv(index=False).encode("utf-8")

csv = convert_df(filtered_df)
st.download_button("Download Filtered Data as CSV", data=csv, file_name="filtered_data.csv", mime="text/csv")
