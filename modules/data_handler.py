import re

import numpy as np
import pandas as pd

# --- PARSING & STÄDNING ---
def parse_garmin_custom_csv(file_content):
    lines = file_content.splitlines()
    data_rows = []
    current_date_str = None
    header_found = False
    headers = []
    
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
            
        if re.search(r'"?\s*\d+\s+[A-Za-zåäöÅÄÖ]+\s+\d+', line):
            current_date_str = line.replace('"', '').replace(',', '').strip()
            lower_date = current_date_str.lower()
            for swe, eng in month_map.items():
                if swe in lower_date:
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
    """Standardiserar kolumnnamn oavsett källa (CSV eller API)."""
    df.columns = df.columns.str.strip().str.replace('"', '').str.replace("'", "")
    
    # HÄR VAR FELET: Jag har lagt till de "rena" namnen (t.ex. weight_kg) i listan
    # så att de identifieras och behålls.
    column_mapping = {
        'weight_kg': ['weight_kg', 'Weight', 'Vikt', 'Weight (kg)', 'Vikt (kg)'],
        'bone_kg': ['bone_kg', 'Bone Mass', 'Benmassa', 'Benmassa (kg)'],
        'muscle_kg': ['muscle_kg', 'Skeletal Muscle Mass', 'Muskelmassa', 'Skelettmuskelmassa', 'Muscle Mass'],
        'fat_pct': ['fat_pct', 'Body Fat', 'Kroppsfett', 'Fett', 'Body Fat (%)'],
        'water_pct': ['water_pct', 'Body Water', 'Vatten', 'Kroppsvatten', 'Vatten (%)', 'Vatten i kroppen'],
        'Date': ['Date', 'FullDate', 'Datum', 'Tid', 'Time']
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

    # Tvätta numeriska värden
    for col in ['weight_kg', 'bone_kg', 'muscle_kg', 'fat_pct', 'water_pct']:
        if col in new_df.columns:
            if new_df[col].dtype == object:
                s = new_df[col].astype(str).str.replace(r'[^\d,.-]', '', regex=True).str.replace(',', '.')
                new_df[col] = pd.to_numeric(s, errors='coerce')
            
    if 'water_pct' not in new_df.columns: new_df['water_pct'] = 55.0

    # Säkerhetskoll
    if 'weight_kg' not in new_df.columns:
        return pd.DataFrame() # Returnera tomt istället för att krascha

    return new_df.dropna(subset=['weight_kg'])