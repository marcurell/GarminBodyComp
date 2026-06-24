from garminconnect import Garmin
import pandas as pd
from datetime import date, timedelta
import os

# Mapp för att spara inloggningstokens
TOKEN_DIR = ".garmin_tokens"
TOKEN_PATH = os.path.join(TOKEN_DIR, "garmin_tokens")

def init_garmin_client(email, password):
    try:
        # Försök med sparade tokens om de finns
        if os.path.exists(TOKEN_PATH):
            try:
                garmin = Garmin()
                garmin.login(TOKEN_PATH)
                return garmin, None
            except Exception as e:
                print(f"Token-fel, försöker logga in manuellt: {e}")

        # Ny inloggning
        garmin = Garmin(email, password)
        garmin.login()

        # Spara tokens om möjligt (fungerar inte alltid i molnmiljö)
        try:
            os.makedirs(TOKEN_DIR, exist_ok=True)
            garmin.garth.dump(TOKEN_PATH)
        except Exception:
            pass

        return garmin, None

    except Exception as e:
        return None, str(e)

def fetch_garmin_data(email, password, days_back=30):
    try:
        client, error = init_garmin_client(email, password)
        if not client:
            return None, f"Login Error: {error}"
        
        start_date = date.today() - timedelta(days=days_back)
        end_date = date.today()
        
        stats = client.get_body_composition(start_date.isoformat(), end_date.isoformat())
        
        data_rows = []
        if 'dateWeightList' in stats:
            for entry in stats['dateWeightList']:
                # --- SÄKER LOGIK ---
                # Hämta värden, men om de är None, sätt dem till 0 direkt.
                
                # Vikt
                w = entry.get('weight')
                if w is None: w = 0.0
                else: w = float(w)
                
                # Konvertera gram till kg om det behövs
                if w > 200: w = w / 1000.0
                
                # Benmassa
                b = entry.get('boneMass')
                if b is None: b = 0.0
                else: b = float(b)
                
                if b > 20: b = b / 1000.0
                
                # Muskelmassa
                m = entry.get('muscleMass')
                if m is None: m = 0.0
                else: m = float(m)
                
                if m > 100: m = m / 1000.0

                # Fett %
                f = entry.get('bodyFat')
                if f is None: f = 0.0
                else: f = float(f)
                
                # Vatten %
                wa = entry.get('bodyWater')
                if wa is None: wa = 0.0
                else: wa = float(wa)

                row = {
                    'Date': pd.to_datetime(entry.get('date') or entry.get('startDate')),
                    'weight_kg': w,
                    'bone_kg': b,
                    'muscle_kg': m,
                    'fat_pct': f,
                    'water_pct': wa
                }
                
                # Spara bara om vi faktiskt har en vikt
                if w > 0:
                    data_rows.append(row)
                
        df = pd.DataFrame(data_rows)
        
        if df.empty:
            return None, "Ingen data hittades."
            
        return df, None

    except Exception as e:
        import traceback
        traceback.print_exc()
        return None, f"API Error: {str(e)}"