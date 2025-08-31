
import streamlit as st
import pandas as pd
import plotly.express as px
import datetime

# -------------------- CONFIG --------------------
st.set_page_config(page_title="Lepto Dashboard", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_csv("STC-2502958-001.csv", parse_dates=["Date"])
    df["ISO_Week"] = df["Date"].dt.isocalendar().week
    df["Year"] = df["Date"].dt.year
    df["Week"] = df["Year"].astype(str) + "-W" + df["ISO_Week"].astype(str)
    return df

df = load_data()

# -------------------- LOGIN --------------------
def login():
    st.title("Lepto Bed Dashboard Login")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        if submitted:
            if username == "STC-2502958-001" and password == "123456":
                return True
            else:
                st.error("Invalid credentials")
                return False
    return False

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.session_state.logged_in = login()
    if not st.session_state.logged_in:
        st.stop()

# -------------------- NAVIGATION --------------------
page = st.sidebar.radio("Navigate", ["Home", "Data Entry", "Trends", "Tables"])

# Shared filters
province_filter = st.sidebar.multiselect("Province", sorted(df["Province"].unique()))
city_filter = st.sidebar.multiselect("City/Mun", sorted(df[df["Province"].isin(province_filter)]["City/Mun"].unique()) if province_filter else sorted(df["City/Mun"].unique()))
disease_filter = st.sidebar.selectbox("Disease Type", ["All", "Lepto", "Other"])
aggregation = st.sidebar.selectbox("Aggregation", ["ISO Week", "7-Day Moving Average"])

# Apply filters
def apply_filters(data):
    filtered = data.copy()
    if province_filter:
        filtered = filtered[filtered["Province"].isin(province_filter)]
    if city_filter:
        filtered = filtered[filtered["City/Mun"].isin(city_filter)]
    if disease_filter == "Lepto":
        filtered = filtered[(filtered["No. of ICU beds Occupied due to Lepto"] > 0) | 
                            (filtered["No. of Non-ICU Beds Occupied due to Lepto"] > 0)]
    elif disease_filter == "Other":
        filtered = filtered[(filtered["No. of ICU beds Occupied due to Other diseases"] > 0) | 
                            (filtered["No. of Non-ICU Beds Occupied due to Other diseases"] > 0)]
    return filtered

filtered_df = apply_filters(df)

# -------------------- HOME --------------------
if page == "Home":
    st.title("Leptospirosis Bed Monitoring Dashboard")
    st.write("Monitor ICU and Non-ICU bed usage across Central Luzon hospitals.")

    st.subheader("Summary Panel")
    col1, col2 = st.columns(2)
    col1.metric("Current Total ICU Occupancy", int(filtered_df["Total ICU beds occupied"].sum()))
    col2.metric("Current Mortality Rate", f"{filtered_df['% Died'].mean():.2f}%")

# -------------------- DATA ENTRY --------------------
elif page == "Data Entry":
    st.title("New Data Entry (Post 24-Nov-2025 Only)")

    provinces = sorted(df["Province"].unique())
    cities_by_prov = df.groupby("Province")["City/Mun"].unique().to_dict()

    with st.form("entry_form", clear_on_submit=True):
        date = st.date_input("Date", min_value=datetime.date(2025, 11, 25))
        province = st.selectbox("Province", provinces)
        city = st.selectbox("City/Mun", sorted(cities_by_prov.get(province, [])))
        icu_lepto = st.number_input("ICU Beds (Lepto)", min_value=0)
        icu_other = st.number_input("ICU Beds (Other)", min_value=0)
        non_icu_lepto = st.number_input("Non-ICU Beds (Lepto)", min_value=0)
        non_icu_other = st.number_input("Non-ICU Beds (Other)", min_value=0)
        deaths = st.number_input("Deaths", min_value=0)

        submitted = st.form_submit_button("Submit")
        if submitted:
            st.success("✅ Data submitted successfully (This version does not persist to file)")

# -------------------- TRENDS --------------------
elif page == "Trends":
    st.title("ICU & Non-ICU Bed Trends")

    if aggregation == "ISO Week":
        group = filtered_df.groupby("Week")[["Total ICU beds occupied", "Total Non-ICU beds occupied", "Died"]].sum().reset_index()
        x = "Week"
    else:
        numeric_cols = ["Total ICU beds occupied", "Total Non-ICU beds occupied", "Died"]
        df_temp = filtered_df.set_index("Date").sort_index()[numeric_cols]
        group = df_temp.rolling("7D", min_periods=1).sum().reset_index()
        x = "Date"

    st.subheader("ICU and Non-ICU Bed Occupancy Over Time")
    fig1 = px.line(group, x=x, y=["Total ICU beds occupied", "Total Non-ICU beds occupied"])
    fig1.update_layout(hovermode="x unified", xaxis=dict(rangeslider=dict(visible=True)))
    st.plotly_chart(fig1, use_container_width=True)

    st.subheader("Deaths Over Time")
    fig2 = px.line(group, x=x, y="Died")
    fig2.update_layout(hovermode="x unified", xaxis=dict(rangeslider=dict(visible=True)))
    st.plotly_chart(fig2, use_container_width=True)

# -------------------- TABLES --------------------
elif page == "Tables":
    st.title("Filtered Data Table")
    st.dataframe(filtered_df)

    csv = filtered_df.to_csv(index=False).encode("utf-8")
    st.download_button("Download Filtered Data (CSV)", data=csv, file_name="filtered_lepto_data.csv", mime="text/csv")
