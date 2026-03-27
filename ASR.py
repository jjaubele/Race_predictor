import pandas as pd
import numpy as np
import plotly.graph_objects as go
import streamlit as st
from scipy.optimize import fsolve
from utils import seconds_to_mm_ss, mm_ss_to_seconds, get_points
from physiological_functions import (
    speed, anaerobic_speed_reserve, aerobic_speed)

# Cargar tablas de puntajes World Athletics
mens_scoring_tables_df = pd.read_csv('mens_scoring_tables.csv', index_col=0)
womens_scoring_tables_df = pd.read_csv('womens_scoring_tables.csv', index_col=0)

# Convertir tiempos a segundos para las distancias relevantes
mens_100m_seconds = mens_scoring_tables_df.get("100m", pd.Series()).apply(mm_ss_to_seconds) if "100m" in mens_scoring_tables_df.columns else None
mens_200m_seconds = mens_scoring_tables_df.get("200m", pd.Series()).apply(mm_ss_to_seconds) if "200m" in mens_scoring_tables_df.columns else None
mens_300m_seconds = mens_scoring_tables_df.get("300m", pd.Series()).apply(mm_ss_to_seconds) if "300m" in mens_scoring_tables_df.columns else None
mens_400m_seconds = mens_scoring_tables_df.get("400m", pd.Series()).apply(mm_ss_to_seconds) if "400m" in mens_scoring_tables_df.columns else None
mens_600m_seconds = mens_scoring_tables_df.get("600m", pd.Series()).apply(mm_ss_to_seconds) if "600m" in mens_scoring_tables_df.columns else None
mens_800m_seconds = mens_scoring_tables_df.get("800m", pd.Series()).apply(mm_ss_to_seconds) if "800m" in mens_scoring_tables_df.columns else None
mens_1000m_seconds = mens_scoring_tables_df.get("1000m", pd.Series()).apply(mm_ss_to_seconds) if "1000m" in mens_scoring_tables_df.columns else None
mens_1500m_seconds = mens_scoring_tables_df.get("1500m", pd.Series()).apply(mm_ss_to_seconds) if "1500m" in mens_scoring_tables_df.columns else None
mens_1mile_seconds = mens_scoring_tables_df.get("Mile", pd.Series()).apply(mm_ss_to_seconds) if "Mile" in mens_scoring_tables_df.columns else None
mens_2000m_seconds = mens_scoring_tables_df.get("2000m", pd.Series()).apply(mm_ss_to_seconds) if "2000m" in mens_scoring_tables_df.columns else None

womens_100m_seconds = womens_scoring_tables_df.get("100m", pd.Series()).apply(mm_ss_to_seconds) if "100m" in womens_scoring_tables_df.columns else None
womens_200m_seconds = womens_scoring_tables_df.get("200m", pd.Series()).apply(mm_ss_to_seconds) if "200m" in womens_scoring_tables_df.columns else None
womens_300m_seconds = womens_scoring_tables_df.get("300m", pd.Series()).apply(mm_ss_to_seconds) if "300m" in womens_scoring_tables_df.columns else None
womens_400m_seconds = womens_scoring_tables_df.get("400m", pd.Series()).apply(mm_ss_to_seconds) if "400m" in womens_scoring_tables_df.columns else None
womens_600m_seconds = womens_scoring_tables_df.get("600m", pd.Series()).apply(mm_ss_to_seconds) if "600m" in womens_scoring_tables_df.columns else None
womens_800m_seconds = womens_scoring_tables_df.get("800m", pd.Series()).apply(mm_ss_to_seconds) if "800m" in womens_scoring_tables_df.columns else None
womens_1000m_seconds = womens_scoring_tables_df.get("1000m", pd.Series()).apply(mm_ss_to_seconds) if "1000m" in womens_scoring_tables_df.columns else None
womens_1500m_seconds = womens_scoring_tables_df.get("1500m", pd.Series()).apply(mm_ss_to_seconds) if "1500m" in womens_scoring_tables_df.columns else None
womens_1mile_seconds = womens_scoring_tables_df.get("Mile", pd.Series()).apply(mm_ss_to_seconds) if "Mile" in womens_scoring_tables_df.columns else None
womens_2000m_seconds = womens_scoring_tables_df.get("2000m", pd.Series()).apply(mm_ss_to_seconds) if "2000m" in womens_scoring_tables_df.columns else None

# Ratios de referencia basados en tablas WA (mismo criterio que race_predictor_2.py)
mens_ratios_400_800 = (mens_400m_seconds / 400) / (mens_800m_seconds / 800) if mens_400m_seconds is not None and mens_800m_seconds is not None else None
mens_ratios_800_1500 = (mens_800m_seconds / 800) / (mens_1500m_seconds / 1500) if mens_800m_seconds is not None and mens_1500m_seconds is not None else None
womens_ratios_400_800 = (womens_400m_seconds / 400) / (womens_800m_seconds / 800) if womens_400m_seconds is not None and womens_800m_seconds is not None else None
womens_ratios_800_1500 = (womens_800m_seconds / 800) / (womens_1500m_seconds / 1500) if womens_800m_seconds is not None and womens_1500m_seconds is not None else None

# Configuración de Streamlit
st.set_page_config(page_title="ASR Velocity vs Time", layout="wide")
st.title("Predictor de marcas de mediofondo")
st.markdown("Esta aplicación simula mediante una curva exponencial negativa la perdida de reserva de velocidad anaeróbica (ASR) entre los 20 segundos y los 6 minutos.")

# Sidebar para controles
st.sidebar.header("Parámetros")

# Selección de género
gender = st.sidebar.radio("Género:", ('Masculino', 'Femenino'))

st.sidebar.markdown("### Trial 1 (más corto)")
col1, col2 = st.sidebar.columns(2)
with col1:
    distance_1 = st.number_input(
        "Distancia 1 (m)",
        min_value=200,
        max_value=2000,
        value=400,
        step=1
    )
with col2:
    time_1_sec = st.number_input(
        "Tiempo 1 (seg)",
        min_value=20.0,
        max_value=360.0,
        value=54.0,
        step=0.1
    )

st.sidebar.markdown("### Trial 2 (más largo)")
col3, col4 = st.sidebar.columns(2)
with col3:
    distance_2 = st.number_input(
        "Distancia 2 (m)",
        min_value=200,
        max_value=2000,
        value=1500,
        step=1
    )
with col4:
    time_2_sec = st.number_input(
        "Tiempo 2 (seg)",
        min_value=20.0,
        max_value=360.0,
        value=250.0,
        step=0.1
    )

# Validar que trial 1 sea más corto que trial 2
if time_1_sec >= time_2_sec:
    st.sidebar.error("⚠️ El Trial 1 debe ser más corto (menor tiempo) que el Trial 2")
    st.stop()


def classify_runner_profile(ratio_400_800, ratio_800_1500, wa_ratio_400_800, wa_ratio_800_1500,
                            limit_400_specialist, limit_1500_specialist):
    """Clasifica con el mismo criterio de race_predictor_2.py."""
    if ratio_400_800 < wa_ratio_400_800:
        return "400m o menos", "Mejor desempeño relativo en 400m que en 800m."
    if ratio_800_1500 > wa_ratio_800_1500:
        return "1500m o más", "Mejor desempeño relativo en 1500m que en 800m."
    if ratio_400_800 < limit_400_specialist:
        return "800-400", "Perfil de 800m con tendencia a velocidad."
    if ratio_800_1500 > limit_1500_specialist:
        return "800-1500", "Perfil de 800m con tendencia a resistencia."
    return "Especialista de 800", "Perfil equilibrado, especialista puro de 800m."

# Calcular ASR y velocidad aeróbica
try:
    ASR = anaerobic_speed_reserve(distance_1, time_1_sec, distance_2, time_2_sec)
    aerobic_speed_val = aerobic_speed(distance_2, time_2_sec, ASR)

    if aerobic_speed_val <= 0:
        st.sidebar.error("La velocidad aeróbica calculada no es válida. Revisa los trials ingresados.")
        st.stop()
    
except Exception as e:
    st.sidebar.error(f"Error en el cálculo: {str(e)}")
    st.stop()

# Rango de tiempo (20 segundos a 360 segundos)
time_range = np.linspace(20, 360, 1000)

# Crear figura con dos ejes Y
from plotly.subplots import make_subplots
fig = make_subplots(specs=[[{"secondary_y": True}]])

# Calcular velocidades para cada tiempo
velocity_values = []
velocity_kmh_values = []
pace_values = []
time_formatted = []
distance_values = []

for t in time_range:
    vel = speed(aerobic_speed_val, aerobic_speed_val + ASR, t)
    velocity_values.append(vel)
    vel_kmh = vel * 3.6  # convertir m/s a km/h
    velocity_kmh_values.append(vel_kmh)
    time_formatted.append(seconds_to_mm_ss(t))
    distance_values.append(vel * t)
    
    # Pace en min/km
    if vel > 0:
        pace = 1000 / (vel * 60)  # minutos por kilómetro
        pace_values.append(pace)
    else:
        pace_values.append(0)

# Agregar la curva principal de velocidad (eje Y primario)
fig.add_trace(go.Scatter(
    x=time_range,
    y=velocity_kmh_values,
    mode='lines',
    name='Velocidad',
    line=dict(width=3, color='#1f77b4'),
    hovertemplate='<b>Tiempo:</b> %{customdata[0]}<br>' +
                 '<b>Distancia:</b> %{customdata[4]:.0f} m<br>' +
                 '<b>Velocidad:</b> %{y:.2f} km/h<br>' +
                 '<b>Velocidad:</b> %{customdata[5]:.2f} m/s<br>' +
                 '<b>Pace:</b> %{customdata[1]}<extra></extra>',
    customdata=[[time_fmt, seconds_to_mm_ss(pace*60) if pace > 0 else "N/A", 0, 0, dist, vel] 
               for time_fmt, pace, dist, vel in zip(time_formatted, pace_values, distance_values, velocity_values)]
), secondary_y=False)

# Agregar marcadores para los trials ingresados
fig.add_trace(go.Scatter(
    x=[time_1_sec, time_2_sec],
    y=[distance_1/time_1_sec * 3.6, distance_2/time_2_sec * 3.6],
    mode='markers+text',
    name='Trials',
    marker=dict(size=12, color='red', symbol='circle'),
    text=['Trial 1', 'Trial 2'],
    textposition='top center',
    textfont=dict(size=12, color='red'),
    hovertemplate='<b>%{text}</b><br>' +
                 '<b>Tiempo:</b> %{customdata[0]}<br>' +
                 '<b>Distancia:</b> %{customdata[1]:.0f} m<br>' +
                 '<b>Velocidad:</b> %{y:.2f} km/h<extra></extra>',
    customdata=[[seconds_to_mm_ss(time_1_sec), distance_1],
                [seconds_to_mm_ss(time_2_sec), distance_2]]
), secondary_y=False)

# Agregar marcadores para distancias específicas
distances = [200, 300, 400, 600, 800, 1000, 1500, 1609.34, 2000]  # 1 milla = 1609.34 m
distance_labels = ['200m', '300m', '400m', '600m', '800m', '1000m', '1500m', '1 milla', '2000m']

marker_times = []
marker_velocities = []
marker_labels = []
marker_customdata = []

# Diccionario para almacenar todos los datos de distancias
all_distance_data = {}

for dist, label in zip(distances, distance_labels):
    # Función para resolver: speed * time = distance
    def equation(t):
        if t <= 0:
            return float('inf')
        vel = speed(aerobic_speed_val, aerobic_speed_val + ASR, t)
        return vel * t - dist
    
    try:
        # Estimar tiempo inicial
        initial_guess = dist / (aerobic_speed_val + ASR/2)
        time_solution = fsolve(equation, initial_guess)[0]
        
        # Verificar que esté en el rango
        if 10 <= time_solution <= 360:
            vel = speed(aerobic_speed_val, aerobic_speed_val + ASR, time_solution)
            vel_kmh = vel * 3.6
            pace = 1000 / (vel * 60) if vel > 0 else 0
            
            marker_times.append(time_solution)
            marker_velocities.append(vel_kmh)
            marker_labels.append(label)
            
            all_distance_data[label] = {
                'dist': dist,
                'time': time_solution,
                'velocity': vel,
                'velocity_kmh': vel_kmh,
                'pace': pace
            }
    except:
        pass

# Clasificación de perfil con el mismo criterio que race_predictor_2.py
runner_profile = "No disponible"
profile_description = "No fue posible calcular el perfil con el criterio de 400/800/1500."
ratio_400_800_actual = None
ratio_800_1500_actual = None
wa_ratio_400_800 = None
wa_ratio_800_1500 = None

if all(k in all_distance_data for k in ['400m', '800m', '1500m']):
    t400 = all_distance_data['400m']['time']
    t800 = all_distance_data['800m']['time']
    t1500 = all_distance_data['1500m']['time']

    if t400 > 0 and t800 > 0 and t1500 > 0:
        ratio_400_800_actual = (t400 / 400) / (t800 / 800)
        ratio_800_1500_actual = (t800 / 800) / (t1500 / 1500)

        if gender == 'Masculino':
            ratios_400_800 = mens_ratios_400_800
            ratios_800_1500 = mens_ratios_800_1500
            scoring_400 = mens_400m_seconds
            scoring_800 = mens_800m_seconds
            scoring_1500 = mens_1500m_seconds
        else:
            ratios_400_800 = womens_ratios_400_800
            ratios_800_1500 = womens_ratios_800_1500
            scoring_400 = womens_400m_seconds
            scoring_800 = womens_800m_seconds
            scoring_1500 = womens_1500m_seconds

        t800_points = get_points(t800, scoring_800) if scoring_800 is not None else None

        if (
            t800_points is not None and
            ratios_400_800 is not None and
            ratios_800_1500 is not None and
            t800_points in ratios_400_800.index and
            t800_points in ratios_800_1500.index
        ):
            wa_ratio_400_800 = ratios_400_800.loc[t800_points]
            wa_ratio_800_1500 = ratios_800_1500.loc[t800_points]

            t400_min = 0.82 * t800 / 2
            t400_max = 0.96 * t800 / 2
            t400_range = np.linspace(t400_min, t400_max, 1000)
            t1500_values_eq = (t800 - t400_range * 1.2) / 0.216

            pace_400_eq = t400_range / 400
            pace_800_eq = t800 / 800
            pace_1500_eq = t1500_values_eq / 1500
            ratio_400_800_eq = pace_400_eq / pace_800_eq
            ratio_800_1500_eq = pace_800_eq / pace_1500_eq

            points_400_eq = np.array([
                get_points(t, scoring_400) if get_points(t, scoring_400) is not None else 0
                for t in t400_range
            ])
            points_1500_eq = np.array([
                get_points(t, scoring_1500) if get_points(t, scoring_1500) is not None else 0
                for t in t1500_values_eq
            ])

            point_differences = np.abs(points_400_eq - points_1500_eq)
            equilibrium_idx = np.argmin(point_differences)
            equilibrium_ratio_400_800 = ratio_400_800_eq[equilibrium_idx]
            equilibrium_ratio_800_1500 = ratio_800_1500_eq[equilibrium_idx]

            limit_400_specialist = (equilibrium_ratio_400_800 + wa_ratio_400_800) / 2
            limit_1500_specialist = (equilibrium_ratio_800_1500 + wa_ratio_800_1500) / 2

            runner_profile, profile_description = classify_runner_profile(
                ratio_400_800_actual,
                ratio_800_1500_actual,
                wa_ratio_400_800,
                wa_ratio_800_1500,
                limit_400_specialist,
                limit_1500_specialist
            )

# Agregar marcadores de distancias
if marker_times:
    fig.add_trace(go.Scatter(
        x=marker_times,
        y=marker_velocities,
        mode='markers+text',
        name='Distancias',
        marker=dict(size=10, color='green', symbol='diamond'),
        text=marker_labels,
        textposition='bottom center',
        textfont=dict(size=10, color='green'),
        hoverinfo='skip'
    ), secondary_y=False)

# Agregar líneas de referencia
fig.add_hline(y=aerobic_speed_val * 3.6, line_dash="dash", line_color="orange", line_width=2,
              annotation_text="Velocidad Aeróbica", annotation_position="left", secondary_y=False)
# Configurar layout
fig.update_xaxes(title_text="Tiempo (segundos)")
fig.update_yaxes(title_text="Velocidad (km/h)", secondary_y=False)

fig.update_layout(
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

# Crear datos para la tabla (vo2_aerobic_max ya fue calculado arriba)
table_data = []

# Mapeo de etiquetas de distancia a columnas de tabla de puntajes
distance_to_column = {
    '100m': ('100m', mens_100m_seconds if gender == 'Masculino' else womens_100m_seconds),
    '200m': ('200m', mens_200m_seconds if gender == 'Masculino' else womens_200m_seconds),
    '300m': ('300m', mens_300m_seconds if gender == 'Masculino' else womens_300m_seconds),
    '400m': ('400m', mens_400m_seconds if gender == 'Masculino' else womens_400m_seconds),
    '600m': ('600m', mens_600m_seconds if gender == 'Masculino' else womens_600m_seconds),
    '800m': ('800m', mens_800m_seconds if gender == 'Masculino' else womens_800m_seconds),
    '1000m': ('1000m', mens_1000m_seconds if gender == 'Masculino' else womens_1000m_seconds),
    '1500m': ('1500m', mens_1500m_seconds if gender == 'Masculino' else womens_1500m_seconds),
    '1 milla': ('1 Mile', mens_1mile_seconds if gender == 'Masculino' else womens_1mile_seconds),
    '2000m': ('2000m', mens_2000m_seconds if gender == 'Masculino' else womens_2000m_seconds)
}

# Agregar distancias
for label in distance_labels:
    if label in all_distance_data:
        data = all_distance_data[label]
        
        # Velocidad en m/min para cálculo de VO2
        vel_mmin = data['velocity'] * 60
        
        # Tiempo en minutos
        time_minutes = data['time'] / 60
        
        # Calcular puntos World Athletics
        wa_points = None
        if label in distance_to_column:
            col_name, scoring_table = distance_to_column[label]
            if scoring_table is not None and not scoring_table.empty:
                wa_points = get_points(data['time'], scoring_table)
        
        table_data.append({
            'Distancia': label,
            'Tiempo': seconds_to_mm_ss(data['time']),
            'Tiempo_num': data['time'],
            'Velocidad (km/h)': f"{data['velocity_kmh']:.2f}",
            'Pace (min/km)': seconds_to_mm_ss(data['pace']*60) if data['pace'] > 0 else 'N/A',
            'Puntos WA': wa_points if wa_points is not None else '-'
        })

# Ordenar por tiempo (de más rápido a más lento)
if table_data:
    df = pd.DataFrame(table_data)
    df = df.sort_values('Tiempo_num', ascending=True)
    df = df.drop(columns=['Tiempo_num'])
    df = df.reset_index(drop=True)
    st.dataframe(df, use_container_width=True, hide_index=True)

st.markdown("### Notas:")
st.markdown("- El modelo se ajusto haciendo uso de marcas de 400m, 800m y 1500m, por lo que los mejores resultados se obtienen con un trial 1 entre 400m y 800m, y un trial 2 entre 800m y 1500m.")
st.markdown("- Las interpolaciones (marcas entre trials) tienden a ser más precisas que las extrapolaciones (marcas fuera del rango de los trials). ")
st.markdown("- Si escoges distancias para los trials que sean muy cercanas entre sí (Ej: 1500m y milla), las predicciones para distancias más alejadas (Ej: 400m) serán extrapolaciones y podrían ser menos precisas.")
st.markdown("- Si haz corrido tiempos más rapidos que los indicados por la predicción, ingresa esos tiempos como trials para ver margen tu de mejora.")
st.markdown("- La predicción se basa en la suposición de que ambos trials son esfuerzos máximos realizados en un mismo estado de forma física (idealmente cercanos en el tiempo).")

# --- GRÁFICO DE PUNTOS WORLD ATHLETICS ---
st.markdown("---")
st.subheader("Puntos World Athletics por Distancia")

# Filtrar datos con puntos WA válidos
wa_data = []
for item in table_data:
    if item['Puntos WA'] != '-' and item['Puntos WA'] is not None:
        wa_data.append({
            'Distancia': item['Distancia'],
            'Puntos': item['Puntos WA'],
            'Tiempo': item['Tiempo']
        })

if wa_data:
    # Crear el gráfico de barras
    fig_wa = go.Figure()
    
    distances_list = [item['Distancia'] for item in wa_data]
    points_list = [item['Puntos'] for item in wa_data]
    times_list = [item['Tiempo'] for item in wa_data]
    
    fig_wa.add_trace(go.Bar(
        x=distances_list,
        y=points_list,
        marker=dict(
            color='#1f77b4',
            line=dict(color='rgba(0,0,0,0.3)', width=1)
        ),
        text=[f"{pts} pts" for pts in points_list],
        textposition='outside',
        textfont=dict(size=12, color='black'),
        hovertemplate='<b>%{x}</b><br>' +
                     '<b>Puntos WA:</b> %{y}<br>' +
                     '<b>Tiempo:</b> %{customdata}<extra></extra>',
        customdata=times_list
    ))
    
    # Configurar layout del gráfico
    fig_wa.update_layout(
        xaxis_title="Distancia",
        yaxis_title="Puntos World Athletics",
        yaxis=dict(
            range=[0, min(1450, max(points_list) * 1.1)],
            showgrid=True,
            gridwidth=1,
            gridcolor='LightGray'
        ),
        xaxis=dict(
            showgrid=False
        ),
        template="plotly_white",
        height=500,
        showlegend=False,
        hovermode='x'
    )
    
    # Agregar líneas de referencia para niveles
    fig_wa.add_hline(y=1200, line_dash="dash", line_color="green", line_width=1.5, annotation_position="right")
    fig_wa.add_hline(y=1000, line_dash="dash", line_color="lightgreen", line_width=1, annotation_position="right")
    fig_wa.add_hline(y=800, line_dash="dash", line_color="gold", line_width=1, annotation_position="right")
    fig_wa.add_hline(y=600, line_dash="dash", line_color="orange", line_width=1, annotation_position="right")
    
    st.plotly_chart(fig_wa, use_container_width=True)
else:
    st.warning("No hay datos de puntos World Athletics disponibles para las distancias predichas.")

st.markdown("### Perfil de corredor")
col_profile_1, col_profile_2, col_profile_3 = st.columns(3)
with col_profile_1:
    st.metric("Perfil", runner_profile)
with col_profile_2:
    st.metric("Ratio 400/800", f"{ratio_400_800_actual:.4f}" if ratio_400_800_actual is not None else "N/A")
with col_profile_3:
    st.metric("Ratio 800/1500", f"{ratio_800_1500_actual:.4f}" if ratio_800_1500_actual is not None else "N/A")

st.caption(profile_description)

# Mostrar valores límites de cada tipo de perfil
if wa_ratio_400_800 is not None and wa_ratio_800_1500 is not None:
    with st.expander("Valores límites de perfiles", expanded=False):
        st.write("**Ratio de velocidades para marcas técnicas equivalentes (WA)**")
        col_wa1, col_wa2 = st.columns(2)
        with col_wa1:
            st.metric("Ratio 400/800", f"{wa_ratio_400_800:.4f}")
        with col_wa2:
            st.metric("Ratio 800/1500", f"{wa_ratio_800_1500:.4f}")
        
        st.write("---")
        st.write("**Límites de clasificación:**")
        col_lim1, col_lim2, col_lim3, col_lim4 = st.columns(4)
        with col_lim1:
            st.metric("Ratio 400/800 de equilibrio", f"{equilibrium_ratio_400_800:.4f}" if 'equilibrium_ratio_400_800' in locals() else "N/A")
        with col_lim2:
            st.metric("Ratio 800/1500 de equilibrio", f"{equilibrium_ratio_800_1500:.4f}" if 'equilibrium_ratio_800_1500' in locals() else "N/A")
        with col_lim3:
            st.metric("Ratio 400/800 de velocidad", f"{limit_400_specialist:.4f}" if 'limit_400_specialist' in locals() else "N/A")
        with col_lim4:
            st.metric("Ratio 800/1500 de resistencia", f"{limit_1500_specialist:.4f}" if 'limit_1500_specialist' in locals() else "N/A")
        
        st.write("---")
        st.write("**Criterios de clasificación:**")
        st.markdown(f"""
        - **400m o menos**: Ratio 400/800 < {wa_ratio_400_800:.4f}, mejor marca técnica en 400m que en 800m.
        - **800-400**: Ratio 400/800 < {limit_400_specialist:.4f}, desempeño considerablemente mejor en 400m que en 1500m, tendencia a velocidad.
        - **Especialista de 800**: Marcas técnicas equilibradas, sin tendencia fuerte a velocidad o resistencia.
        - **800-1500**: Ratio 800/1500 > {limit_1500_specialist:.4f}, desempeño considerablemente mejor en 1500m que en 400m, tendencia a resistencia.
        - **1500m o más**: Ratio 800/1500 > {wa_ratio_800_1500:.4f}, mejor marca técnica en 1500m que en 800m.
        """)

st.markdown("### Formulas utilizadas:")
st.latex(r'''ASR = \frac{V_1 - V_2}{e^{-Kt_1} - e^{-Kt_2}}''')
st.markdown("Donde:")
st.markdown("- $ASR$: Reserva de velocidad anaeróbica")
st.markdown("- $V_1$: Velocidad en el primer trial")
st.markdown("- $V_2$: Velocidad en el segundo trial")
st.markdown("- $t_1$: Tiempo del primer trial")
st.markdown("- $t_2$: Tiempo del segundo trial")
st.markdown("- $K$: Constante de decaimiento (1/150s)")
st.latex(r'''V_a = V_2 - ASR \cdot e^{-Kt_2}''')
st.markdown("Donde:")
st.markdown("- $V_a$: Velocidad aeróbica")
st.latex(r'''V(t) = V_a + ASR \cdot e^{-Kt}''')
st.markdown("Donde:")
st.markdown("- $V(t)$: Velocidad en función del tiempo")
