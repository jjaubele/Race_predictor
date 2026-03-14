import pandas as pd
import numpy as np
import plotly.graph_objects as go
import streamlit as st
from scipy.optimize import fsolve
from utils import seconds_to_mm_ss, minutes_to_hhmmss, mmin_to_kmh, mmin_to_pace
from physiological_functions import percent_max, velocity, vo2max_calc

# Configuración de Streamlit
st.set_page_config(page_title="VO2max Velocity vs Time", layout="wide")
st.title("Velocidad vs Tiempo para diferentes VO2max")
st.markdown("Esta aplicación muestra la relación entre velocidad y tiempo de esfuerzo para diferentes valores de VO2max")

# Sidebar para controles
st.sidebar.header("Parámetros")

# Opción para elegir cómo definir el VO2max
vo2max_mode = st.sidebar.radio(
    "Definir VO2max:",
    ["Valor directo", "Calcular desde marca"],
    index=0
)

if vo2max_mode == "Valor directo":
    # Slider para VO2max
    vo2max_value = st.sidebar.slider(
        "VO2max (ml/kg/min)",
        min_value=30.0,
        max_value=100.0,
        value=60.0,
        step=0.1
    )
else:
    # Calcular VO2max desde una marca
    st.sidebar.markdown("**Ingresa tu mejor marca:**")
    
    # Input para distancia
    distance_input = st.sidebar.number_input(
        "Distancia (metros)",
        min_value=100,
        max_value=50000,
        value=5000,
        step=100
    )
    
    # Input para tiempo en formato hh:mm:ss
    col1, col2, col3 = st.sidebar.columns(3)
    with col1:
        hours = st.number_input("Horas", min_value=0, max_value=10, value=0, step=1)
    with col2:
        minutes = st.number_input("Minutos", min_value=0, max_value=59, value=20, step=1)
    with col3:
        seconds = st.number_input("Segundos", min_value=0, max_value=59, value=0, step=1)
    
    # Convertir tiempo a minutos
    time_in_minutes = hours * 60 + minutes + seconds / 60
    
    # Calcular VO2max
    if time_in_minutes > 0:
        vo2max_value = vo2max_calc(distance_input, time_in_minutes)
        st.sidebar.success(f"VO2max calculado: **{vo2max_value:.1f}** ml/kg/min")
    else:
        vo2max_value = 60.0
        st.sidebar.warning("Ingresa un tiempo válido")

# Rango de tiempo
time_range = np.linspace(6, 180, 1000)  # De 6 a 180 minutos

# Crear figura
fig = go.Figure()

# Mostrar la curva seleccionada
velocity_values = []
pace_values = []
vo2_values = []
time_formatted = []
distance_values = []

for t in time_range:
    vo2_at_time = vo2max_value * percent_max(t)
    vel = velocity(vo2_at_time)
    vel_kmh = mmin_to_kmh(vel)
    velocity_values.append(vel_kmh)
    pace_values.append(mmin_to_pace(vel))
    vo2_values.append(vo2_at_time)
    time_formatted.append(minutes_to_hhmmss(t))
    # Calcular distancia en metros: tiempo (min) * velocidad (m/min)
    distance_values.append(t * vel)

fig.add_trace(go.Scatter(
    x=time_range,
    y=velocity_values,
    mode='lines',
    name=f'VO2max = {vo2max_value:.2f}',
    line=dict(width=3, color='#1f77b4'),
    hovertemplate='<b>Distancia:</b> %{customdata[4]:.0f} m<br>' +
                 '<b>Tiempo:</b> %{customdata[0]}<br>' +
                 '<b>Velocidad:</b> %{y:.2f} km/h<br>' +
                 '<b>Pace:</b> %{customdata[1]}<br>' +
                 '<b>VO2:</b> %{customdata[2]:.2f} ml/kg/min<br>' +
                 '<b>%VO2max:</b> %{customdata[3]:.1f}%<extra></extra>',
    customdata=[[time_fmt, seconds_to_mm_ss(pace*60), vo2_val, (vo2_val/vo2max_value)*100, dist] 
               for time_fmt, pace, vo2_val, dist in zip(time_formatted, pace_values, vo2_values, distance_values)]
))

# Agregar marcadores para distancias específicas
distances = [3000, 5000, 10000, 21097, 42195]  # metros
distance_labels = ['3K', '5K', '10K', '21K', '42K']

marker_times = []
marker_velocities = []
marker_labels = []
marker_customdata = []

# Diccionario para almacenar todos los datos de distancias (para la tabla)
all_distance_data = {}

for dist, label in zip(distances, distance_labels):
    # Encontrar el punto en la curva donde tiempo * velocidad = distancia
    # velocidad en km/h, tiempo en minutos, distancia en metros
    # Necesitamos: t (min) * v (m/min) = dist (m)
    # v (m/min) = v_kmh * 1000 / 60
    # Entonces: t * v_kmh * 1000 / 60 = dist
    # t * v_kmh = dist * 60 / 1000
    
    found = False
    for i, (t, v_kmh) in enumerate(zip(time_range, velocity_values)):
        v_mmin = v_kmh * 1000 / 60  # convertir km/h a m/min
        distance_covered = t * v_mmin
        
        if i > 0 and distance_covered >= dist:
            # Interpolación lineal para encontrar el punto exacto
            t_prev = time_range[i-1]
            v_prev = velocity_values[i-1]
            v_mmin_prev = v_prev * 1000 / 60
            dist_prev = t_prev * v_mmin_prev
            
            # Interpolación
            alpha = (dist - dist_prev) / (distance_covered - dist_prev)
            t_exact = t_prev + alpha * (t - t_prev)
            v_exact = v_prev + alpha * (v_kmh - v_prev)
            
            # Calcular datos adicionales para el punto
            vo2_at_time = vo2max_value * percent_max(t_exact)
            vel_mmin = velocity(vo2_at_time)
            pace = mmin_to_pace(vel_mmin)
            
            # Guardar para marcadores (solo si está en el rango del gráfico)
            marker_times.append(t_exact)
            marker_velocities.append(v_exact)
            marker_labels.append(label)
            marker_customdata.append([
                minutes_to_hhmmss(t_exact),
                seconds_to_mm_ss(pace*60),
                vo2_at_time,
                (vo2_at_time/vo2max_value)*100,
                label
            ])
            
            # Guardar para la tabla
            all_distance_data[label] = {
                'dist': dist,
                'time': t_exact,
                'velocity': v_exact,
                'pace': pace,
                'vo2': vo2_at_time
            }
            found = True
            break
    
    # Si no se encontró (fuera del rango), calcular usando fsolve
    if not found:
        def equation(time):
            if time <= 0:
                return float('inf')
            vo2_at_time = vo2max_value * percent_max(time)
            vel = velocity(vo2_at_time)
            return vel * time - dist
        
        try:
            # Estimar tiempo inicial basado en la distancia
            initial_guess = dist / 200  # Asumiendo ~200 m/min como velocidad inicial
            time_solution = fsolve(equation, initial_guess)[0]
            
            # Calcular velocidad y otros datos
            vo2_at_time = vo2max_value * percent_max(time_solution)
            vel_mmin = velocity(vo2_at_time)
            vel_kmh = mmin_to_kmh(vel_mmin)
            pace = mmin_to_pace(vel_mmin)
            
            # Guardar para la tabla (no para marcadores)
            all_distance_data[label] = {
                'dist': dist,
                'time': time_solution,
                'velocity': vel_kmh,
                'pace': pace,
                'vo2': vo2_at_time
            }
        except:
            # Si falla, usar valores por defecto
            pass

# Agregar marcadores de distancia
if marker_times:
    fig.add_trace(go.Scatter(
        x=marker_times,
        y=marker_velocities,
        mode='markers+text',
        name='Distancias Notables',
        marker=dict(size=10, color='red', symbol='circle'),
        text=marker_labels,
        textposition='top center',
        textfont=dict(size=10, color='red'),
        hoverinfo='skip'
    ))
# Calcular el tiempo al 100% VO2max
time_100_vo2max = fsolve(lambda t: percent_max(t) - 1.0, 5)[0]

# Agregar líneas verticales para umbrales
fig.add_vline(x=time_100_vo2max, line_dash="dash", line_color="red", line_width=2,
              annotation_text="100% VO2max", annotation_position="top")
fig.add_vline(x=60, line_dash="dash", line_color="green", line_width=2,
              annotation_text="LT2", annotation_position="top")

# Configurar layout
fig.update_layout(
    xaxis_title="Tiempo (minutos)",
    yaxis_title="Velocidad (km/h)",
    hovermode='x unified',
    template="plotly_white",
    height=600,
    legend=dict(
        yanchor="top",
        y=0.99,
        xanchor="right",
        x=0.99
    )
)

# Mostrar gráfico
st.plotly_chart(fig, use_container_width=True)

# Tabla de predicciones
st.markdown("---")
st.subheader("Predicciones de rendimiento")
    
# Crear datos para la tabla
table_data = []

# Agregar distancias estándar usando all_distance_data
for label in distance_labels:
    if label in all_distance_data:
        data = all_distance_data[label]
        table_data.append({
            'Prueba': label,
            'Distancia (m)': f"{data['dist']:,}",
            'Tiempo': minutes_to_hhmmss(data['time']),
            'Velocidad (km/h)': f"{data['velocity']:.2f}",
            'Velocidad_num': data['velocity'],  # Para ordenar
            'Pace (min/km)': seconds_to_mm_ss(data['pace']*60),
            '%VO2max': f"{(data['vo2']/vo2max_value)*100:.1f}%"
        })
    
# Agregar 100% VO2max
vo2_at_100 = vo2max_value
vel_100 = velocity(vo2_at_100)
vel_100_kmh = mmin_to_kmh(vel_100)
pace_100 = mmin_to_pace(vel_100)
dist_100 = time_100_vo2max * vel_100

table_data.append({
    'Prueba': '100% VO2max',
    'Distancia (m)': f"{dist_100:,.0f}",
    'Tiempo': minutes_to_hhmmss(time_100_vo2max),
    'Velocidad (km/h)': f"{vel_100_kmh:.2f}",
    'Velocidad_num': vel_100_kmh,  # Para ordenar
    'Pace (min/km)': seconds_to_mm_ss(pace_100*60),
    '%VO2max': "100.0%"
})

# Agregar LT2 (60 minutos)
vo2_at_lt2 = vo2max_value * percent_max(60)
vel_lt2 = velocity(vo2_at_lt2)
vel_lt2_kmh = mmin_to_kmh(vel_lt2)
pace_lt2 = mmin_to_pace(vel_lt2)
dist_lt2 = 60 * vel_lt2

table_data.append({
    'Prueba': 'LT2 (60 min)',
    'Distancia (m)': f"{dist_lt2:,.0f}",
    'Tiempo': minutes_to_hhmmss(60),
    'Velocidad (km/h)': f"{vel_lt2_kmh:.2f}",
    'Velocidad_num': vel_lt2_kmh,  # Para ordenar
    'Pace (min/km)': seconds_to_mm_ss(pace_lt2*60),
    '%VO2max': f"{(vo2_at_lt2/vo2max_value)*100:.1f}%"
})

# Crear DataFrame y ordenar por velocidad (de más rápido a más lento)
df = pd.DataFrame(table_data)
df = df.sort_values('Velocidad_num', ascending=False)
df = df.drop(columns=['Velocidad_num'])  # Eliminar columna auxiliar
df = df.reset_index(drop=True)
st.dataframe(df, use_container_width=True, hide_index=True)
