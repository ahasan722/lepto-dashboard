
import streamlit as st
import pandas as pd
import plotly.express as px
import datetime

st.set_page_config(page_title="Lepto Bed Dashboard", layout="wide")

# Background styling
st.markdown("""
    <style>
        body { background-color: #f4f6f9; }
        .block-container { padding-top: 2rem; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_data():
    df = pd.read_csv("STC-2502958-001.csv", parse_dates=["Date"])
    df["Lepto ICU"] = df["No. of ICU beds Occupied due to Lepto"]
    df["Other ICU"] = df["No. of ICU beds Occupied due to Other diseases"]
    df["Lepto Non-ICU"] = df["No. of Non-ICU Beds Occupied due to Lepto"]
    df["Other Non-ICU"] = df["No. of Non-ICU Beds Occupied due to Other diseases"]
    df["ISO_Week"] = df["Date"].dt.isocalendar().week
    df["Year"] = df["Date"].dt.year
    df["Week"] = df["Year"].astype(str) + "-W" + df["ISO_Week"].astype(str)
    return df

df = load_data()

# -------------------- LOGIN --------------------
def login_view():
    st.title("Login")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        if submitted:
            if username == "STC-2502958-001" and password == "123456":
                st.session_state.logged_in = True
                st.session_state.page = "Home"
                st.rerun()
            else:
                st.error("Invalid credentials")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "page" not in st.session_state:
    st.session_state.page = "Login"

if not st.session_state.logged_in:
    login_view()
    st.stop()

# -------------------- SIDEBAR --------------------
st.sidebar.title("Navigation")
page = st.sidebar.radio("Navigate", ["Home", "Summary", "Data Entry", "Trends", "Tables"], index=0)

province_filter = st.sidebar.multiselect("Province", sorted(df["Province"].unique()),
                                         default=st.session_state.get("province_filter", []))
city_filter = st.sidebar.multiselect("City/Mun", 
                                     sorted(df[df["Province"].isin(province_filter)]["City/Mun"].unique()) if province_filter else sorted(df["City/Mun"].unique()),
                                     default=st.session_state.get("city_filter", []))
disease_mode = st.sidebar.selectbox("Disease Type View", ["All (both)", "Lepto only", "Other only"],
                                    index=["All (both)", "Lepto only", "Other only"].index(st.session_state.get("disease_mode", "All (both)")))
aggregation = st.sidebar.selectbox("Aggregation", ["ISO Week", "7-Day Moving Average"],
                                   index=["ISO Week", "7-Day Moving Average"].index(st.session_state.get("aggregation", "ISO Week")))

col_buttons = st.sidebar.columns(2)
if col_buttons[0].button("Clear filters"):
    st.session_state.province_filter = []
    st.session_state.city_filter = []
    st.session_state.disease_mode = "All (both)"
    st.session_state.aggregation = "ISO Week"
    st.rerun()

if col_buttons[1].button("Log out"):
    st.session_state.logged_in = False
    st.rerun()

# -------------------- FILTERS --------------------
def apply_filters(data):
    d = data.copy()
    if province_filter:
        d = d[d["Province"].isin(province_filter)]
    if city_filter:
        d = d[d["City/Mun"].isin(city_filter)]
    if disease_mode == "Lepto only":
        d = d.assign(
            **{
                "Total ICU beds occupied": d["Lepto ICU"],
                "Total Non-ICU beds occupied": d["Lepto Non-ICU"],
                "Total beds occupied": d["Lepto ICU"] + d["Lepto Non-ICU"]
            }
        )
    elif disease_mode == "Other only":
        d = d.assign(
            **{
                "Total ICU beds occupied": d["Other ICU"],
                "Total Non-ICU beds occupied": d["Other Non-ICU"],
                "Total beds occupied": d["Other ICU"] + d["Other Non-ICU"]
            }
        )
    return d

filtered_df = apply_filters(df)

# -------------------- HOME --------------------
if page == "Home":
    st.title("Leptospirosis Bed Monitoring Dashboard")
    st.write("Welcome to the Central Luzon Lepto Bed Monitoring System.")
    st.write(f"Dataset covers {len(df)} records from {df['Date'].min().date()} to {df['Date'].max().date()}.")

    st.subheader("Key Metrics")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Records (Filtered)", len(filtered_df))
    col2.metric("Total ICU Occupancy", int(filtered_df["Total ICU beds occupied"].sum()))
    mortality = round((filtered_df["Died"].sum() / filtered_df["Total beds occupied"].sum())*100, 2) if filtered_df["Total beds occupied"].sum() else 0
    col3.metric("Mortality Rate", f"{mortality}%")

# -------------------- SUMMARY --------------------
elif page == "Summary":
    st.title("Summary Panel")
    col1, col2, col3 = st.columns(3)
    col1.metric("ICU Beds", int(filtered_df["Total ICU beds occupied"].sum()))
    col2.metric("Non-ICU Beds", int(filtered_df["Total Non-ICU beds occupied"].sum()))
    col3.metric("Total Beds", int(filtered_df["Total beds occupied"].sum()))
    st.metric("Mortality Rate", f"{round((filtered_df['Died'].sum()/filtered_df['Total beds occupied'].sum())*100,2) if filtered_df['Total beds occupied'].sum() else 0}%")

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
            st.success("✅ Data submitted (simulation only)")

# -------------------- TRENDS --------------------
elif page == "Trends":
    st.title("Trends Dashboard")
    if aggregation == "ISO Week":
        group = filtered_df.groupby("Week")[["Total ICU beds occupied", "Total Non-ICU beds occupied", "Died"]].sum().reset_index()
        x = "Week"
    else:
        numeric_cols = ["Total ICU beds occupied", "Total Non-ICU beds occupied", "Died"]
        df_temp = filtered_df.set_index("Date").sort_index()[numeric_cols]
        group = df_temp.rolling("7D", min_periods=1).sum().reset_index()
        x = "Date"

    st.subheader("ICU and Non-ICU Bed Occupancy")
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
