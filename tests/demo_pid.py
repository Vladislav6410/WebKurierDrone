# -*- coding: utf-8 -*-
"""
Демонстрация работы PID-контроллера на упрощённой модели 1-го порядка.
Печатается динамика: шаг, значение x, управляющий сигнал u, ошибка.
"""

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
    alpha = 0.05  # коэффициент реакции "системы"

    print(f"{'t':>4} {'x':>8} {'u':>8} {'error':>8}")
    print("-" * 32)

    for step in range(50):
        u = pid.update(x, dt)
        x += alpha * u
        error = pid.setpoint - x
        print(f"{step*dt:4.1f} {x:8.3f} {u:8.3f} {error:8.3f}")

if __name__ == "__main__":
    main()