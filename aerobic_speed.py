import re

import numpy as np
import plotly.graph_objects as go
import streamlit as st

K = 1 / (30 * 60)  # Convert 30 minutes to seconds

def speed(vLT2, vVO2Max, time):
	return vLT2 + (vVO2Max - vLT2) * np.exp(-K * time)

def parse_pace_mmss(pace_text):
	"""Parse pace in MM:SS format and return seconds per km."""
	if pace_text is None:
		return False, "El pace no puede estar vacio.", None

	text = str(pace_text).strip()
	match = re.fullmatch(r"(\d{1,2}):(\d{2})", text)
	if not match:
		return False, "Formato invalido. Usa MM:SS, por ejemplo 4:30.", None

	minutes = int(match.group(1))
	seconds = int(match.group(2))

	if seconds > 59:
		return False, "Los segundos deben estar entre 00 y 59.", None

	total_seconds = minutes * 60 + seconds
	if total_seconds <= 0:
		return False, "El pace debe ser mayor que 0:00.", None

	if total_seconds > 1200:
		return False, "El pace ingresado es demasiado alto. Maximo permitido: 20:00.", None

	return True, "", float(total_seconds)


def seconds_to_mmss(seconds_value):
	minutes = int(seconds_value // 60)
	seconds = int(round(seconds_value % 60))
	if seconds == 60:
		minutes += 1
		seconds = 0
	return f"{minutes}:{seconds:02d}"


def mmss_to_seconds(mmss_text):
	minutes_str, seconds_str = str(mmss_text).split(":")
	return int(minutes_str) * 60 + int(seconds_str)


def calibrate_exponential_model(v_6min, v_60min):
	"""Get Va and ASR for V(t)=Va + ASR*exp(-K*t) using points at 6 and 60 min."""
	t1 = 6 * 60
	t2 = 60 * 60
	exp1 = np.exp(-K * t1)
	exp2 = np.exp(-K * t2)
	denominator = exp1 - exp2

	if abs(denominator) < 1e-12:
		raise ValueError("No se pudo calibrar el modelo con los tiempos definidos.")

	asr = (v_6min - v_60min) / denominator
	va = v_6min - asr * exp1
	return va, asr


st.set_page_config(page_title="Curva de Velocidad desde Pace", layout="wide")
st.title("Curva velocidad vs tiempo desde pace")
st.markdown(
	"Ingresa el pace de VO2Max y el pace de LT2. El modelo asocia esos valores a 6 y 60 "
	"minutos, respectivamente, y ajusta una curva exponencial de decaimiento."
)

st.sidebar.header("Parametros de entrada")
pace_vo2_text = st.sidebar.text_input("Pace VO2Max (6 min) [MM:SS /km]", value="3:10")
pace_lt2_text = st.sidebar.text_input("Pace LT2 (60 min) [MM:SS /km]", value="3:35")

ok_vo2, msg_vo2, pace_vo2_sec_km = parse_pace_mmss(pace_vo2_text)
ok_lt2, msg_lt2, pace_lt2_sec_km = parse_pace_mmss(pace_lt2_text)

if not ok_vo2:
	st.sidebar.error(f"Pace VO2Max invalido: {msg_vo2}")
if not ok_lt2:
	st.sidebar.error(f"Pace LT2 invalido: {msg_lt2}")
if not (ok_vo2 and ok_lt2):
	st.stop()

# Convert pace (s/km) to speed (m/s)
v_6min = 1000.0 / pace_vo2_sec_km
v_60min = 1000.0 / pace_lt2_sec_km

if v_6min <= v_60min:
	st.sidebar.error("El pace de 6 min debe ser mas rapido que el de 60 min.")
	st.stop()

try:
	vLT2, asr_val = calibrate_exponential_model(v_6min, v_60min)
	vVO2Max = vLT2 + asr_val
except ValueError as error:
	st.error(str(error))
	st.stop()

if vLT2 <= 0 or asr_val <= 0:
	st.error(
		"La calibracion resulto en parametros no fisiologicos (Va <= 0 o ASR <= 0). "
		"Revisa los paces ingresados."
	)
	st.stop()

# Time domain: 6 to 60 minutes (in seconds)
time_seconds = np.linspace(6 * 60, 60 * 60, 600)
time_minutes = time_seconds / 60.0

velocity_ms = speed(vLT2, vVO2Max, time_seconds)
velocity_kmh = velocity_ms * 3.6
pace_seconds_curve = 1000.0 / velocity_ms
distance_m_curve = velocity_ms * time_seconds
pace_labels_curve = [f"{seconds_to_mmss(p)} /km" for p in pace_seconds_curve]
time_labels_curve = [seconds_to_mmss(t) for t in time_seconds]

customdata = np.column_stack(
	[
		time_labels_curve,
		velocity_ms,
		distance_m_curve,
		pace_labels_curve,
	]
)

fig = go.Figure()
fig.add_trace(
	go.Scatter(
		x=time_minutes,
		y=velocity_kmh,
		mode="lines",
		name="Curva exponencial",
		line=dict(width=3, color="#1f77b4"),
		customdata=customdata,
		hovertemplate="<b>Tiempo:</b> %{customdata[0]}<br>"
		+ "<b>Velocidad:</b> %{y:.2f} km/h<br>"
		+ "<b>Distancia:</b> %{customdata[2]:.0f} m<br>"
		+ "<b>Pace:</b> %{customdata[3]}<extra></extra>",
	)
)

marker_times_min = np.array([6.0, 60.0])
marker_vel_kmh = np.array([v_6min, v_60min]) * 3.6
marker_paces = [seconds_to_mmss(pace_vo2_sec_km), seconds_to_mmss(pace_lt2_sec_km)]
marker_labels = ["VO2Max (6 min)", "LT2 (60 min)"]
marker_distances_m = np.array([v_6min * 6 * 60, v_60min * 60 * 60])
marker_times_mmss = [seconds_to_mmss(6 * 60), seconds_to_mmss(60 * 60)]

fig.add_trace(
	go.Scatter(
		x=marker_times_min,
		y=marker_vel_kmh,
		mode="markers+text",
		name="Puntos de calibracion",
		marker=dict(size=12, color="red", symbol="circle"),
		text=marker_labels,
		textposition="top center",
		customdata=np.column_stack([marker_paces, marker_distances_m, marker_times_mmss]),
		hovertemplate="<b>%{text}</b><br>"
		+ "<b>Tiempo:</b> %{customdata[2]}<br>"
		+ "<b>Velocidad:</b> %{y:.2f} km/h<br>"
		+ "<b>Distancia:</b> %{customdata[1]:.0f} m<br>"
		+ "<b>Pace:</b> %{customdata[0]} /km<extra></extra>",
	)
)

# Hitos de distancia: se marcan solo si caen dentro del rango temporal modelado
distance_milestones = [
	("3000m", 3000.0),
	("5K", 5000.0),
	("10K", 10000.0),
	("15K", 15000.0),
	("Media maraton (21.097K)", 21097.0),
]

milestone_times_min = []
milestone_vel_kmh = []
milestone_labels = []
milestone_customdata = []
milestone_table_rows = [
	{
		"Hito": "VO2Max (6 min)",
		"Distancia (m)": int(marker_distances_m[0]),
		"Tiempo": marker_times_mmss[0],
		"Velocidad (km/h)": round(marker_vel_kmh[0], 2),
		"Pace": f"{marker_paces[0]} /km",
	},
	{
		"Hito": "LT2 (60 min)",
		"Distancia (m)": int(marker_distances_m[1]),
		"Tiempo": marker_times_mmss[1],
		"Velocidad (km/h)": round(marker_vel_kmh[1], 2),
		"Pace": f"{marker_paces[1]} /km",
	},
]

curve_min_distance = float(distance_m_curve.min())
curve_max_distance = float(distance_m_curve.max())

for label, target_distance in distance_milestones:
	if curve_min_distance <= target_distance <= curve_max_distance:
		t_solution_seconds = np.interp(target_distance, distance_m_curve, time_seconds)
		t_solution_minutes = t_solution_seconds / 60.0
		v_solution_ms = speed(vLT2, vVO2Max, t_solution_seconds)
		v_solution_kmh = v_solution_ms * 3.6
		pace_solution = seconds_to_mmss(1000.0 / v_solution_ms)
		time_solution_label = seconds_to_mmss(t_solution_seconds)

		milestone_times_min.append(t_solution_minutes)
		milestone_vel_kmh.append(v_solution_kmh)
		milestone_labels.append(label)
		milestone_customdata.append([target_distance, pace_solution, time_solution_label])
		milestone_table_rows.append(
			{
				"Hito": label,
				"Distancia (m)": int(target_distance),
				"Tiempo": time_solution_label,
				"Velocidad (km/h)": round(v_solution_kmh, 2),
				"Pace": f"{pace_solution} /km",
			}
		)

if milestone_times_min:
	fig.add_trace(
		go.Scatter(
			x=milestone_times_min,
			y=milestone_vel_kmh,
			mode="markers+text",
			name="Hitos de distancia",
			marker=dict(size=10, color="green", symbol="diamond"),
			text=milestone_labels,
			textposition="bottom center",
			customdata=np.array(milestone_customdata, dtype=object),
			hovertemplate="<b>%{text}</b><br>"
			+ "<b>Tiempo:</b> %{customdata[2]}<br>"
			+ "<b>Velocidad:</b> %{y:.2f} km/h<br>"
			+ "<b>Distancia:</b> %{customdata[0]:.0f} m<br>"
			+ "<b>Pace:</b> %{customdata[1]} /km<extra></extra>",
		)
	)

milestone_table_rows = sorted(
	milestone_table_rows,
	key=lambda row: mmss_to_seconds(row["Tiempo"]),
)

fig.add_hline(
	y=vLT2 * 3.6,
	line_dash="dash",
	line_color="orange",
	line_width=2,
	annotation_text="Velocidad LT2",
	annotation_position="top left",
)

fig.update_layout(
	template="plotly_white",
	hovermode="x unified",
	height=620,
	legend=dict(yanchor="top", y=0.98, xanchor="right", x=0.98),
)
fig.update_xaxes(title_text="Tiempo (minutos)", range=[6, 60])
fig.update_yaxes(title_text="Velocidad (km/h)")

st.plotly_chart(fig, use_container_width=True)

st.subheader("Resultados de hitos")
st.dataframe(milestone_table_rows, use_container_width=True, hide_index=True)

st.markdown("---")
st.subheader("Parametros calibrados")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Velocidad LT2", f"{vLT2 * 3.6:.2f} km/h")
col2.metric("Pace LT2", marker_paces[1])
col3.metric("Velocidad VO2Max", f"{vVO2Max * 3.6:.2f} km/h")
col4.metric("Pace VO2Max", marker_paces[0])
