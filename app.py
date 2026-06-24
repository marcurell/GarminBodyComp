import streamlit as st
import pandas as pd
import sys
import os
import plotly.graph_objects as go
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

st.set_page_config(page_title="Body Comp: Modular AI", page_icon="🧩", layout="wide")

def load_css():
    st.markdown("""
    <style>
        .consensus-box { padding: 15px; border-radius: 10px; background-color: #e3f2fd; border-left: 5px solid #2196f3; }
        .stMetric { background-color: #f9f9f9; padding: 10px; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

load_css()

try:
    from modules.data_handler import parse_garmin_custom_csv, clean_and_map_columns
    from modules.logic import run_triangulation
    from modules.garmin_api import fetch_garmin_data
    from modules.auth import require_login, get_current_user, logout_button
    from modules.storage import load_measurements, save_measurements, load_garmin_data, save_garmin_data
except ImportError as e:
    st.error(f"Kritiskt fel: Kunde inte ladda moduler. Felmeddelande: {e}")
    st.stop()

# ==========================================
# AUTH — blocks rendering until logged in
# ==========================================
require_login()
user_id = get_current_user()

st.title("🧩 True Body Comp: Modular & Connected")

# ==========================================
# STATE & CACHING
# ==========================================
if "data" not in st.session_state:
    st.session_state.data = load_garmin_data(user_id)  # restore from blob on refresh
if "measurements" not in st.session_state:
    st.session_state.measurements = load_measurements(user_id)

@st.cache_data(ttl=3600)
def cached_triangulation(df, meas, height, gender):
    return run_triangulation(df, meas, height, gender)

# ==========================================
# SIDEBAR: DATA INPUT
# ==========================================
with st.sidebar:
    st.header("1. Hämta Data")

    source_tab1, source_tab2 = st.tabs(["☁️ Garmin Cloud", "📂 CSV Fil"])

    with source_tab1:
        st.info("Logga in med ditt Garmin-konto.")
        with st.form("garmin_login"):
            email = st.text_input("E-mail")
            password = st.text_input("Lösenord", type="password")
            days = st.number_input("Hämta antal dagar", 30, 365, 60)

            if st.form_submit_button("Hämta från Cloud"):
                if not email or not password:
                    st.error("Ange e-post och lösenord.")
                else:
                    with st.spinner("Ansluter till Garmin..."):
                        df_api, error = fetch_garmin_data(email, password, days, user_id)
                        if df_api is not None:
                            cleaned = clean_and_map_columns(df_api)
                            st.session_state.data = cleaned
                            save_garmin_data(user_id, cleaned)  # persist across refreshes
                            st.success(f"Klart! Hämtade {len(df_api)} mätningar.")
                        else:
                            st.error(f"Fel vid hämtning: {error}")

    with source_tab2:
        uploaded_file = st.file_uploader("Ladda upp CSV", type=["csv"])
        if uploaded_file:
            try:
                content = uploaded_file.getvalue().decode("utf-8", errors="replace")
                raw_input = parse_garmin_custom_csv(content)
                if raw_input is None:
                    uploaded_file.seek(0)
                    raw_input = pd.read_csv(uploaded_file, skiprows=20, on_bad_lines="skip")
                st.session_state.data = clean_and_map_columns(raw_input)
                st.success("CSV Inläst!")
            except Exception as e:
                st.error(f"Kunde inte läsa filen: {e}")

    st.divider()

    st.header("2. Fysiska Data")
    height = st.number_input("Din Längd (cm)", 150, 220, 180)
    gender = st.radio("Kön", ["Man", "Kvinna"])

    st.header("3. Måttband (Ankare)")
    with st.form("tape_measure"):
        m_date = st.date_input("Datum", datetime.now())
        m_waist = st.number_input("Midjemått (cm)", 50, 150, 90)
        m_neck = st.number_input("Halsmått (cm)", 20, 60, 40)
        m_hip = st.number_input("Höftmått (cm) [0 = Frivilligt]", 0, 150, 0)

        if st.form_submit_button("Spara Mätning"):
            new_m = pd.DataFrame([{
                "Date": pd.to_datetime(m_date),
                "Waist": m_waist, "Neck": m_neck, "Hip": m_hip
            }])
            if st.session_state.measurements.empty:
                updated_df = new_m
            else:
                combined = pd.concat([st.session_state.measurements, new_m])
                updated_df = combined.drop_duplicates(subset="Date", keep="last").sort_values("Date")

            st.session_state.measurements = updated_df
            save_measurements(user_id, updated_df)
            st.success("Sparat!")
            st.rerun()

    if not st.session_state.measurements.empty:
        with st.expander("Visa sparade mått"):
            st.dataframe(st.session_state.measurements, hide_index=True)
            if st.button("Rensa Mätningar"):
                empty_df = pd.DataFrame(columns=["Date", "Waist", "Neck", "Hip"])
                st.session_state.measurements = empty_df
                save_measurements(user_id, empty_df)
                st.rerun()

    st.divider()
    logout_button()

# ==========================================
# MAIN APP LOGIC
# ==========================================
if st.session_state.data is not None:
    df = st.session_state.data
    meas = st.session_state.measurements

    if meas.empty:
        st.warning("⚠️ Tips: Lägg till minst en måttbandsmätning i menyn för att kalibrera AI:n!")

    processed_df = cached_triangulation(df, meas, height, gender)

    if processed_df is None or processed_df.empty:
        st.error("Ingen data kunde beräknas. Kontrollera att datumen matchar.")
    else:
        latest = processed_df.iloc[-1]
        prev = processed_df.iloc[-2] if len(processed_df) > 1 else latest
        bias = latest.get("Bias_Offset", 0)

        st.markdown(f"""
        <div class="consensus-box">
            <h3>🤖 Triangulerings-Analys</h3>
            <p><b>SLUTSATS:</b> Din sanna fettprocent är sannolikt <b>{latest.get('Consensus_Fat_Pct', 0):.1f}%</b>.</p>
            <small>Garmin visade {latest.get('fat_pct', 0):.1f}% (Avvikelse {bias:+.1f}%)</small>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Vikt", f"{latest.get('weight_kg', 0):.1f} kg", f"{(latest.get('weight_kg', 0)-prev.get('weight_kg', 0)):.1f} kg")
        col2.metric("SANN Fett %", f"{latest.get('Consensus_Fat_Pct', 0):.1f} %", f"{(latest.get('Consensus_Fat_Pct', 0)-prev.get('Consensus_Fat_Pct', 0)):.1f} %")
        col3.metric("Lean Mass", f"{latest.get('Lean_Mass_kg', 0):.1f} kg")
        col4.metric("Bias", f"{bias:+.1f} %")

        tab1, tab2 = st.tabs(["🎯 Sanningen", "📊 Data"])

        with tab1:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=processed_df["Date"], y=processed_df["fat_pct"], name="Garmin (Rå)", line=dict(color="gray", dash="dot"), opacity=0.3))
            if "Navy_Fat_Pct" in processed_df.columns:
                fig.add_trace(go.Scatter(x=processed_df["Date"], y=processed_df["Navy_Fat_Pct"], name="Navy (Måttband)", line=dict(color="#1976d2", width=2)))
            fig.add_trace(go.Scatter(x=processed_df["Date"], y=processed_df["Consensus_Fat_Pct"], name="★ CONSENSUS", line=dict(color="#2e7d32", width=4)))
            fig.update_layout(
                title="Jakten på Sanningen",
                hovermode="x unified",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig, use_container_width=True)

        with tab2:
            st.dataframe(processed_df.sort_values("Date", ascending=False), use_container_width=True)

else:
    st.info("👈 Logga in på Garmin eller ladda upp CSV i menyn för att starta.")
