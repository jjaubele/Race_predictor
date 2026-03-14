import pandas as pd
import numpy as np

Tau = 150
K = 1 / Tau

# tiempo en minutos
def percent_max(time):
    return 0.8 + 0.1894393 * np.exp(-0.012778 * time) + 0.2989558 * np.exp(-0.1932605 * time)

# velocidad en m/min
def vo2(velocity):
    return -4.60 + 0.182258 * velocity + 0.000104 * velocity**2

def velocity(vo2):
    a = 0.000104
    b = 0.182258
    c = -4.60 - vo2
    discriminant = b**2 - 4*a*c
    if discriminant < 0:
        raise ValueError("No real solution for the given VO2 value.")
    sqrt_discriminant = np.sqrt(discriminant)
    velocity1 = (-b + sqrt_discriminant) / (2*a)
    return velocity1

def vo2max_calc(distance, time):
    velocity_val = distance / time
    return vo2(velocity_val) / percent_max(time)

# tiempo en segundos, distance en metros
def VAM(distance, time):
    time = time / 60  # convertir a minutos
    return velocity(vo2max_calc(distance, time))  / 60  # convertir a m/s

def speed(aerobic_speed, anaerobic_speed, time):
    return aerobic_speed + (anaerobic_speed - aerobic_speed) * np.exp(-K * time)

def anaerobic_speed_reserve(distance_1, time_1, distance_2, time_2):
    speed_1 = distance_1 / time_1
    speed_2 = distance_2 / time_2
    speed_diff = speed_1 - speed_2
    exp_diff = np.exp(-K * time_1) - np.exp(-K * time_2)
    return speed_diff / exp_diff

def aerobic_speed(distance, time, ASR):
    speed = distance / time
    return speed - ASR * np.exp(-K * time)

def maximal_sprint_speed(aerobic_speed, time, distance):
    speed = distance / time
    return (speed - aerobic_speed) / np.exp(-K * time) + aerobic_speed

