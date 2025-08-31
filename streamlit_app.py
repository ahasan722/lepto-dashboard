
import streamlit as st
import pandas as pd
import plotly.express as px
import datetime

# -------------------- AUTH --------------------
def check_login():
    with st.sidebar:
        st.title("🔐 Secure Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if username == "STC-2502958-001" and password == "123456":
            return True
        else:
            st.warning("Enter valid credentials")
            return False

if not check_login():
    st.stop()

# -------------------- CONFIG --------------------
st.set_page_config(page_title="Lepto Bed Dashboard", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_csv("final_cleaned_lepto_bed_occupancy_corrected.csv", parse_dates=["Date"])
    df["ISO_Week"] = df["Date"].dt.isocalendar().week
    df["Year"] = df["Date"].dt.year
    df["Week"] = df["Year"].astype(str) + "-W" + df["ISO_Week"].astype(str)
    return df

df = load_data()

# -------------------- SIDEBAR FILTERS --------------------
st.sidebar.title("Filters")
page = st.sidebar.radio("Navigate", ["🏠 Home", "📥 Data Entry", "📊 Trends", "📋 Tables"])

selected_provinces = st.sidebar.multiselect("Province", sorted(df["Province"].unique()))
selected_cities = st.sidebar.multiselect("City/Mun", sorted(df["City/Mun"].unique()))
disease_type = st.sidebar.selectbox("Disease Type", ["All", "Lepto", "Other"])
agg_method = st.sidebar.selectbox("Aggregation", ["ISO Week", "7-Day Moving Average"])

def apply_filters(data):
    d = data.copy()
    if selected_provinces:
        d = d[d["Province"].isin(selected_provinces)]
    if selected_cities:
        d = d[d["City/Mun"].isin(selected_cities)]
    if disease_type == "Lepto":
        d = d[(d["No. of ICU beds Occupied due to Lepto"] > 0) | (d["No. of Non-ICU Beds Occupied due to Lepto"] > 0)]
    elif disease_type == "Other":
        d = d[(d["No. of ICU beds Occupied due to Other diseases"] > 0) | (d["No. of Non-ICU Beds Occupied due to Other diseases"] > 0)]
    return d

filtered_df = apply_filters(df)

# -------------------- HOME --------------------
if page == "🏠 Home":
    st.title("🏥 Lepto Bed Occupancy Dashboard")
    st.markdown("Monitor ICU and non-ICU occupancy due to Leptospirosis and other diseases across Central Luzon.")
    st.subheader("📊 Summary Panel")

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Current Total ICU Occupancy", int(filtered_df["Total ICU beds occupied"].sum()))
    with col2:
        st.metric("Current Mortality Rate", f"{filtered_df['% Died'].mean():.2f} %")

# -------------------- DATA ENTRY --------------------
elif page == "📥 Data Entry":
    st.title("📥 Data Entry (After Nov 24, 2025 Only)")
    with st.form("entry_form", clear_on_submit=True):
        date = st.date_input("Date", value=datetime.date(2025, 11, 25), min_value=datetime.date(2025, 11, 25))
        province = st.text_input("Province")
        city = st.text_input("City/Mun")
        icu_lepto = st.number_input("ICU Beds (Lepto)", min_value=0)
        icu_other = st.number_input("ICU Beds (Other)", min_value=0)
        non_icu_lepto = st.number_input("Non-ICU Beds (Lepto)", min_value=0)
        non_icu_other = st.number_input("Non-ICU Beds (Other)", min_value=0)
        died = st.number_input("Deaths", min_value=0)
        submit = st.form_submit_button("Submit")

        if submit:
            st.success("✅ Data submitted (Note: permanent save requires backend)")

# -------------------- TRENDS --------------------
elif page == "📊 Trends":
    st.title("📈 Trends Dashboard")

    st.subheader("ICU & Non-ICU Bed Occupancy Over Time")

    if agg_method == "ISO Week":
        data_plot = filtered_df.groupby("Week")[["Total ICU beds occupied", "Total Non-ICU beds occupied", "Died"]].sum().reset_index()
        x = "Week"
    else:
        df_temp = filtered_df.set_index("Date").sort_index()
        data_plot = df_temp.rolling("7D").sum().reset_index()
        x = "Date"

    fig1 = px.line(data_plot, x=x, y=["Total ICU beds occupied", "Total Non-ICU beds occupied"],
                   labels={"value": "Beds Occupied", "variable": "Type"}, title="ICU and Non-ICU Bed Occupancy")
    fig1.update_layout(
        hovermode="x unified",
        xaxis=dict(rangeslider=dict(visible=True))  # ✅ Brush and zoom
    )
    st.plotly_chart(fig1, use_container_width=True)

    st.subheader("💀 Deaths Over Time")
    fig2 = px.line(data_plot, x=x, y="Died", title="Death Trend")
    fig2.update_layout(
        hovermode="x unified",
        xaxis=dict(rangeslider=dict(visible=True))  # ✅ Brush and zoom
    )
    st.plotly_chart(fig2, use_container_width=True)

# -------------------- TABLES & EXPORT --------------------
elif page == "📋 Tables":
    st.title("📋 Filtered Data Table")
    st.dataframe(filtered_df)

    csv_data = filtered_df.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Download Filtered Data (CSV)", data=csv_data, file_name="filtered_lepto_data.csv", mime="text/csv")
