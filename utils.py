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
    return f"{mm}:{ss:05.2f}"

def get_points(time, scoring_table_event):
    valid_times = scoring_table_event[scoring_table_event >= time]
    if not valid_times.empty:
        return valid_times.index[0]

