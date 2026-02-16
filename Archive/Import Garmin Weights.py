import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots  # <--- Denna saknades!
from datetime import datetime, timedelta
import re

# ==========================================
# 1. KONFIGURATION & DESIGN
# ==========================================
st.set_page_config(page_title="Body Comp: Triangulation Engine", page_icon="📐", layout="wide")

st.markdown("""
<style>
    .big-font { font-size:24px !important; font-weight: bold; }
    .consensus-box { padding: 15px; border-radius: 10px; background-color: #e3f2fd; border-left: 5px solid #2196f3; }
    .metric-card { background-color: #f9f9f9; padding: 10px; border-radius: 5px; border: 1px solid #ddd; text-align: center; }
</style>
""", unsafe_allow_html=True)

st.title("📐 True Body Comp: The Triangulation Engine")
st.markdown("""
**Koncept:** Vi använder "Sensor Fusion" för att hitta din sanna komposition. 
Vi triangulerar data från **Garmin** (Impedans), **Navy Seal-formeln** (Måttband) och **RFM** (Relative Fat Mass).
Resultatet är en "Consensus-kurva" som är mer exakt än någon av källorna enskilt.
""")

# ==========================================
# 2. DATAHANTERING (PARSING)
# ==========================================
def parse_garmin_custom_format(file_content):
    lines = file_content.splitlines()
    data_rows = []
    current_date_str = None
    header_found = False
    headers = []
    
    # Hantera svenska månader (både kort och lång form, gemener/versaler)
    month_map = {
        'maj': 'May', 'okt': 'Oct', 'feb': 'Feb', 'mar': 'Mar', 
        'apr': 'Apr', 'jun': 'Jun', 'jul': 'Jul', 'aug': 'Aug', 
        'sep': 'Sep', 'nov': 'Nov', 'dec': 'Dec', 'jan': 'Jan',
        'juni': 'Jun', 'juli': 'Jul', 'mars': 'Mar', 'april': 'Apr'
    }
    
    for line in lines:
        line = line.strip()
        if not line: continue
        
        if not header_found:
            if "Vikt" in line or "Weight" in line:
                headers = [h.strip() for h in line.split(',')]
                header_found = True
            continue
            
        # Datumrad: Leta efter mönster som "13 Feb 2026" eller "13 februari 2026"
        if re.search(r'"?\s*\d+\s+[A-Za-zåäöÅÄÖ]+\s+\d+', line):
            current_date_str = line.replace('"', '').replace(',', '').strip()
            # Loopa igenom map och ersätt (case insensitive)
            lower_date = current_date_str.lower()
            for swe, eng in month_map.items():
                if swe in lower_date:
                    # Ersätt den svenska delen med engelsk (bevara versalisering någorlunda)
                    current_date_str = re.sub(swe, eng, current_date_str, flags=re.IGNORECASE)
            continue
            
        if header_found and current_date_str and ',' in line and any(c.isdigit() for c in line):
            parts = [p.strip() for p in line.split(',')]
            row_data = {}
            for i, header in enumerate(headers):
                if i < len(parts):
                    row_data[header] = parts[i]
            
            time_val = row_data.get('Tid', row_data.get('Time', ''))
            time_val = time_val.replace('fm', 'AM').replace('em', 'PM').replace('FM', 'AM').replace('EM', 'PM')
            row_data['FullDate'] = f"{current_date_str} {time_val}"
            data_rows.append(row_data)

    return pd.DataFrame(data_rows) if data_rows else None

def clean_and_map_columns(df):
    df.columns = df.columns.str.strip().str.replace('"', '').str.replace("'", "")
    
    column_mapping = {
        'weight_kg': ['Weight', 'Vikt', 'Weight (kg)', 'Vikt (kg)'],
        'bone_kg': ['Bone Mass', 'Benmassa', 'Benmassa (kg)'],
        'muscle_kg': ['Skeletal Muscle Mass', 'Muskelmassa', 'Skelettmuskelmassa', 'Muscle Mass'],
        'fat_pct': ['Body Fat', 'Kroppsfett', 'Fett', 'Body Fat (%)'],
        'water_pct': ['Body Water', 'Vatten', 'Kroppsvatten', 'Vatten (%)', 'Vatten i kroppen'],
        'Date': ['FullDate', 'Date', 'Datum', 'Tid', 'Time']
    }

    new_df = pd.DataFrame()
    for internal_name, possible_names in column_mapping.items():
        for col in df.columns:
            if any(p.lower() == col.lower() for p in possible_names):
                new_df[internal_name] = df[col]
                break
    
    if 'Date' in new_df.columns:
        new_df['Date'] = pd.to_datetime(new_df['Date'], errors='coerce')
        new_df = new_df.dropna(subset=['Date']).sort_values('Date')

    for col in ['weight_kg', 'bone_kg', 'muscle_kg', 'fat_pct', 'water_pct']:
        if col in new_df.columns:
            s = new_df[col].astype(str).str.replace(r'[^\d,.-]', '', regex=True).str.replace(',', '.')
            new_df[col] = pd.to_numeric(s, errors='coerce')
            
    if 'water_pct' not in new_df.columns: new_df['water_pct'] = 55.0

    return new_df.dropna(subset=['weight_kg'])

# ==========================================
# 3. KÄRNLOGIK: TRIANGULERING
# ==========================================
def calculate_navy_fat(height_cm, waist_cm, neck_cm, hip_cm=0, gender='Man'):
    """
    US Navy Method Formula.
    """
    if gender == 'Man':
        return 495 / (1.0324 - 0.19077 * np.log10(waist_cm - neck_cm) + 0.15456 * np.log10(height_cm)) - 450
    else:
        # Kvinnor: (Midja + Höft - Hals)
        # Om höft saknas (0), gissa att höft är midja * 1.15 (grov uppskattning)
        if hip_cm == 0: hip_cm = waist_cm * 1.15
        return 495 / (1.29579 - 0.35004 * np.log10(waist_cm + hip_cm - neck_cm) + 0.22100 * np.log10(height_cm)) - 450

def calculate_rfm(height_cm, waist_cm, gender='Man'):
    """
    Relative Fat Mass (RFM).
    """
    if gender == 'Man':
        return 64 - (20 * (height_cm / waist_cm))
    else:
        return 76 - (20 * (height_cm / waist_cm))

def run_triangulation(df, measurements, height_cm, gender='Man', tape_weight=0.7):
    df = df.sort_values('Date').reset_index(drop=True)
    
    # --- STEG 1: BERÄKNA EXTERNA MODELLER ---
    m_df = measurements.sort_values('Date').copy()
    
    # Initiera kolumner
    df['Waist_cm'] = np.nan
    df['Neck_cm'] = np.nan
    df['Hip_cm'] = np.nan
    
    # Mappa mätningar till närmaste datum i df
    for idx, row in m_df.iterrows():
        if df.empty: break
        nearest_idx = (df['Date'] - row['Date']).abs().idxmin()
        df.at[nearest_idx, 'Waist_cm'] = row['Waist']
        df.at[nearest_idx, 'Neck_cm'] = row['Neck']
        df.at[nearest_idx, 'Hip_cm'] = row.get('Hip', 0)
    
    # Interpolera
    df['Waist_cm'] = df['Waist_cm'].interpolate(method='linear', limit_direction='both')
    df['Neck_cm'] = df['Neck_cm'].interpolate(method='linear', limit_direction='both')
    df['Hip_cm'] = df['Hip_cm'].interpolate(method='linear', limit_direction='both')
    
    # Fallbacks om inga mätningar finns alls
    last_waist = m_df['Waist'].iloc[-1] if not m_df.empty else 90
    last_neck = m_df['Neck'].iloc[-1] if not m_df.empty else 40
    last_hip = m_df['Hip'].iloc[-1] if 'Hip' in m_df.columns and not m_df.empty else 100
    
    df['Waist_cm'] = df['Waist_cm'].fillna(last_waist)
    df['Neck_cm'] = df['Neck_cm'].fillna(last_neck)
    df['Hip_cm'] = df['Hip_cm'].fillna(last_hip)
    
    # Beräkna modellerna
    df['Navy_Fat_Pct'] = df.apply(lambda x: calculate_navy_fat(height_cm, x['Waist_cm'], x['Neck_cm'], x['Hip_cm'], gender), axis=1)
    df['RFM_Fat_Pct'] = df.apply(lambda x: calculate_rfm(height_cm, x['Waist_cm'], gender), axis=1)
    
    # --- STEG 2: SYNTES (SENSOR FUSION) ---
    
    # Consensus Model: Hur mycket litar vi på Navy vs RFM?
    # Navy är generellt bättre om man har nackmått.
    df['Model_Consensus'] = (df['Navy_Fat_Pct'] * 0.8) + (df['RFM_Fat_Pct'] * 0.2)
    
    # Jämna ut Garmins rådata (High Frequency Noise Removal)
    df['Garmin_Smoothed'] = df['fat_pct'].ewm(span=7).mean()
    
    # Beräkna Bias (Offset)
    # Bias = Garmin - Consensus
    df['Bias_Offset'] = df['Garmin_Smoothed'] - df['Model_Consensus']
    
    # Jämna ut Biasen så att vi inte hoppar vilt när vi lägger in en ny mätpunkt
    # 'tape_weight' avgör hur snabbt vi dras mot måttbandet.
    # Om tape_weight är hög, litar vi stenhårt på måttbandets nivå.
    smoothed_bias = df['Bias_Offset'].rolling(window=14, min_periods=1).mean()
    
    # --- THE FINAL FORMULA ---
    # Vi tar Garmins "kurvform" (dagsförändringar) men justerar den till Måttbandets "nivå".
    # Genom att dra av Biaset, flyttar vi Garmins kurva upp/ner så den matchar måttbandet.
    df['Consensus_Fat_Pct'] = df['fat_pct'] - smoothed_bias
    
    # Beräkna kilon
    df['Consensus_Fat_kg'] = df['weight_kg'] * (df['Consensus_Fat_Pct'] / 100)
    df['Lean_Mass_kg'] = df['weight_kg'] - df['Consensus_Fat_kg']

    return df

# ==========================================
# 4. UI & STATE
# ==========================================
if 'data' not in st.session_state: st.session_state.data = None

# Initiera databas för mätningar och säkerställ att nya kolumner finns
if 'measurements' not in st.session_state: 
    # Datum, Midja, Hals, Höft
    st.session_state.measurements = pd.DataFrame(columns=['Date', 'Waist', 'Neck', 'Hip'])
else:
    # Migration för existerande session state (om 'Hip' saknas)
    if 'Hip' not in st.session_state.measurements.columns:
        st.session_state.measurements['Hip'] = 0

with st.sidebar:
    st.header("1. Dataimport")
    uploaded_file = st.file_uploader("Garmin CSV", type=['csv'])
    if uploaded_file:
        content = uploaded_file.getvalue().decode('utf-8', errors='replace')
        raw_input = parse_garmin_custom_format(content)
        if raw_input is None: 
            uploaded_file.seek(0)
            raw_input = pd.read_csv(uploaded_file, skiprows=20)
        st.session_state.data = clean_and_map_columns(raw_input)
    
    st.divider()
    st.header("2. Fysiska Data")
    height = st.number_input("Din Längd (cm)", 150, 220, 180)
    gender = st.radio("Kön", ["Man", "Kvinna"])
    
    st.header("3. Måttband (Ankare)")
    st.info("Lägg till mätningar för att kalibrera AI:n.")
    
    with st.form("tape_measure"):
        m_date = st.date_input("Datum", datetime.now())
        m_waist = st.number_input("Midjemått (cm)", 50, 150, 90)
        m_neck = st.number_input("Halsmått (cm)", 20, 60, 40)
        # FIXAT: min_value är nu 0 för att tillåta standardvärdet 0 (frivilligt)
        m_hip = st.number_input("Höftmått (cm) [Frivilligt för män]", 0, 150, 0)
        
        if st.form_submit_button("Spara Mätning"):
            new_m = pd.DataFrame([{
                'Date': pd.to_datetime(m_date), 
                'Waist': m_waist, 
                'Neck': m_neck,
                'Hip': m_hip
            }])
            st.session_state.measurements = pd.concat([st.session_state.measurements, new_m]).drop_duplicates(subset='Date', keep='last').sort_values('Date')
            st.success("Sparat!")
            st.rerun()
            
    if not st.session_state.measurements.empty:
        st.caption("Sparade mätningar:")
        st.dataframe(st.session_state.measurements, hide_index=True)
        if st.button("Rensa mätningar"):
            st.session_state.measurements = pd.DataFrame(columns=['Date', 'Waist', 'Neck', 'Hip'])
            st.rerun()

# --- MAIN ---
if st.session_state.data is not None:
    df = st.session_state.data
    meas = st.session_state.measurements
    
    # Om inga mätningar finns, varna
    if meas.empty:
        st.warning("⚠️ Du har inte lagt in några måttbandsvärden än! Algoritmen kör på standardvärden (Midja 90cm) vilket gör trianguleringen gissningsbaserad. Lägg in minst en mätning i menyn.")
    
    # Kör Triangulering
    processed_df = run_triangulation(df, meas, height, gender)
    
    latest = processed_df.iloc[-1]
    prev = processed_df.iloc[-2] if len(processed_df) > 1 else latest
    
    # --- CONSENSUS BOX ---
    bias = latest['Bias_Offset']
    
    st.markdown(f"""
    <div class="consensus-box">
        <h3>🤖 Triangulerings-Analys</h3>
        <p>Algoritmen har vägt samman dina datakällor:</p>
        <ul>
            <li><b>Garmin (Impedans):</b> {latest['fat_pct']:.1f}% (Avviker med {bias:+.1f}%)</li>
            <li><b>Måttband (Navy):</b> {latest['Navy_Fat_Pct']:.1f}%</li>
            <li><b>RFM (Statistik):</b> {latest['RFM_Fat_Pct']:.1f}%</li>
        </ul>
        <p><b>SLUTSATS:</b> Din sanna fettprocent är sannolikt <b>{latest['Consensus_Fat_Pct']:.1f}%</b>.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    # KPIer
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Vikt", f"{latest['weight_kg']:.1f} kg")
    c2.metric("SANN Fett %", f"{latest['Consensus_Fat_Pct']:.1f} %", f"{(latest['Consensus_Fat_Pct']-prev['Consensus_Fat_Pct']):.1f} %")
    c3.metric("Lean Mass (Muskler+Ben)", f"{latest['Lean_Mass_kg']:.1f} kg", f"{(latest['Lean_Mass_kg']-prev['Lean_Mass_kg']):.1f} kg")
    c4.metric("Bias-korrigering", f"{bias:.1f} %", help="Negativt = Garmin visar för högt, Positivt = Garmin visar för lågt")

    # --- VISUALISERING ---
    tab1, tab2 = st.tabs(["🎯 Triangulering", "📏 Måttbands-historik"])
    
    with tab1:
        st.subheader("Konvergens av modeller")
        fig = make_subplots()
        
        # Garmin (Gray background noise)
        fig.add_trace(go.Scatter(x=processed_df['Date'], y=processed_df['fat_pct'],
                                 name="Garmin (Rådata)", line=dict(color="gray", width=1, dash='dot'), opacity=0.3))
        
        # Navy (Anchor)
        fig.add_trace(go.Scatter(x=processed_df['Date'], y=processed_df['Navy_Fat_Pct'],
                                 name="Navy Method (Trend)", line=dict(color="#1976d2", width=2)))
        
        # CONSENSUS (The Truth)
        fig.add_trace(go.Scatter(x=processed_df['Date'], y=processed_df['Consensus_Fat_Pct'],
                                 name="★ CONSENSUS (Sanningen)", line=dict(color="#2e7d32", width=5)))

        fig.update_layout(title="Jakten på Sanningen", yaxis_title="Fettprocent (%)", hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)
        
    with tab2:
        st.subheader("Interpolerade Mått")
        st.markdown("Tabellen visar hur dina mått interpoleras mellan mätningarna.")
        cols_to_show = ['Date', 'weight_kg', 'Waist_cm', 'Neck_cm']
        if gender == 'Kvinna' or meas['Hip'].sum() > 0:
            cols_to_show.append('Hip_cm')
        cols_to_show.extend(['Navy_Fat_Pct', 'Consensus_Fat_Pct'])
        
        st.dataframe(processed_df[cols_to_show].sort_values('Date', ascending=False))

else:
    st.info("👈 Ladda upp CSV och ange dina mått för att starta motorn.")