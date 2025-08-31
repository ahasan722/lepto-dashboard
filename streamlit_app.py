
import streamlit as st
import pandas as pd
import plotly.express as px
import datetime

st.set_page_config(page_title="Lepto Dashboard", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_csv("final_cleaned_lepto_bed_occupancy_corrected.csv", parse_dates=["Date"])
    df["ISO_Week"] = df["Date"].dt.isocalendar().week
    df["Year"] = df["Date"].dt.year
    df["Week"] = df["Year"].astype(str) + "-W" + df["ISO_Week"].astype(str)
    return df

df = load_data()

# Sidebar
st.sidebar.title("Filters")
selected_provinces = st.sidebar.multiselect("Province", sorted(df["Province"].unique()))
selected_cities = st.sidebar.multiselect("City/Mun", sorted(df["City/Mun"].unique()))
disease_type = st.sidebar.selectbox("Disease Type", ["All", "Lepto", "Other"])
agg_method = st.sidebar.selectbox("Aggregation", ["ISO Week", "7-Day Moving Average"])

# Apply filters
def apply_filters(data):
    d = data.copy()
    if selected_provinces:
        d = d[d["Province"].isin(selected_provinces)]
    if selected_cities:
        d = d[d["City/Mun"].isin(selected_cities)]
    if disease_type == "Lepto":
        d = d[d["No. of ICU beds Occupied due to Lepto"] + d["No. of Non-ICU Beds Occupied due to Lepto"] > 0]
    elif disease_type == "Other":
        d = d[d["No. of ICU beds Occupied due to Other diseases"] + d["No. of Non-ICU Beds Occupied due to Other diseases"] > 0]
    return d

filtered_df = apply_filters(df)

# Trends Page
st.title("📊 Trends: Bed Occupancy and Deaths")

# Aggregation
if agg_method == "ISO Week":
    trend_data = filtered_df.groupby("Week")[["Total ICU beds occupied", "Total Non-ICU beds occupied", "Died"]].sum().reset_index()
    x_col = "Week"
else:
    trend_data = filtered_df.set_index("Date").rolling("7D").sum().reset_index()
    x_col = "Date"

# ICU & Non-ICU Beds
st.subheader("ICU and Non-ICU Bed Occupancy Over Time")
fig1 = px.line(trend_data, x=x_col, y=["Total ICU beds occupied", "Total Non-ICU beds occupied"],
               labels={"value": "Beds Occupied", "variable": "Type"}, title="Bed Occupancy Trends")

# ✅ Brush and zoom function (Users can click and drag to highlight a date range, then zoom out)
fig1.update_layout(
    hovermode="x unified",
    xaxis=dict(rangeslider=dict(visible=True))
)

st.plotly_chart(fig1, use_container_width=True)

# Deaths Over Time
st.subheader("Deaths Over Time")
fig2 = px.line(trend_data, x=x_col, y="Died", title="Deaths Trend")

# ✅ Brush and zoom function for deaths chart
fig2.update_layout(
    hovermode="x unified",
    xaxis=dict(rangeslider=dict(visible=True))
)

st.plotly_chart(fig2, use_container_width=True)
