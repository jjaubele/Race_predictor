precision = 10000
t_1 = 206.73/3.75
t_3 = 437.55/7.5
t_2 = 283.13/5

for i in range(precision):
    p1 = (i + 1) / precision
    p2 = 1 - p1
    if round(p1 * t_1 + p2 * t_3 - t_2, 2) < 0.001:
        print(f'p1 = {p1}, p2 = {p2}')
        break


