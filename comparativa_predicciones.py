import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils import mm_ss_to_seconds, seconds_to_mm_ss, get_points
from physiological_functions import (
    speed, anaerobic_speed_reserve, aerobic_speed, 
    vo2, vo2max_calc
)
from scipy.optimize import fsolve

# Cargar tablas y convertir tiempos a segundos
mens_scoring_tables_df = pd.read_csv('mens_scoring_tables.csv', index_col=0)
womens_scoring_tables_df = pd.read_csv('womens_scoring_tables.csv', index_col=0)

# Convertir tiempos de formato mm:ss.ss a segundos
mens_400m_seconds = mens_scoring_tables_df["400m"].apply(mm_ss_to_seconds)
mens_800m_seconds = mens_scoring_tables_df["800m"].apply(mm_ss_to_seconds)
mens_1500m_seconds = mens_scoring_tables_df["1500m"].apply(mm_ss_to_seconds)

womens_400m_seconds = womens_scoring_tables_df["400m"].apply(mm_ss_to_seconds)
womens_800m_seconds = womens_scoring_tables_df["800m"].apply(mm_ss_to_seconds)
womens_1500m_seconds = womens_scoring_tables_df["1500m"].apply(mm_ss_to_seconds)

# Configuración de Streamlit
st.set_page_config(page_title="Comparativa de Predicciones", layout="wide")
st.title("Comparativa: Race Predictor vs ASR Model")
st.markdown("Compara las predicciones de 1500m entre el modelo estadístico (World Athletics) y el modelo fisiológico (ASR)")

# Sidebar para inputs
st.sidebar.header("Parámetros de entrada")

# Selección de género
gender = st.sidebar.radio("Selecciona el género:", ('Masculino', 'Femenino'))

if gender == 'Masculino':
    fastest_800 = mens_800m_seconds[1400]
    slowest_800 = mens_800m_seconds[1]
    default_t800 = 120.0
else:
    fastest_800 = womens_800m_seconds[1400]
    slowest_800 = womens_800m_seconds[1]
    default_t800 = 150.0

# Input para t800 (este será el Trial 2 del ASR)
t800_fixed = st.sidebar.number_input(
    "Tiempo de 800m (segundos) - Trial 2 para ASR", 
    min_value=float(fastest_800), 
    max_value=float(slowest_800), 
    value=default_t800,
    step=0.1
)

st.sidebar.markdown("---")
st.sidebar.markdown("### Selección de tiempo 400m")
st.sidebar.info("Usa el gráfico para explorar diferentes tiempos de 400m y ver su impacto en las predicciones")

# Rango para t400 basado en race_predictor_2
t400_min = 0.82 * t800_fixed / 2 
t400_max = 0.96 * t800_fixed / 2 
t400_selected = st.sidebar.slider(
    "Tiempo de 400m (segundos) - Trial 1 para ASR",
    min_value=float(t400_min),
    max_value=float(t400_max),
    value=float((t400_min + t400_max) / 2),
    step=0.1
)

# --- CÁLCULOS RACE PREDICTOR ---
# Generar datos para el modelo estadístico
t400_range = np.linspace(t400_min, t400_max, 1000)
t1500_rp = (t800_fixed - t400_range * 1.2) / 0.216  # Race Predictor formula

# Calcular ratios para clasificación de perfiles
pace_400 = t400_range / 400
pace_800 = t800_fixed / 800
pace_1500 = t1500_rp / 1500

ratio_400_800 = pace_400 / pace_800
ratio_800_1500 = pace_800 / pace_1500

if gender == 'Masculino':
    ratios_400_800 = mens_scoring_tables_df["400m"].apply(mm_ss_to_seconds) / 400 / (mens_scoring_tables_df["800m"].apply(mm_ss_to_seconds) / 800)
    ratios_800_1500 = mens_scoring_tables_df["800m"].apply(mm_ss_to_seconds) / 800 / (mens_scoring_tables_df["1500m"].apply(mm_ss_to_seconds) / 1500)
    t800_fixed_points = get_points(t800_fixed, mens_800m_seconds)
    wa_ratio_400_800 = ratios_400_800.loc[t800_fixed_points]
    wa_ratio_800_1500 = ratios_800_1500.loc[t800_fixed_points]
    points_400 = np.array([get_points(t, mens_400m_seconds) if get_points(t, mens_400m_seconds) is not None else 0 for t in t400_range])
    points_1500 = np.array([get_points(t, mens_1500m_seconds) if get_points(t, mens_1500m_seconds) is not None else 0 for t in t1500_rp])
else:
    ratios_400_800 = womens_scoring_tables_df["400m"].apply(mm_ss_to_seconds) / 400 / (womens_scoring_tables_df["800m"].apply(mm_ss_to_seconds) / 800)
    ratios_800_1500 = womens_scoring_tables_df["800m"].apply(mm_ss_to_seconds) / 800 / (womens_scoring_tables_df["1500m"].apply(mm_ss_to_seconds) / 1500)
    t800_fixed_points = get_points(t800_fixed, womens_800m_seconds)
    wa_ratio_400_800 = ratios_400_800.loc[t800_fixed_points]
    wa_ratio_800_1500 = ratios_800_1500.loc[t800_fixed_points]
    points_400 = np.array([get_points(t, womens_400m_seconds) if get_points(t, womens_400m_seconds) is not None else 0 for t in t400_range])
    points_1500 = np.array([get_points(t, womens_1500m_seconds) if get_points(t, womens_1500m_seconds) is not None else 0 for t in t1500_rp])

# Calcular predicción de 1500m para el t400 seleccionado usando Race Predictor
t1500_rp_selected = (t800_fixed - t400_selected * 1.2) / 0.216

# Determinar el color/perfil del punto seleccionado
point_differences = np.abs(points_400 - points_1500)
equilibrium_idx = np.argmin(point_differences)
equilibrium_ratio_400_800 = ratio_400_800[equilibrium_idx]
equilibrium_ratio_800_1500 = ratio_800_1500[equilibrium_idx]

limit_400_specialist = (equilibrium_ratio_400_800 + wa_ratio_400_800) / 2
limit_1500_specialist = (equilibrium_ratio_800_1500 + wa_ratio_800_1500) / 2

# Determinar colores para toda la curva
colors = []
color_names = []
for i in range(len(ratio_400_800)):
    if ratio_400_800[i] < wa_ratio_400_800:
        colors.append('red')
        color_names.append('400m o menos')
    elif ratio_800_1500[i] > wa_ratio_800_1500:
        colors.append('green')
        color_names.append('1500m o más')
    elif ratio_400_800[i] < limit_400_specialist:
        colors.append('orange')
        color_names.append('800m-400m')
    elif ratio_800_1500[i] > limit_1500_specialist:
        colors.append('cyan')
        color_names.append('800m-1500m')
    else:
        colors.append('blue')
        color_names.append('800m')

# --- CÁLCULOS ASR ---
try:
    distance_1 = 400  # fijo
    distance_2 = 800  # fijo
    time_1_sec = t400_selected
    time_2_sec = t800_fixed
    
    ASR = anaerobic_speed_reserve(distance_1, time_1_sec, distance_2, time_2_sec)
    aerobic_speed_val = aerobic_speed(distance_2, time_2_sec, ASR)
    
    # Calcular predicción de 1500m usando ASR
    def equation_1500(t):
        if t <= 0:
            return float('inf')
        vel = speed(aerobic_speed_val, aerobic_speed_val + ASR, t)
        return vel * t - 1500
    
    initial_guess = 1500 / (aerobic_speed_val + ASR/2)
    t1500_asr_selected = fsolve(equation_1500, initial_guess)[0]
    
    # Calcular velocidad a 1500m
    vel_1500_asr = speed(aerobic_speed_val, aerobic_speed_val + ASR, t1500_asr_selected)
    
    vo2max_val = vo2(aerobic_speed_val * 60)
    
    asr_calculation_success = True
except Exception as e:
    asr_calculation_success = False
    error_message = str(e)

# --- CREAR GRÁFICOS ---
# Crear subplots: Race Predictor a la izquierda, Comparación a la derecha
fig = make_subplots(
    rows=1, cols=2,
    subplot_titles=('Race Predictor Model (World Athletics)', 
                   'Comparación de Predicciones para 1500m'),
    specs=[[{"type": "scatter"}, {"type": "bar"}]],
    column_widths=[0.6, 0.4]
)

# Gráfico 1: Race Predictor (izquierda)
t400_formatted = [seconds_to_mm_ss(t) for t in t400_range]
t1500_formatted = [seconds_to_mm_ss(t) for t in t1500_rp]

fig.add_trace(go.Scatter(
    x=t400_range,
    y=t1500_rp,
    mode='markers+lines',
    marker=dict(
        color=colors,
        size=6,
        line=dict(width=0)
    ),
    line=dict(
        color='rgba(128,128,128,0.3)',
        width=1
    ),
    customdata=list(zip(
        t400_formatted,
        t1500_formatted,
        [f"{r:.4f}" for r in ratio_400_800],
        [f"{r:.4f}" for r in ratio_800_1500],
        color_names
    )),
    hovertemplate=(
        '<b>Perfil</b>: %{customdata[4]}<br>'
        '<b>t400</b>: %{customdata[0]}<br>'
        '<b>t1500</b>: %{customdata[1]}<br>'
        '<b>Ratio 400/800</b>: %{customdata[2]}<br>'
        '<b>Ratio 800/1500</b>: %{customdata[3]}<extra></extra>'
    ),
    showlegend=False,
    name='Curva RP'
), row=1, col=1)

# Marcar el punto seleccionado en Race Predictor
fig.add_trace(go.Scatter(
    x=[t400_selected],
    y=[t1500_rp_selected],
    mode='markers',
    marker=dict(
        size=15,
        color='black',
        symbol='star',
        line=dict(width=2, color='yellow')
    ),
    name='Punto seleccionado',
    showlegend=True,
    hovertemplate='<b>Punto seleccionado</b><br>' +
                 '<b>t400</b>: ' + seconds_to_mm_ss(t400_selected) + '<br>' +
                 '<b>t1500 (RP)</b>: ' + seconds_to_mm_ss(t1500_rp_selected) + '<extra></extra>'
), row=1, col=1)

# Gráfico 2: Comparación de barras (derecha)
if asr_calculation_success:
    comparison_data = {
        'Modelo': ['Race Predictor', 'ASR Model'],
        'Tiempo 1500m (seg)': [t1500_rp_selected, t1500_asr_selected],
        'Tiempo formatted': [seconds_to_mm_ss(t1500_rp_selected), seconds_to_mm_ss(t1500_asr_selected)],
        'Color': ['#636EFA', '#EF553B']
    }
    
    fig.add_trace(go.Bar(
        x=comparison_data['Modelo'],
        y=comparison_data['Tiempo 1500m (seg)'],
        text=comparison_data['Tiempo formatted'],
        textposition='outside',
        marker_color=comparison_data['Color'],
        showlegend=False,
        hovertemplate='<b>%{x}</b><br>' +
                     '<b>Tiempo 1500m</b>: %{text}<br>' +
                     '<b>Segundos</b>: %{y:.2f}<extra></extra>'
    ), row=1, col=2)
    
    # Calcular diferencia
    diff_seconds = t1500_asr_selected - t1500_rp_selected
    diff_formatted = f"+{abs(diff_seconds):.2f}s" if diff_seconds > 0 else f"-{abs(diff_seconds):.2f}s"
else:
    # Mostrar solo Race Predictor si ASR falla
    fig.add_trace(go.Bar(
        x=['Race Predictor'],
        y=[t1500_rp_selected],
        text=[seconds_to_mm_ss(t1500_rp_selected)],
        textposition='outside',
        marker_color=['#636EFA'],
        showlegend=False
    ), row=1, col=2)

# Actualizar layouts
fig.update_xaxes(title_text="Tiempo 400m (mm:ss)", row=1, col=1)
fig.update_yaxes(title_text="Tiempo 1500m (mm:ss)", row=1, col=1)
fig.update_xaxes(title_text="Modelo", row=1, col=2)
fig.update_yaxes(title_text="Tiempo 1500m (segundos)", row=1, col=2)

# Formato de ticks para el gráfico Race Predictor
y_min = int(np.floor(t1500_rp.min() / 10) * 10)
y_max = int(np.ceil(t1500_rp.max() / 10) * 10)
y_ticks = np.arange(y_min, y_max + 1, 10)
fig.update_yaxes(
    tickmode='array',
    tickvals=y_ticks,
    ticktext=[seconds_to_mm_ss(t) for t in y_ticks],
    row=1, col=1
)

x_min = int(np.floor(t400_min))
x_max = int(np.ceil(t400_max))
x_ticks = np.arange(x_min, x_max + 1, 1)
fig.update_xaxes(
    tickmode='array',
    tickvals=x_ticks,
    ticktext=[seconds_to_mm_ss(t) for t in x_ticks],
    row=1, col=1
)

fig.update_layout(
    height=600,
    showlegend=True,
    template='plotly_white',
    hovermode='closest'
)

# Mostrar gráfico
st.plotly_chart(fig, use_container_width=True)

# --- TABLA DE COMPARACIÓN ---
st.markdown("---")
st.subheader("Resumen de Predicciones")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### Tiempos de entrada")
    st.metric("400m (Trial 1)", seconds_to_mm_ss(t400_selected))
    st.metric("800m (Trial 2)", seconds_to_mm_ss(t800_fixed))
    if gender == 'Masculino':
        st.metric("Puntos WA (800m)", f"{t800_fixed_points}")

with col2:
    st.markdown("### Race Predictor")
    st.metric("Predicción 1500m", seconds_to_mm_ss(t1500_rp_selected))
    st.metric("Ecuación", "t800 = 1.2·t400 + 0.216·t1500")
    if gender == 'Masculino':
        points_1500_rp = get_points(t1500_rp_selected, mens_1500m_seconds)
        if points_1500_rp:
            st.metric("Puntos WA (1500m)", f"{points_1500_rp}")
    else:
        points_1500_rp = get_points(t1500_rp_selected, womens_1500m_seconds)
        if points_1500_rp:
            st.metric("Puntos WA (1500m)", f"{points_1500_rp}")

with col3:
    if asr_calculation_success:
        st.markdown("### ASR Model")
        st.metric("Predicción 1500m", seconds_to_mm_ss(t1500_asr_selected))
        st.metric("Diferencia vs RP", diff_formatted)
        st.metric("Velocidad 1500m", f"{vel_1500_asr * 3.6:.2f} km/h")
    else:
        st.markdown("### ASR Model")
        st.error(f"Error en el cálculo: {error_message}")

# --- INFORMACIÓN ADICIONAL ASR ---
if asr_calculation_success:
    st.markdown("---")
    st.subheader("Detalles del modelo ASR")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("ASR", f"{ASR * 3.6:.2f} km/h")
    with col2:
        st.metric("Velocidad Aeróbica", f"{aerobic_speed_val * 3.6:.2f} km/h")
    with col3:
        st.metric("Vel. Máx. Sprint", f"{(aerobic_speed_val + ASR) * 3.6:.2f} km/h")
    with col4:
        st.metric("VO2max (est.)", f"{vo2max_val:.1f} ml/kg/min")

# --- EXPLICACIÓN ---
st.markdown("---")
st.markdown("""
### Sobre esta comparativa

Esta herramienta compara dos métodos para predecir el rendimiento en 1500m:

1. **Race Predictor (World Athletics)**: Modelo estadístico basado en las tablas de puntos de World Athletics. 
   Usa la ecuación empírica `t800 = 1.2·t400 + 0.216·t1500` para relacionar los tiempos de 400m, 800m y 1500m.

2. **ASR Model (Anaerobic Speed Reserve)**: Modelo fisiológico que usa la reserva de velocidad anaeróbica.
   Calcula la velocidad esperada basándose en el decay exponencial de la capacidad anaeróbica.

**Cómo usar:**
- Ingresa tu tiempo de 800m (se usa como Trial 2 para ASR)
- Ajusta el slider de 400m para explorar diferentes escenarios (Trial 1 para ASR)
- Observa cómo ambos modelos predicen tu tiempo de 1500m
- Compara las predicciones para entender tu perfil fisiológico vs estadístico
""")
