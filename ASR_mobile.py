import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots
from scipy.optimize import fsolve

from physiological_functions import aerobic_speed, anaerobic_speed_reserve, speed
from utils import get_points, mm_ss_to_seconds, seconds_to_mm_ss


def load_scoring_data():
    mens_df = pd.read_csv("mens_scoring_tables.csv", index_col=0)
    womens_df = pd.read_csv("womens_scoring_tables.csv", index_col=0)

    event_columns = ["100m", "200m", "300m", "400m", "600m", "800m", "1000m", "1500m", "Mile", "2000m"]
    mens_seconds = {}
    womens_seconds = {}

    for event in event_columns:
        mens_seconds[event] = mens_df.get(event, pd.Series()).apply(mm_ss_to_seconds) if event in mens_df.columns else None
        womens_seconds[event] = womens_df.get(event, pd.Series()).apply(mm_ss_to_seconds) if event in womens_df.columns else None

    return mens_seconds, womens_seconds


def solve_distance_predictions(aerobic_speed_val, asr):
    distances = [200, 300, 400, 600, 800, 1000, 1500, 1609.34, 2000]
    labels = ["200m", "300m", "400m", "600m", "800m", "1000m", "1500m", "1 milla", "2000m"]

    all_distance_data = {}
    marker_times = []
    marker_velocities = []
    marker_labels = []

    for dist, label in zip(distances, labels):
        def equation(t):
            if t <= 0:
                return float("inf")
            vel = speed(aerobic_speed_val, aerobic_speed_val + asr, t)
            return vel * t - dist

        try:
            initial_guess = dist / (aerobic_speed_val + asr / 2)
            time_solution = fsolve(equation, initial_guess)[0]

            if 10 <= time_solution <= 360:
                vel = speed(aerobic_speed_val, aerobic_speed_val + asr, time_solution)
                vel_kmh = vel * 3.6
                pace = 1000 / (vel * 60) if vel > 0 else 0

                marker_times.append(time_solution)
                marker_velocities.append(vel_kmh)
                marker_labels.append(label)

                all_distance_data[label] = {
                    "dist": dist,
                    "time": time_solution,
                    "velocity": vel,
                    "velocity_kmh": vel_kmh,
                    "pace": pace,
                }
        except Exception:
            continue

    return all_distance_data, marker_times, marker_velocities, marker_labels


def build_velocity_chart(time_1_sec, time_2_sec, distance_1, distance_2, aerobic_speed_val, asr, marker_times, marker_velocities, marker_labels):
    time_range = np.linspace(20, 360, 1000)

    velocity_values = []
    velocity_kmh_values = []
    pace_values = []
    time_formatted = []
    distance_values = []

    for t in time_range:
        vel = speed(aerobic_speed_val, aerobic_speed_val + asr, t)
        velocity_values.append(vel)
        velocity_kmh_values.append(vel * 3.6)
        time_formatted.append(seconds_to_mm_ss(t))
        distance_values.append(vel * t)
        pace_values.append(1000 / (vel * 60) if vel > 0 else 0)

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Scatter(
            x=time_range,
            y=velocity_kmh_values,
            mode="lines",
            name="Velocidad",
            line=dict(width=3, color="#0077b6"),
            hovertemplate="<b>Tiempo:</b> %{customdata[0]}<br>"
            + "<b>Distancia:</b> %{customdata[2]:.0f} m<br>"
            + "<b>Velocidad:</b> %{y:.2f} km/h<br>"
            + "<b>Pace:</b> %{customdata[1]}<extra></extra>",
            customdata=[
                [
                    tf,
                    seconds_to_mm_ss(p * 60) if p > 0 else "N/A",
                    d,
                ]
                for tf, p, d in zip(time_formatted, pace_values, distance_values)
            ],
        ),
        secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(
            x=[time_1_sec, time_2_sec],
            y=[distance_1 / time_1_sec * 3.6, distance_2 / time_2_sec * 3.6],
            mode="markers+text",
            name="Trials",
            marker=dict(size=11, color="#d90429", symbol="circle"),
            text=["Trial 1", "Trial 2"],
            textposition="top center",
            textfont=dict(size=11, color="#d90429"),
            hovertemplate="<b>%{text}</b><br>"
            + "<b>Tiempo:</b> %{customdata[0]}<br>"
            + "<b>Distancia:</b> %{customdata[1]:.0f} m<br>"
            + "<b>Velocidad:</b> %{y:.2f} km/h<extra></extra>",
            customdata=[[seconds_to_mm_ss(time_1_sec), distance_1], [seconds_to_mm_ss(time_2_sec), distance_2]],
        ),
        secondary_y=False,
    )

    if marker_times:
        fig.add_trace(
            go.Scatter(
                x=marker_times,
                y=marker_velocities,
                mode="markers+text",
                name="Distancias",
                marker=dict(size=9, color="#2a9d8f", symbol="diamond"),
                text=marker_labels,
                textposition="bottom center",
                textfont=dict(size=9, color="#2a9d8f"),
                hoverinfo="skip",
            ),
            secondary_y=False,
        )

    fig.add_hline(
        y=aerobic_speed_val * 3.6,
        line_dash="dash",
        line_color="#fb8500",
        line_width=2,
        annotation_text="Velocidad Aerobica",
        annotation_position="left",
        secondary_y=False,
    )

    fig.update_xaxes(title_text="Tiempo (s)")
    fig.update_yaxes(title_text="Velocidad (km/h)", secondary_y=False)

    fig.update_layout(
        hovermode="x unified",
        template="plotly_white",
        height=430,
        margin=dict(l=10, r=10, t=20, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
    )

    return fig


def build_prediction_table(all_distance_data, gender, mens_scores, womens_scores):
    distance_to_column = {
        "100m": "100m",
        "200m": "200m",
        "300m": "300m",
        "400m": "400m",
        "600m": "600m",
        "800m": "800m",
        "1000m": "1000m",
        "1500m": "1500m",
        "1 milla": "Mile",
        "2000m": "2000m",
    }

    score_map = mens_scores if gender == "Masculino" else womens_scores
    ordered_labels = ["200m", "300m", "400m", "600m", "800m", "1000m", "1500m", "1 milla", "2000m"]
    table_data = []

    for label in ordered_labels:
        if label not in all_distance_data:
            continue

        data = all_distance_data[label]
        wa_points = None
        score_key = distance_to_column.get(label)
        score_table = score_map.get(score_key) if score_key else None

        if score_table is not None and not score_table.empty:
            wa_points = get_points(data["time"], score_table)

        table_data.append(
            {
                "Distancia": label,
                "Tiempo": seconds_to_mm_ss(data["time"]),
                "Tiempo_num": data["time"],
                "Velocidad (km/h)": f"{data['velocity_kmh']:.2f}",
                "Pace (min/km)": seconds_to_mm_ss(data["pace"] * 60) if data["pace"] > 0 else "N/A",
                "Puntos WA": wa_points if wa_points is not None else "-",
            }
        )

    if not table_data:
        return pd.DataFrame(), []

    df = pd.DataFrame(table_data).sort_values("Tiempo_num", ascending=True).drop(columns=["Tiempo_num"]).reset_index(drop=True)

    wa_data = []
    for item in table_data:
        if item["Puntos WA"] != "-" and item["Puntos WA"] is not None:
            wa_data.append({"Distancia": item["Distancia"], "Puntos": item["Puntos WA"], "Tiempo": item["Tiempo"]})

    return df, wa_data


def build_wa_chart(wa_data):
    fig_wa = go.Figure()
    distances_list = [item["Distancia"] for item in wa_data]
    points_list = [item["Puntos"] for item in wa_data]
    times_list = [item["Tiempo"] for item in wa_data]

    fig_wa.add_trace(
        go.Bar(
            x=distances_list,
            y=points_list,
            marker=dict(color="#0077b6", line=dict(color="rgba(0,0,0,0.2)", width=1)),
            text=[f"{pts} pts" for pts in points_list],
            textposition="outside",
            textfont=dict(size=11, color="black"),
            hovertemplate="<b>%{x}</b><br><b>Puntos WA:</b> %{y}<br><b>Tiempo:</b> %{customdata}<extra></extra>",
            customdata=times_list,
        )
    )

    fig_wa.update_layout(
        xaxis_title="Distancia",
        yaxis_title="Puntos WA",
        yaxis=dict(range=[0, min(1450, max(points_list) * 1.1)], showgrid=True, gridcolor="LightGray"),
        xaxis=dict(showgrid=False),
        template="plotly_white",
        height=420,
        margin=dict(l=10, r=10, t=20, b=10),
        showlegend=False,
    )

    fig_wa.add_hline(y=1200, line_dash="dash", line_color="green", line_width=1.2, annotation_text="Elite")
    fig_wa.add_hline(y=1000, line_dash="dash", line_color="lightgreen", line_width=1.0, annotation_text="Muy Bueno")
    fig_wa.add_hline(y=800, line_dash="dash", line_color="gold", line_width=1.0, annotation_text="Bueno")

    return fig_wa


st.set_page_config(page_title="ASR Mobile", layout="centered", initial_sidebar_state="collapsed")

st.title("ASR Predictor (Mobile)")
st.caption("Version optimizada para pantalla de celular")
st.markdown(
    "Modelo exponencial negativo para estimar rendimiento de 200m a 2000m, usando dos trials maximos."
)

mens_scores, womens_scores = load_scoring_data()

with st.form("mobile_inputs"):
    gender = st.segmented_control("Genero", ["Masculino", "Femenino"], default="Masculino")

    st.markdown("### Trial 1 (mas corto)")
    distance_1 = st.number_input("Distancia 1 (m)", min_value=200, max_value=2000, value=400, step=1)
    time_1_sec = st.number_input("Tiempo 1 (s)", min_value=20.0, max_value=360.0, value=54.0, step=0.1)

    st.markdown("### Trial 2 (mas largo)")
    distance_2 = st.number_input("Distancia 2 (m)", min_value=200, max_value=2000, value=1500, step=1)
    time_2_sec = st.number_input("Tiempo 2 (s)", min_value=20.0, max_value=360.0, value=250.0, step=0.1)

    submitted = st.form_submit_button("Calcular predicciones", use_container_width=True)

if not submitted:
    st.info("Ingresa tus datos y toca Calcular predicciones.")
    st.stop()

if time_1_sec >= time_2_sec:
    st.error("El Trial 1 debe ser mas corto (menor tiempo) que el Trial 2.")
    st.stop()

try:
    asr = anaerobic_speed_reserve(distance_1, time_1_sec, distance_2, time_2_sec)
    aerobic_speed_val = aerobic_speed(distance_2, time_2_sec, asr)
except Exception as exc:
    st.error(f"Error en el calculo: {exc}")
    st.stop()

c1, c2 = st.columns(2)
c1.metric("ASR (m/s)", f"{asr:.2f}")
c2.metric("Velocidad aerobica (km/h)", f"{aerobic_speed_val * 3.6:.2f}")

all_distance_data, marker_times, marker_velocities, marker_labels = solve_distance_predictions(aerobic_speed_val, asr)

fig_velocity = build_velocity_chart(
    time_1_sec,
    time_2_sec,
    distance_1,
    distance_2,
    aerobic_speed_val,
    asr,
    marker_times,
    marker_velocities,
    marker_labels,
)
st.plotly_chart(fig_velocity, use_container_width=True)

st.markdown("### Predicciones")
df_predictions, wa_data = build_prediction_table(all_distance_data, gender, mens_scores, womens_scores)

if not df_predictions.empty:
    st.dataframe(df_predictions, use_container_width=True, hide_index=True)
else:
    st.warning("No fue posible generar predicciones con estos parametros.")

st.markdown("### Puntos World Athletics")
if wa_data:
    st.plotly_chart(build_wa_chart(wa_data), use_container_width=True)
else:
    st.info("No hay puntos WA disponibles para estas distancias predichas.")

with st.expander("Notas de uso"):
    st.markdown("- Mejores resultados con Trial 1 entre 400m y 800m.")
    st.markdown("- Mejores resultados con Trial 2 entre 800m y 1500m.")
    st.markdown("- Interpolar entre trials suele ser mas preciso que extrapolar fuera de su rango.")
    st.markdown("- Los dos trials deben ser esfuerzos maximos y de un estado de forma similar.")

with st.expander("Formulas"):
    st.latex(r"ASR = \frac{V_1 - V_2}{e^{-Kt_1} - e^{-Kt_2}}")
    st.latex(r"V_a = V_2 - ASR \cdot e^{-Kt_2}")
    st.latex(r"V(t) = V_a + ASR \cdot e^{-Kt}")
