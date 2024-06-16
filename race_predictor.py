import streamlit as st

# Función para calcular el tiempo de 800m
def calculate_t800(t400, t1500):
    return t400 * 1.2 + t1500 * 0.216

def calculate_t400(t800, t1500):
    return (t800 - t1500 * 0.216) / 1.2

def calculate_t1500(t400, t800):
    return (t800 - t400 * 1.2) / 0.216

def calculate_t800_2(t1500, t5000):
    return (t1500 - t5000 * 0.1015) / 1.25

def calculate_t1500_2(t800, t5000):
    return t800 * 1.25 + t5000 * 0.1015

def calculate_t5000(t800, t1500):
    return (t1500 - t800 * 1.25) / 0.1015

# Función para convertir mm:ss.ss a segundos
def mm_ss_to_seconds(mm_ss):
    mm, ss = mm_ss.split(':')
    mm = int(mm)
    ss = float(ss)
    return mm * 60 + ss

# Función para convertir segundos a mm:ss.ss
def seconds_to_mm_ss(seconds):
    mm = int(seconds // 60)
    ss = seconds % 60
    return f"{mm}:{ss:05.2f}"

# Título de la aplicación
st.title('Predicción de tiempos para carreras de medio fondo')

# Selección de la variable constante
constant_var = st.selectbox('Selecciona la distancia a predecir:', ('400m (800-1500)', '800m (400-1500)', '800m (1500-5000)', '1500m (400-800)', '1500m (800-5000)', '5000m (800-1500)'))

# Entrada de los tiempos
if constant_var == '400m (800-1500)':
    t800_mm_ss = st.text_input('Introduce el tiempo de 800m:', value='00:00.00')
    t1500_mm_ss = st.text_input('Introduce el tiempo de 1500m:', value='00:00.00')
    t800 = mm_ss_to_seconds(t800_mm_ss)
    t1500 = mm_ss_to_seconds(t1500_mm_ss)
    t400 = calculate_t400(t800, t1500)
    t400_mm_ss = seconds_to_mm_ss(t400)
    st.write(f'Con 800m = {t800_mm_ss} y 1500m = {t1500_mm_ss}, el tiempo predicho para 400m es: {t400_mm_ss}')

elif constant_var == '1500m (400-800)':
    t400_mm_ss = st.text_input('Introduce el tiempo de 400m:', value='00:00.00')
    t800_mm_ss = st.text_input('Introduce el tiempo de 800m:', value='00:00.00')
    t400 = mm_ss_to_seconds(t400_mm_ss)
    t800 = mm_ss_to_seconds(t800_mm_ss)
    t1500 = calculate_t1500(t400, t800)
    t1500_mm_ss = seconds_to_mm_ss(t1500)
    st.write(f'Con 400m = {t400_mm_ss} y 800m = {t800_mm_ss}, el tiempo predicho para 1500m es: {t1500_mm_ss}')

elif constant_var == '800m (400-1500)':
    t400_mm_ss = st.text_input('Introduce el tiempo de 400m:', value='00:00.00')
    t1500_mm_ss = st.text_input('Introduce el tiempo de 1500m:', value='00:00.00')
    t400 = mm_ss_to_seconds(t400_mm_ss)
    t1500 = mm_ss_to_seconds(t1500_mm_ss)
    t800 = calculate_t800(t400, t1500)
    t800_mm_ss = seconds_to_mm_ss(t800)
    st.write(f'Con 400m = {t400_mm_ss} y 1500m = {t1500_mm_ss}, el tiempo predicho para 800m es: {t800_mm_ss}')

elif constant_var == '5000m (800-1500)':
    t800_mm_ss = st.text_input('Introduce el tiempo de 800m:', value='00:00.00')
    t1500_mm_ss = st.text_input('Introduce el tiempo de 1500m:', value='00:00.00')
    t800 = mm_ss_to_seconds(t800_mm_ss)
    t1500 = mm_ss_to_seconds(t1500_mm_ss)
    t5000 = calculate_t5000(t800, t1500)
    t5000_mm_ss = seconds_to_mm_ss(t5000)
    st.write(f'Con 800m = {t800_mm_ss} y 1500m = {t1500_mm_ss}, el tiempo predicho para 5000m es: {t5000_mm_ss}')

elif constant_var == '800m (1500-5000)':
    t1500_mm_ss = st.text_input('Introduce el tiempo de 1500m:', value='00:00.00')
    t5000_mm_ss = st.text_input('Introduce el tiempo de 5000m:', value='00:00.00')
    t1500 = mm_ss_to_seconds(t1500_mm_ss)
    t5000 = mm_ss_to_seconds(t5000_mm_ss)
    t800 = calculate_t800_2(t1500, t5000)
    t800_mm_ss = seconds_to_mm_ss(t800)
    st.write(f'Con 1500m = {t1500_mm_ss} y 5000m = {t5000_mm_ss}, el tiempo predicho para 800m es: {t800_mm_ss}')

elif constant_var == '1500m (800-5000)':
    t800_mm_ss = st.text_input('Introduce el tiempo de 800m:', value='00:00.00')
    t5000_mm_ss = st.text_input('Introduce el tiempo de 5000m:', value='00:00.00')
    t800 = mm_ss_to_seconds(t800_mm_ss)
    t5000 = mm_ss_to_seconds(t5000_mm_ss)
    t1500 = calculate_t1500_2(t800, t5000)
    t1500_mm_ss = seconds_to_mm_ss(t1500)
    st.write(f'Con 800m = {t800_mm_ss} y 5000m = {t5000_mm_ss}, el tiempo predicho para 1500m es: {t1500_mm_ss}')

# Nota sobre la fórmula utilizada
st.markdown('### Fórmulas utilizadas:')
st.latex(r't_{800} = t_{400} \times 1.2 + t_{1500} \times 0.216')
st.latex(r't_{1500} = t_{800} \times 1.25 + t_{5000} \times 0.1015')
