import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from utils import mm_ss_to_seconds, seconds_to_mm_ss, get_points

# Cargar tablas y convertir tiempos a segundos
mens_scoring_tables_df = pd.read_csv('mens_scoring_tables.csv', index_col=0)
womens_scoring_tables_df = pd.read_csv('womens_scoring_tables.csv', index_col=0)

# Convertir tiempos de formato mm:ss.ss a segundos
mens_800m_seconds = mens_scoring_tables_df["800m"].apply(mm_ss_to_seconds)
mens_1500m_seconds = mens_scoring_tables_df["1500m"].apply(mm_ss_to_seconds)
mens_5000m_seconds = mens_scoring_tables_df["5000m"].apply(mm_ss_to_seconds)

womens_800m_seconds = womens_scoring_tables_df["800m"].apply(mm_ss_to_seconds)
womens_1500m_seconds = womens_scoring_tables_df["1500m"].apply(mm_ss_to_seconds)
womens_5000m_seconds = womens_scoring_tables_df["5000m"].apply(mm_ss_to_seconds)

# Calcular ratios usando tiempos en segundos
mens_ratios_800_1500 = (mens_800m_seconds / 800) / (mens_1500m_seconds / 1500)
mens_ratios_1500_5000 = (mens_1500m_seconds / 1500) / (mens_5000m_seconds / 5000)

womens_ratios_800_1500 = (womens_800m_seconds / 800) / (womens_1500m_seconds / 1500)
womens_ratios_1500_5000 = (womens_1500m_seconds / 1500) / (womens_5000m_seconds / 5000)

# Título de la aplicación
st.title("Perfiles de Tiempo de Carrera - 1500m")

# Sidebar para inputs
st.sidebar.header("Parámetros")

# Selección de género
gender = st.sidebar.radio("Selecciona el género:", ('Masculino', 'Femenino'))

if gender == 'Masculino':
    ratios_800_1500 = mens_ratios_800_1500
    ratios_1500_5000 = mens_ratios_1500_5000
    fastest_1500 = mens_1500m_seconds[1400]
    slowest_1500 = mens_1500m_seconds[1]
    default_t1500 = 240.0
else:
    ratios_800_1500 = womens_ratios_800_1500
    ratios_1500_5000 = womens_ratios_1500_5000
    fastest_1500 = womens_1500m_seconds[1400]
    slowest_1500 = womens_1500m_seconds[1]
    default_t1500 = 300.0

# Input para t1500 fijo
t1500_fixed = st.sidebar.number_input(
    "Tiempo objetivo de 1500m (segundos)", 
    min_value=fastest_1500, 
    max_value=slowest_1500, 
    value=default_t1500,
    step=1.0
)

# Rango para t800
t800_min = 0.88 * t1500_fixed * (800/1500)  # Ajuste para 800m más rápido
t800_max = 0.97 * t1500_fixed * (800/1500)  # Ajuste para 800m más lento

# Generar datos
t800_range = np.linspace(t800_min, t800_max, 1000)
# Despejar t5000 de la ecuación: t1500 = t800 * 1.25 + t5000 * 0.1015
# t5000 = (t1500 - t800 * 1.25) / 0.1015
t5000_values = (t1500_fixed - t800_range * 1.25) / 0.1015

# Calcular ratios para cada punto
pace_800 = t800_range / 800  # segundos por metro
pace_1500 = t1500_fixed / 1500
pace_5000 = t5000_values / 5000

ratio_800_1500 = pace_800 / pace_1500
ratio_1500_5000 = pace_1500 / pace_5000

if gender == 'Masculino':
    t1500_fixed_points = get_points(t1500_fixed, mens_1500m_seconds)
    wa_ratio_800_1500 = mens_ratios_800_1500.loc[t1500_fixed_points]
    wa_ratio_1500_5000 = mens_ratios_1500_5000.loc[t1500_fixed_points]
    # Calcular puntos para cada tiempo de 800m y 5000m
    points_800 = np.array([get_points(t, mens_800m_seconds) if get_points(t, mens_800m_seconds) is not None else 0 for t in t800_range])
    points_5000 = np.array([get_points(t, mens_5000m_seconds) if get_points(t, mens_5000m_seconds) is not None else 0 for t in t5000_values])
else:
    t1500_fixed_points = get_points(t1500_fixed, womens_1500m_seconds)
    wa_ratio_800_1500 = womens_ratios_800_1500.loc[t1500_fixed_points]
    wa_ratio_1500_5000 = womens_ratios_1500_5000.loc[t1500_fixed_points]
    # Calcular puntos para cada tiempo de 800m y 5000m
    points_800 = np.array([get_points(t, womens_800m_seconds) if get_points(t, womens_800m_seconds) is not None else 0 for t in t800_range])
    points_5000 = np.array([get_points(t, womens_5000m_seconds) if get_points(t, womens_5000m_seconds) is not None else 0 for t in t5000_values])

# Encontrar el punto de equilibrio puro (diferencia mínima de puntajes)
point_differences = np.abs(points_800 - points_5000)
equilibrium_idx = np.argmin(point_differences)
equilibrium_ratio_800_1500 = ratio_800_1500[equilibrium_idx]
equilibrium_ratio_1500_5000 = ratio_1500_5000[equilibrium_idx]

# Calcular límites como promedios entre equilibrio puro y ratios WA
limit_800_specialist = (equilibrium_ratio_800_1500 + wa_ratio_800_1500) / 2
limit_5000_specialist = (equilibrium_ratio_1500_5000 + wa_ratio_1500_5000) / 2

# Determinar el color para cada segmento (5 categorías)
# Rojo: mejor en 800m (ratio_800_1500 < wa_ratio_800_1500)
# Naranja: corredor 1500-800 (equilibrado con tendencia a 800)
# Azul: especialista de 1500 (equilibrado puro)
# Cyan: corredor 1500-5000 (equilibrado con tendencia a 5000)
# Verde: mejor en 5000m (ratio_1500_5000 > wa_ratio_1500_5000)

colors = []
color_names = []

for i in range(len(ratio_800_1500)):
    if ratio_800_1500[i] < wa_ratio_800_1500:
        colors.append('red')
        color_names.append('800m o menos')
    elif ratio_1500_5000[i] > wa_ratio_1500_5000:
        colors.append('green')
        color_names.append('5000m o más')
    elif ratio_800_1500[i] < limit_800_specialist:
        colors.append('orange')
        color_names.append('1500m-800m')
    elif ratio_1500_5000[i] > limit_5000_specialist:
        colors.append('cyan')
        color_names.append('1500m-5000m')
    else:
        colors.append('blue')
        color_names.append('1500m')

# Crear gráfico interactivo con Plotly
fig = go.Figure()

# Convertir valores a formato mm:ss.ss para el hover
t800_formatted = [seconds_to_mm_ss(t) for t in t800_range]
t5000_formatted = [seconds_to_mm_ss(t) for t in t5000_values]

# Los puntos ya fueron calculados anteriormente, solo convertir None a 0 para el hover
points_800_display = [p if p is not None else 0 for p in points_800]
points_5000_display = [p if p is not None else 0 for p in points_5000]

# Crear una única traza con marcadores de colores variables
fig.add_trace(go.Scatter(
    x=t800_range,
    y=t5000_values,
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
        t800_formatted,
        t5000_formatted,
        [f"{r:.4f}" for r in ratio_800_1500],
        [f"{r:.4f}" for r in ratio_1500_5000],
        color_names,
        points_800_display,
        points_5000_display
    )),
    hovertemplate=(
        '<b>Perfil</b>: %{customdata[4]}<br>'
        '<b>t800</b>: %{customdata[0]} (%{customdata[5]} pts)<br>'
        '<b>t5000</b>: %{customdata[1]} (%{customdata[6]} pts)<br>'
        '<b>Ratio 800/1500</b>: %{customdata[2]}<br>'
        '<b>Ratio 1500/5000</b>: %{customdata[3]}<extra></extra>'
    ),
    showlegend=False
))

# Agregar trazas invisibles solo para la leyenda
legend_items = [
    ('800m o menos', 'red'),
    ('1500m-800m', 'orange'),
    ('1500m', 'blue'),
    ('1500m-5000m', 'cyan'),
    ('5000m o más', 'green')
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
    title=f'Relaciones 800m vs 5000m para 1500m en {seconds_to_mm_ss(t1500_fixed)} ({t1500_fixed_points} puntos)',
    xaxis_title='Tiempo 800m (mm:ss)',
    yaxis_title='Tiempo 5000m (mm:ss)',
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
    
# Crear ticks personalizados en formato mm:ss para el eje Y (múltiplos de 10)
y_min = int(np.floor(t5000_values.min() / 30) * 30)
y_max = int(np.ceil(t5000_values.max() / 30) * 30)
y_ticks = np.arange(y_min, y_max + 1, 30)
fig.update_yaxes(
    tickmode='array',
    tickvals=y_ticks,
    ticktext=[seconds_to_mm_ss(t) for t in y_ticks]
)

# Crear ticks personalizados en formato mm:ss para el eje X (múltiplos de 2)
x_min = int(np.floor(t800_min / 2) * 2)
x_max = int(np.ceil(t800_max / 2) * 2)
x_ticks = np.arange(x_min, x_max + 1, 2)
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
- **Tiempo objetivo de 1500m**: {seconds_to_mm_ss(t1500_fixed)}
- **Ecuación**: `t1500 = t800 × 1.25 + t5000 × 0.1015`
- **Ratio de velocidades 800/1500 para marcas técnicas equivalentes ({t1500_fixed_points} puntos)**: {wa_ratio_800_1500:.4f}
- **Ratio de velocidades 1500/5000 para marcas técnicas equivalentes ({t1500_fixed_points} puntos)**: {wa_ratio_1500_5000:.4f}

**Interpretación de colores (5 categorías):**
- 🔴 **800m o menos**: Mejor desempeño en 800m que en 1500m (ratio 800/1500 < {wa_ratio_800_1500:.4f})
- 🟠 **1500m-800m**: Corredor de 1500m con tendencia a velocidad
- 🔵 **1500m**: Perfil equilibrado, especialista puro de 1500m
- 🔷 **1500m-5000m**: Corredor de 1500m con tendencia a resistencia
- 🟢 **5000m o más**: Mejor desempeño en 5000m que en 1500m (ratio 1500/5000 > {wa_ratio_1500_5000:.4f})
""")
