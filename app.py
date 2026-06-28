import html
import logging
import os
import sys

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
logging.basicConfig(level=logging.WARNING)

st.set_page_config(
    page_title="True Body Composition",
    page_icon="🏃",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Garmin-inspired dark theme ───────────────────────────────────────────────
st.markdown("""
<style>
    /* Base */
    [data-testid="stAppViewContainer"] { background-color: #111318; }
    [data-testid="stSidebar"] { background-color: #1C1E26; border-right: 1px solid #2E3140; }
    [data-testid="stHeader"] { background-color: #111318; }

    /* Typography — high contrast throughout */
    html, body, [class*="css"] { color: #E8EAF0; }
    p, span, div { color: #E8EAF0; }
    h1, h2, h3 { color: #FFFFFF !important; font-weight: 700; letter-spacing: -0.5px; }

    /* Labels */
    label { color: #C8CDE0 !important; font-size: 0.85rem !important; }
    [data-testid="stSidebar"] label { color: #C8CDE0 !important; }

    /* Radio buttons */
    [data-testid="stRadio"] label { color: #E8EAF0 !important; font-size: 0.9rem !important; }
    [data-testid="stRadio"] p { color: #E8EAF0 !important; }

    /* Checkboxes and selects */
    [data-testid="stSelectbox"] label,
    [data-testid="stMultiSelect"] label { color: #C8CDE0 !important; }

    /* Metric cards */
    [data-testid="stMetric"] {
        background-color: #1C1E26;
        border: 1px solid #2E3140;
        border-radius: 12px;
        padding: 16px 20px;
    }
    [data-testid="stMetricLabel"] { color: #8A94B8 !important; font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.8px; }
    [data-testid="stMetricValue"] { color: #FFFFFF !important; font-size: 1.8rem; font-weight: 700; }
    [data-testid="stMetricDelta"] { font-size: 0.85rem; }

    /* Inputs */
    [data-testid="stTextInput"] input,
    [data-testid="stNumberInput"] input,
    [data-testid="stDateInput"] input {
        background-color: #252830 !important;
        border: 1px solid #3E4255 !important;
        border-radius: 8px !important;
        color: #FFFFFF !important;
        font-size: 0.95rem !important;
    }
    [data-testid="stTextInput"] input::placeholder { color: #6B7494 !important; }
    [data-testid="stTextInput"] input:focus,
    [data-testid="stNumberInput"] input:focus {
        border-color: #1DB9E8 !important;
        box-shadow: 0 0 0 2px rgba(29,185,232,0.2) !important;
    }

    /* Number input stepper */
    [data-testid="stNumberInput"] button { color: #E8EAF0 !important; background: #2E3140 !important; border: none !important; }

    /* Date input */
    [data-testid="stDateInput"] input { color: #FFFFFF !important; }

    /* Buttons */
    [data-testid="stFormSubmitButton"] button,
    [data-testid="stButton"] button {
        background-color: #1DB9E8 !important;
        color: #000000 !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 8px 20px !important;
    }
    [data-testid="stFormSubmitButton"] button:hover,
    [data-testid="stButton"] button:hover { background-color: #00A8D8 !important; }

    /* Tabs */
    [data-testid="stTabs"] [role="tab"] { color: #8A94B8 !important; border-bottom: 2px solid transparent; font-weight: 500; }
    [data-testid="stTabs"] [role="tab"][aria-selected="true"] { color: #1DB9E8 !important; border-bottom-color: #1DB9E8; }

    /* Dataframe */
    [data-testid="stDataFrame"] { border: 1px solid #2E3140; border-radius: 8px; }

    /* Divider */
    hr { border-color: #2E3140; }

    /* Consensus box */
    .consensus-box {
        padding: 20px 24px;
        border-radius: 12px;
        background: linear-gradient(135deg, #1a2a3a 0%, #1C1E26 100%);
        border: 1px solid #2E3140;
        border-left: 4px solid #1DB9E8;
    }
    .consensus-box h3 { color: #1DB9E8; margin: 0 0 8px 0; font-size: 1rem; text-transform: uppercase; letter-spacing: 1px; }
    .consensus-box .value { color: #FFFFFF; font-size: 2.5rem; font-weight: 700; line-height: 1; }
    .consensus-box .sub { color: #6B7494; font-size: 0.85rem; margin-top: 6px; }

    /* Sidebar headers */
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 { color: #1DB9E8; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 1px; }

    /* Info/warning/error boxes */
    [data-testid="stInfo"]    { background-color: #1a2535; border-color: #1DB9E8; color: #C8E8F8 !important; }
    [data-testid="stInfo"] p  { color: #C8E8F8 !important; }
    [data-testid="stWarning"] { background-color: #2a2010; border-color: #F0A500; color: #F8DCA0 !important; }
    [data-testid="stWarning"] p { color: #F8DCA0 !important; }
    [data-testid="stSuccess"] { background-color: #102a15; border-color: #30D158; color: #A0F0B8 !important; }
    [data-testid="stSuccess"] p { color: #A0F0B8 !important; }
    [data-testid="stError"]   { background-color: #2a1010; border-color: #FF453A; color: #F8A0A0 !important; }
    [data-testid="stError"] p { color: #F8A0A0 !important; }

    /* Expander */
    [data-testid="stExpander"] { border: 1px solid #2E3140 !important; border-radius: 8px !important; }
    [data-testid="stExpander"] summary { color: #C8CDE0 !important; }
</style>
""", unsafe_allow_html=True)

try:
    from modules.data_handler import parse_garmin_custom_csv, clean_and_map_columns
    from modules.logic import run_triangulation
    from modules.garmin_api import fetch_garmin_data
    from modules.auth import require_login, get_current_user, logout_button
    from modules.storage import (
        load_measurements, save_measurements,
        load_garmin_data, save_garmin_data, delete_garmin_rows,
        load_profile, save_profile,
    )
except ImportError as e:
    st.error("Kritiskt fel: Kunde inte ladda moduler. Kontakta admin.")
    logging.critical("Module import failed: %s", e)
    st.stop()

# ── Auth ─────────────────────────────────────────────────────────────────────
require_login()
user_id = get_current_user()

# ── Header ───────────────────────────────────────────────────────────────────
st.markdown("# 🏃 True Body Composition")
st.markdown("<p style='color:#6B7494;margin-top:-12px;'>Powered by Garmin + AI Triangulation</p>", unsafe_allow_html=True)
st.markdown("---")

# ── Session state ─────────────────────────────────────────────────────────────
if "data" not in st.session_state:
    st.session_state.data = load_garmin_data(user_id)
if "measurements" not in st.session_state:
    st.session_state.measurements = load_measurements(user_id)
if "profile" not in st.session_state:
    st.session_state.profile = load_profile(user_id)

@st.cache_data(ttl=3600)
def cached_triangulation(df, meas, height, gender):
    return run_triangulation(df, meas, height, gender)

MAX_CSV_BYTES = 10 * 1024 * 1024

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:

    # ── Profile ──────────────────────────────────────────────────────────────
    with st.expander("⚙️ Profil"):
        def _save_profile():
            save_profile(user_id, {
                "height": st.session_state.height_input,
                "gender": st.session_state.gender_input,
            })

        st.number_input(
            "Längd (cm)", min_value=100, max_value=250,
            value=st.session_state.profile.get("height", 180),
            key="height_input", on_change=_save_profile,
        )
        st.radio(
            "Kön", ["Man", "Kvinna"],
            index=0 if st.session_state.profile.get("gender", "Man") == "Man" else 1,
            key="gender_input", on_change=_save_profile,
        )
        st.caption("Sparas automatiskt vid ändring.")

    height = st.session_state.get("height_input", st.session_state.profile.get("height", 180))
    gender = st.session_state.get("gender_input", st.session_state.profile.get("gender", "Man"))

    st.markdown("---")

    # ── Import from Garmin ───────────────────────────────────────────────────
    with st.expander("☁️ Importera från Garmin"):
        with st.form("garmin_login"):
            email = st.text_input("E-mail")
            password = st.text_input("Lösenord", type="password")
            days = st.number_input("Antal dagar", 30, 365, 60)
            if st.form_submit_button("🔄 Hämta från Garmin"):
                if not email or "@" not in email:
                    st.error("Ange en giltig e-postadress.")
                elif not password:
                    st.error("Ange lösenord.")
                else:
                    with st.spinner("Ansluter till Garmin..."):
                        df_api, error = fetch_garmin_data(email, password, int(days), user_id)
                        if df_api is not None:
                            cleaned = clean_and_map_columns(df_api)
                            save_garmin_data(user_id, cleaned)
                            st.session_state.data = load_garmin_data(user_id)
                            st.success(f"✓ {len(df_api)} nya rader hämtade (totalt {len(st.session_state.data)} i databasen).")
                        else:
                            st.error(error)

    # ── CSV upload ───────────────────────────────────────────────────────────
    with st.expander("📂 Ladda upp CSV"):
        uploaded_file = st.file_uploader("Garmin-export CSV", type=["csv"])
        if uploaded_file:
            if uploaded_file.size > MAX_CSV_BYTES:
                st.error("Filen är för stor (max 10 MB).")
            else:
                try:
                    content = uploaded_file.getvalue().decode("utf-8", errors="replace")
                    raw_input = parse_garmin_custom_csv(content)
                    if raw_input is None:
                        uploaded_file.seek(0)
                        raw_input = pd.read_csv(uploaded_file, skiprows=20, on_bad_lines="skip")
                    cleaned = clean_and_map_columns(raw_input)
                    save_garmin_data(user_id, cleaned)
                    st.session_state.data = load_garmin_data(user_id)
                    st.success("✓ CSV importerad och sammanfogad!")
                except Exception:
                    st.error("Kunde inte läsa filen.")

    st.markdown("---")

    # ── Add measurement ───────────────────────────────────────────────────────
    with st.expander("➕ Lägg till mätning"):
        source = st.selectbox(
            "Typ av mätning",
            ["Måttband (Navy)", "DEXA Scan", "BodyPod"],
            key="meas_source_select",
        )
        with st.form("add_measurement"):
            m_date = st.date_input("Datum", datetime.now())

            if source == "Måttband (Navy)":
                m_waist = st.number_input("Midja (cm)", min_value=30, max_value=200, value=90)
                m_neck  = st.number_input("Hals (cm)",  min_value=10, max_value=100, value=40)
                m_hip   = st.number_input("Höft (cm) [0 = hoppa över]", min_value=0, max_value=200, value=0)
                m_fat   = None
            else:
                m_fat   = st.number_input("Fettprocent (%)", min_value=1.0, max_value=60.0, value=20.0, step=0.1)
                m_waist = m_neck = m_hip = None

            if st.form_submit_button("💾 Spara mätning"):
                src_key = {"Måttband (Navy)": "Navy", "DEXA Scan": "DEXA", "BodyPod": "BodyPod"}[source]
                new_row = pd.DataFrame([{
                    "Date":       pd.to_datetime(m_date),
                    "Source":     src_key,
                    "BodyFatPct": m_fat if m_fat is not None else float("nan"),
                    "Waist":      m_waist if m_waist is not None else float("nan"),
                    "Neck":       m_neck  if m_neck  is not None else float("nan"),
                    "Hip":        m_hip   if m_hip   is not None else float("nan"),
                }])
                combined = pd.concat([st.session_state.measurements, new_row])
                combined = (combined
                    .drop_duplicates(subset=["Date", "Source"], keep="last")
                    .sort_values("Date")
                    .reset_index(drop=True))
                st.session_state.measurements = combined
                save_measurements(user_id, combined)
                st.success("✓ Sparat!")
                st.rerun()

    st.markdown("---")
    logout_button()

# ── Main ──────────────────────────────────────────────────────────────────────
if st.session_state.data is not None:
    df       = st.session_state.data
    meas     = st.session_state.measurements
    navy_meas = meas[meas["Source"] == "Navy"][["Date", "Waist", "Neck", "Hip"]].copy()
    ref_meas  = meas[meas["Source"].isin(["DEXA", "BodyPod"])].copy()

    if navy_meas.empty and ref_meas.empty:
        st.warning("Lägg till minst en mätning för att kalibrera analysen.")

    processed_df = cached_triangulation(df, navy_meas, height, gender)

    if processed_df is None or processed_df.empty:
        st.error("Ingen data kunde beräknas. Kontrollera att datumen matchar.")
    else:
        latest = processed_df.iloc[-1]
        prev   = processed_df.iloc[-2] if len(processed_df) > 1 else latest
        bias   = latest.get("Bias_Offset", 0)

        consensus_pct = html.escape(f"{latest.get('Consensus_Fat_Pct', 0):.1f}")
        garmin_pct    = html.escape(f"{latest.get('fat_pct', 0):.1f}")
        bias_str      = html.escape(f"{bias:+.1f}")

        # ── Summary card ─────────────────────────────────────────────────────
        st.markdown(f"""
        <div class="consensus-box">
            <h3>AI Triangulering — Resultat</h3>
            <div class="value">{consensus_pct}<span style="font-size:1.2rem;color:#6B7494">%</span></div>
            <div class="sub">Uppskattad sann fettprocent &nbsp;·&nbsp; Garmin visade {garmin_pct}% (avvikelse {bias_str}%)</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Vikt", f"{latest.get('weight_kg', 0):.1f} kg",
                    f"{(latest.get('weight_kg', 0)-prev.get('weight_kg', 0)):.1f} kg")
        col2.metric("Fettprocent", f"{latest.get('Consensus_Fat_Pct', 0):.1f} %",
                    f"{(latest.get('Consensus_Fat_Pct', 0)-prev.get('Consensus_Fat_Pct', 0)):.1f} %")
        col3.metric("Lean Mass", f"{latest.get('Lean_Mass_kg', 0):.1f} kg")
        col4.metric("Garmin Avvikelse", f"{bias:+.1f} %")

        st.markdown("<br>", unsafe_allow_html=True)

        tab_chart, tab_meas, tab_garmin = st.tabs(["📈 Trender", "📋 Mätningar", "📊 Garmin Data"])

        # ── Chart ─────────────────────────────────────────────────────────────
        with tab_chart:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=processed_df["Date"], y=processed_df["fat_pct"],
                name="Garmin (rå)", line=dict(color="#4A5070", dash="dot", width=1.5), opacity=0.6
            ))
            if "Navy_Fat_Pct" in processed_df.columns:
                fig.add_trace(go.Scatter(
                    x=processed_df["Date"], y=processed_df["Navy_Fat_Pct"],
                    name="Navy (måttband)", line=dict(color="#1DB9E8", width=2)
                ))
            fig.add_trace(go.Scatter(
                x=processed_df["Date"], y=processed_df["Consensus_Fat_Pct"],
                name="Consensus", line=dict(color="#30D158", width=3),
                fill="tozeroy", fillcolor="rgba(48,209,88,0.05)"
            ))
            # DEXA / BodyPod reference markers
            for src, color, symbol in [("DEXA", "#F0A500", "diamond"), ("BodyPod", "#FF6B6B", "circle")]:
                src_df = ref_meas[ref_meas["Source"] == src]
                if not src_df.empty:
                    fig.add_trace(go.Scatter(
                        x=src_df["Date"], y=src_df["BodyFatPct"],
                        mode="markers", name=src,
                        marker=dict(color=color, size=12, symbol=symbol,
                                    line=dict(color="#FFFFFF", width=1.5)),
                    ))
            fig.update_layout(
                paper_bgcolor="#111318", plot_bgcolor="#1C1E26",
                font=dict(color="#A0A8C0"),
                title=dict(text="Fettprocent över tid", font=dict(color="#FFFFFF", size=16)),
                hovermode="x unified",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                            bgcolor="rgba(0,0,0,0)", font=dict(color="#A0A8C0")),
                xaxis=dict(gridcolor="#2E3140", linecolor="#2E3140"),
                yaxis=dict(gridcolor="#2E3140", linecolor="#2E3140"),
                margin=dict(t=60, b=40),
            )
            st.plotly_chart(fig, width="stretch")

        # ── Measurements table ────────────────────────────────────────────────
        with tab_meas:
            if meas.empty:
                st.info("Inga mätningar tillagda ännu. Använd '➕ Lägg till mätning' i menyn.")
            else:
                display = meas.copy()
                display["Date"] = display["Date"].dt.strftime("%Y-%m-%d")
                st.dataframe(display, width="stretch", hide_index=True)

                st.markdown("**Ta bort mätningar**")
                date_source_labels = [
                    f"{row['Date'].strftime('%Y-%m-%d')} — {row['Source']}"
                    for _, row in meas.iterrows()
                ]
                to_delete = st.multiselect("Välj rader att ta bort", date_source_labels, key="meas_delete_select")
                col_del, col_clear = st.columns([1, 1])
                with col_del:
                    if to_delete and st.button("🗑 Ta bort valda", key="del_meas_selected"):
                        indices = [date_source_labels.index(lbl) for lbl in to_delete]
                        updated = meas.drop(meas.index[indices]).reset_index(drop=True)
                        st.session_state.measurements = updated
                        save_measurements(user_id, updated)
                        st.rerun()
                with col_clear:
                    if st.button("🗑 Rensa alla", key="del_meas_all"):
                        empty_df = pd.DataFrame(columns=["Date", "Source", "BodyFatPct", "Waist", "Neck", "Hip"])
                        st.session_state.measurements = empty_df
                        save_measurements(user_id, empty_df)
                        st.rerun()

        # ── Garmin data table ─────────────────────────────────────────────────
        with tab_garmin:
            gdf = st.session_state.data
            if gdf is None or gdf.empty:
                st.info("Ingen Garmin-data importerad ännu.")
            else:
                st.caption(f"{len(gdf)} datapunkter · {gdf['Date'].min().date()} → {gdf['Date'].max().date()}")

                # Date filter
                col_f1, col_f2 = st.columns(2)
                with col_f1:
                    filter_from = st.date_input("Från", gdf["Date"].min().date(), key="g_from")
                with col_f2:
                    filter_to = st.date_input("Till", gdf["Date"].max().date(), key="g_to")

                mask = (gdf["Date"].dt.date >= filter_from) & (gdf["Date"].dt.date <= filter_to)
                gdf_filtered = gdf[mask].copy()
                gdf_filtered["Date"] = gdf_filtered["Date"].dt.strftime("%Y-%m-%d")
                st.dataframe(gdf_filtered, width="stretch", hide_index=True)

                st.markdown("**Ta bort datapunkter**")
                g_dates = gdf[mask]["Date"].dt.strftime("%Y-%m-%d").tolist()
                g_to_delete = st.multiselect("Välj datum att ta bort", g_dates, key="garmin_delete_select")
                if g_to_delete and st.button("🗑 Ta bort valda Garmin-rader"):
                    delete_garmin_rows(user_id, g_to_delete)
                    st.session_state.data = load_garmin_data(user_id)
                    st.rerun()

else:
    st.markdown("""
    <div style="text-align:center;padding:80px 20px;color:#4A5070;">
        <div style="font-size:4rem;">🏃</div>
        <h2 style="color:#6B7494;font-weight:400;">Ingen data ännu</h2>
        <p>Importera från Garmin eller ladda upp en CSV-fil i menyn till vänster.</p>
    </div>
    """, unsafe_allow_html=True)
