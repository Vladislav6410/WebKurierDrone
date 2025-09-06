# -*- coding: utf-8 -*-
"""
Демонстрация работы PID-контроллера на упрощённой модели 1-го порядка.
Печатается таблица + строится график изменения состояния.
График сохраняется в tests/out/pid_demo.png
"""

import os
import matplotlib.pyplot as plt
from utils.pid import PID


def main():
    pid = PID(
        kp=0.6, ki=0.2, kd=0.05,
        setpoint=10.0,
        output_limits=(-100, 100),
        integral_limits=(-50, 50)
    )

    x = 0.0       # начальное состояние (например, высота)
    dt = 0.1
    alpha = 0.05  # коэффициент реакции системы

    history_t, history_x, history_u, history_err = [], [], [], []

    print(f"{'t':>4} {'x':>8} {'u':>8} {'error':>8}")
    print("-" * 32)

    for step in range(100):   # 10 секунд моделирования
        u = pid.update(x, dt)
        x += alpha * u
        error = pid.setpoint - x

        t = step * dt
        history_t.append(t)
        history_x.append(x)
        history_u.append(u)
        history_err.append(error)

        if step % 5 == 0:  # печатаем не каждую итерацию, а раз в 5 шагов
            print(f"{t:4.1f} {x:8.3f} {u:8.3f} {error:8.3f}")

    # графики
    plt.figure(figsize=(10, 5))
    plt.plot(history_t, history_x, label="x (состояние)")
    plt.plot(history_t, [pid.setpoint]*len(history_t), "r--", label="Setpoint")
    plt.plot(history_t, history_u, label="u (управление)")
    plt.plot(history_t, history_err, label="error")
    plt.xlabel("Время (с)")
    plt.ylabel("Значения")
    plt.title("PID демо: стабилизация на заданное значение")
    plt.legend()
    plt.grid(True)

    # создаём папку tests/out если её нет
    out_dir = os.path.join("tests", "out")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "pid_demo.png")

    # сохраняем картинку
    plt.savefig(out_path, dpi=150)
    print(f"\n📁 График сохранён: {out_path}")

    # показываем на экране
    plt.show()


if __name__ == "__main__":
    main()