import pandas as pd
import numpy as np

# Función para convertir mm:ss.ss a segundos
def mm_ss_to_seconds(mm_ss):
    if pd.isna(mm_ss) or mm_ss == '':
        return np.nan
    
    mm_ss_str = str(mm_ss).strip()
    
    # Si no contiene ':', asumimos que ya está en segundos
    if ':' not in mm_ss_str:
        try:
            return float(mm_ss_str)
        except ValueError:
            return np.nan
    
    # Si contiene ':', procesamos como mm:ss.ss
    try:
        parts = mm_ss_str.split(':')
        if len(parts) != 2:
            return np.nan
        mm = int(parts[0])
        ss = float(parts[1])
        return mm * 60 + ss
    except (ValueError, IndexError):
        return np.nan
    
# Función para convertir segundos a mm:ss.ss
def seconds_to_mm_ss(seconds):
    mm = int(seconds // 60)
    ss = seconds % 60
    # Manejar el caso donde ss se redondea a 60
    if ss >= 59.995:  # Se redondeará a 60.00
        mm += 1
        ss = 0.0
    return f"{mm}:{ss:05.2f}"

# Función para convertir minutos a hh:mm:ss
def minutes_to_hhmmss(minutes):
    total_seconds = minutes * 60
    hours = int(total_seconds // 3600)
    remaining_seconds = total_seconds % 3600
    mins = int(remaining_seconds // 60)
    secs = int(remaining_seconds % 60)
    return f"{hours:02d}:{mins:02d}:{secs:02d}"

def mmin_to_kmh(velocity_mmin):
    return velocity_mmin * 60 / 1000

def kmh_to_mmin(velocity_kmh):
    return velocity_kmh * 1000 / 60

def mmin_to_pace(velocity_mmin):
    return 1000 / velocity_mmin  # minutes per km

def pace_to_mmin(pace):
    return 1000 / pace  # m/min

def kmh_to_pace(velocity_kmh):
    velocity_mmin = kmh_to_mmin(velocity_kmh)
    return mmin_to_pace(velocity_mmin)

def pace_to_kmh(pace):
    velocity_mmin = pace_to_mmin(pace)
    return mmin_to_kmh(velocity_mmin)

def get_points(time, scoring_table_event):
    valid_times = scoring_table_event[scoring_table_event >= time]
    if not valid_times.empty:
        return valid_times.index[0]

