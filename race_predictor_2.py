import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from utils import mm_ss_to_seconds, seconds_to_mm_ss, get_points

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

# Calcular ratios usando tiempos en segundos
mens_ratios_400_800 = (mens_400m_seconds / 400) / (mens_800m_seconds / 800)
mens_ratios_800_1500 = (mens_800m_seconds / 800) / (mens_1500m_seconds / 1500)

womens_ratios_400_800 = (womens_400m_seconds / 400) / (womens_800m_seconds / 800)
womens_ratios_800_1500 = (womens_800m_seconds / 800) / (womens_1500m_seconds / 1500)

# Título de la aplicación
st.title("Perfiles de Tiempo de Carrera - 800m")

# Sidebar para inputs
st.sidebar.header("Parámetros")

# Selección de género
gender = st.sidebar.radio("Selecciona el género:", ('Masculino', 'Femenino'))

if gender == 'Masculino':
    ratios_400_800 = mens_ratios_400_800
    ratios_800_1500 = mens_ratios_800_1500
    fastest_800 = mens_800m_seconds[1400]
    slowest_800 = mens_800m_seconds[1]
    default_t800 = 120.0
else:
    ratios_400_800 = womens_ratios_400_800
    ratios_800_1500 = womens_ratios_800_1500
    fastest_800 = womens_800m_seconds[1400]
    slowest_800 = womens_800m_seconds[1]
    default_t800 = 150.0

# Input para t800 fijo
t800_fixed = st.sidebar.number_input(
    "Tiempo objetivo de 800m (segundos)", 
    min_value=fastest_800, 
    max_value=slowest_800, 
    value=default_t800,
    step=1.0
)

# Rango para t400
t400_min = 0.82 * t800_fixed / 2 
t400_max = 0.96 * t800_fixed / 2 

# Generar datos
t400_range = np.linspace(t400_min, t400_max, 1000)
# Despejar t1500 de la ecuación: t800 = t400 * 1.2 + t1500 * 0.216
# t1500 = (t800 - t400 * 1.2) / 0.216
t1500_values = (t800_fixed - t400_range * 1.2) / 0.216

# Calcular ratios para cada punto
pace_400 = t400_range / 400  # segundos por metro
pace_800 = t800_fixed / 800
pace_1500 = t1500_values / 1500

ratio_400_800 = pace_400 / pace_800
ratio_800_1500 = pace_800 / pace_1500

if gender == 'Masculino':
    t800_fixed_points = get_points(t800_fixed, mens_800m_seconds)
    wa_ratio_400_800 = mens_ratios_400_800.loc[t800_fixed_points]
    wa_ratio_800_1500 = mens_ratios_800_1500.loc[t800_fixed_points]
    # Calcular puntos para cada tiempo de 400m y 1500m
    points_400 = np.array([get_points(t, mens_400m_seconds) if get_points(t, mens_400m_seconds) is not None else 0 for t in t400_range])
    points_1500 = np.array([get_points(t, mens_1500m_seconds) if get_points(t, mens_1500m_seconds) is not None else 0 for t in t1500_values])
else:
    t800_fixed_points = get_points(t800_fixed, womens_800m_seconds)
    wa_ratio_400_800 = womens_ratios_400_800.loc[t800_fixed_points]
    wa_ratio_800_1500 = womens_ratios_800_1500.loc[t800_fixed_points]
    # Calcular puntos para cada tiempo de 400m y 1500m
    points_400 = np.array([get_points(t, womens_400m_seconds) if get_points(t, womens_400m_seconds) is not None else 0 for t in t400_range])
    points_1500 = np.array([get_points(t, womens_1500m_seconds) if get_points(t, womens_1500m_seconds) is not None else 0 for t in t1500_values])

# Encontrar el punto de equilibrio puro (diferencia mínima de puntajes)
point_differences = np.abs(points_400 - points_1500)
equilibrium_idx = np.argmin(point_differences)
equilibrium_ratio_400_800 = ratio_400_800[equilibrium_idx]
equilibrium_ratio_800_1500 = ratio_800_1500[equilibrium_idx]

# Calcular límites como promedios entre equilibrio puro y ratios WA
limit_400_specialist = (equilibrium_ratio_400_800 + wa_ratio_400_800) / 2
limit_1500_specialist = (equilibrium_ratio_800_1500 + wa_ratio_800_1500) / 2

# Determinar el color para cada segmento (5 categorías)
# Rojo: mejor en 400m (ratio_400_800 < wa_ratio_400_800)
# Naranja: corredor 800-400 (equilibrado con tendencia a 400)
# Azul: especialista de 800 (equilibrado puro)
# Cyan: corredor 800-1500 (equilibrado con tendencia a 1500)
# Verde: mejor en 1500m (ratio_800_1500 > wa_ratio_800_1500)

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

# Crear gráfico interactivo con Plotly
fig = go.Figure()

# Convertir valores a formato mm:ss.ss para el hover
t400_formatted = [seconds_to_mm_ss(t) for t in t400_range]
t1500_formatted = [seconds_to_mm_ss(t) for t in t1500_values]

# Los puntos ya fueron calculados anteriormente, solo convertir None a 0 para el hover
points_400_display = [p if p is not None else 0 for p in points_400]
points_1500_display = [p if p is not None else 0 for p in points_1500]

# Crear una única traza con marcadores de colores variables
fig.add_trace(go.Scatter(
    x=t400_range,
    y=t1500_values,
    mode='markers+lines',
    marker=dict(
        color=colors,
        size=8,
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
        color_names,
        points_400_display,
        points_1500_display
    )),
    hovertemplate=(
        '<b>Perfil</b>: %{customdata[4]}<br>'
        '<b>t400</b>: %{customdata[0]} (%{customdata[5]} pts)<br>'
        '<b>t1500</b>: %{customdata[1]} (%{customdata[6]} pts)<br>'
        '<b>Ratio 400/800</b>: %{customdata[2]}<br>'
        '<b>Ratio 800/1500</b>: %{customdata[3]}<extra></extra>'
    ),
    showlegend=False
))

# Agregar trazas invisibles solo para la leyenda
legend_items = [
    ('400m o menos', 'red'),
    ('800m-400m', 'orange'),
    ('800m', 'blue'),
    ('800m-1500m', 'cyan'),
    ('1500m o más', 'green')
]

for name, color in legend_items:
    fig.add_trace(go.Scatter(
        x=[None],
        y=[None],
        mode='markers',
        marker=dict(size=10, color=color),
        name=name,
        showlegend=True
    ))

# Configurar el layout
fig.update_layout(
    title=f'Relaciones 400m vs 1500m para 800m en {seconds_to_mm_ss(t800_fixed)} ({t800_fixed_points} puntos)',
    xaxis_title='Tiempo 400m (mm:ss)',
    yaxis_title='Tiempo 1500m (mm:ss)',
    hovermode='x',
    showlegend=True,
    height=600,
    template='plotly_white',
    legend=dict(
        title=dict(text="Perfil de corredor"),
        yanchor="top",
        y=0.99,
        xanchor="right",
        x=0.99
    ),
    xaxis=dict(
        showgrid=True,
        gridwidth=1,
        gridcolor='LightGray',
        showspikes=True,
        spikemode='across',
        spikethickness=1,
        spikecolor='gray',
        spikedash='solid',
        spikesnap='cursor'
    ),
    yaxis=dict(
        showgrid=True,
        gridwidth=1,
        gridcolor='LightGray'
    )
)
    
# Crear ticks personalizados en formato mm:ss para el eje Y (múltiplos de 5)
y_min = int(np.floor(t1500_values.min() / 10) * 10)
y_max = int(np.ceil(t1500_values.max() / 10) * 10)
y_ticks = np.arange(y_min, y_max + 1, 10)
fig.update_yaxes(
    tickmode='array',
    tickvals=y_ticks,
    ticktext=[seconds_to_mm_ss(t) for t in y_ticks]
)

# Crear ticks personalizados en formato mm:ss para el eje X (múltiplos de 1)
x_min = int(np.floor(t400_min))
x_max = int(np.ceil(t400_max))
x_ticks = np.arange(x_min, x_max + 1, 1)
fig.update_xaxes(
    tickmode='array',
    tickvals=x_ticks,
    ticktext=[seconds_to_mm_ss(t) for t in x_ticks]
)

# Mostrar el gráfico en Streamlit
st.plotly_chart(fig, use_container_width=True)

# Información adicional
st.markdown("### Información")
st.markdown(f"""
- **Tiempo objetivo de 800m**: {seconds_to_mm_ss(t800_fixed)}
- **Ecuación**: `t800 = t400 × 1.2 + t1500 × 0.216`
- **Ratio de velocidades 400/800 para marcas técnicas equivalentes ({t800_fixed_points} puntos)**: {wa_ratio_400_800:.4f}
- **Ratio de velocidades 800/1500 para marcas técnicas equivalentes ({t800_fixed_points} puntos)**: {wa_ratio_800_1500:.4f}

**Interpretación de colores (5 categorías):**
- 🔴 **400m o menos**: Mejor desempeño en 400m que en 800m (ratio 400/800 < {wa_ratio_400_800:.4f})
- 🟠 **800m-400m**: Corredor de 800m con tendencia a velocidad
- 🔵 **800m**: Perfil equilibrado, especialista puro de 800m
- 🔷 **800m-1500m**: Corredor de 800m con tendencia a resistencia
- 🟢 **1500m o más**: Mejor desempeño en 1500m que en 800m (ratio 800/1500 > {wa_ratio_800_1500:.4f})
""")
