import numpy as np
import pandas as pd

def calculate_navy_fat(height_cm, waist_cm, neck_cm, hip_cm=0, gender='Man'):
    """US Navy Method Formula."""
    if gender == 'Man':
        return 495 / (1.0324 - 0.19077 * np.log10(waist_cm - neck_cm) + 0.15456 * np.log10(height_cm)) - 450
    else:
        if hip_cm == 0: hip_cm = waist_cm * 1.15
        return 495 / (1.29579 - 0.35004 * np.log10(waist_cm + hip_cm - neck_cm) + 0.22100 * np.log10(height_cm)) - 450

def calculate_rfm(height_cm, waist_cm, gender='Man'):
    """Relative Fat Mass (RFM)."""
    if gender == 'Man':
        return 64 - (20 * (height_cm / waist_cm))
    else:
        return 76 - (20 * (height_cm / waist_cm))

def run_triangulation(df, measurements, height_cm, gender='Man'):
    """
    Kärnlogiken: Kombinerar Garmin-data med måttbandsdata.
    """
    # Arbeta på en kopia och sortera
    df = df.copy().sort_values('Date').reset_index(drop=True)
    m_df = measurements.copy().sort_values('Date')
    
    # Initiera kolumner för interpolering
    df['Waist_cm'] = np.nan
    df['Neck_cm'] = np.nan
    df['Hip_cm'] = np.nan
    
    # Mappa mätningar till närmaste datum
    for idx, row in m_df.iterrows():
        if df.empty: break
        # Hitta index för närmaste datum
        nearest_idx = (df['Date'] - row['Date']).abs().idxmin()
        df.at[nearest_idx, 'Waist_cm'] = row['Waist']
        df.at[nearest_idx, 'Neck_cm'] = row['Neck']
        df.at[nearest_idx, 'Hip_cm'] = row.get('Hip', 0)
    
    # Interpolera linjärt mellan mätpunkter
    df['Waist_cm'] = df['Waist_cm'].interpolate(method='linear', limit_direction='both')
    df['Neck_cm'] = df['Neck_cm'].interpolate(method='linear', limit_direction='both')
    df['Hip_cm'] = df['Hip_cm'].interpolate(method='linear', limit_direction='both')
    
    # Fallback-värden (om inga mätningar finns alls eller i början/slutet om interpolation missar)
    # Vi använder sista kända mätningen som fallback, eller default.
    last_waist = m_df['Waist'].iloc[-1] if not m_df.empty else 90
    last_neck = m_df['Neck'].iloc[-1] if not m_df.empty else 40
    last_hip = m_df['Hip'].iloc[-1] if 'Hip' in m_df.columns and not m_df.empty else 100
    
    df['Waist_cm'] = df['Waist_cm'].fillna(last_waist)
    df['Neck_cm'] = df['Neck_cm'].fillna(last_neck)
    df['Hip_cm'] = df['Hip_cm'].fillna(last_hip)
    
    # Beräkna modellerna
    df['Navy_Fat_Pct'] = df.apply(lambda x: calculate_navy_fat(height_cm, x['Waist_cm'], x['Neck_cm'], x['Hip_cm'], gender), axis=1)
    df['RFM_Fat_Pct'] = df.apply(lambda x: calculate_rfm(height_cm, x['Waist_cm'], gender), axis=1)
    
    # --- SENSOR FUSION ---
    
    # Consensus Model: 80% Navy, 20% RFM
    df['Model_Consensus'] = (df['Navy_Fat_Pct'] * 0.8) + (df['RFM_Fat_Pct'] * 0.2)
    
    # Garmin Smoothing (Ta bort dagsbrus)
    df['Garmin_Smoothed'] = df['fat_pct'].ewm(span=7).mean()
    
    # Bias Calculation (Offset mellan Garmin och Consensus)
    df['Bias_Offset'] = df['Garmin_Smoothed'] - df['Model_Consensus']
    
    # Jämna ut Biasen (så den inte hoppar när man lägger in nya mått)
    smoothed_bias = df['Bias_Offset'].rolling(window=14, min_periods=1).mean()
    
    # Final Formula: Garmin Daily Variation - Smoothed Bias Level
    df['Consensus_Fat_Pct'] = df['fat_pct'] - smoothed_bias
    
    # Beräkna massa
    df['Consensus_Fat_kg'] = df['weight_kg'] * (df['Consensus_Fat_Pct'] / 100)
    df['Lean_Mass_kg'] = df['weight_kg'] - df['Consensus_Fat_kg']

    return df