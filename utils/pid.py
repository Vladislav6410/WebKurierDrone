# -*- coding: utf-8 -*-
"""
Простой PID-контроллер для WebKurierDrone.
- Анти-накопление интегральной ошибки (anti-windup)
- Ограничение выходного сигнала
- Плавная производная по измерению (без "кика" по setpoint)
"""

from typing import Optional, Tuple


class PID:
    def __init__(
        self,
        kp: float,
        ki: float,
        kd: float,
        setpoint: float = 0.0,
        output_limits: Tuple[Optional[float], Optional[float]] = (None, None),
        integral_limits: Tuple[Optional[float], Optional[float]] = (None, None),
    ) -> None:
        self.kp = float(kp)
        self.ki = float(ki)
        self.kd = float(kd)
        self.setpoint = float(setpoint)
        self.min_out, self.max_out = output_limits
        self.min_int, self.max_int = integral_limits
        self.reset()

    def reset(self) -> None:
        self._integral = 0.0
        self._prev_meas = None  # для производной по измерению

    @staticmethod
    def _clamp(v: float, lo: Optional[float], hi: Optional[float]) -> float:
        if lo is not None and v < lo:
            return lo
        if hi is not None and v > hi:
            return hi
        return v

    def update(self, measurement: float, dt: float) -> float:
        """
        Обновить контроллер и вернуть управляющий сигнал.
        measurement — текущее измерение процесса.
        dt — шаг времени (сек).
        """
        if dt <= 0:
            raise ValueError("dt must be > 0")

        error = self.setpoint - float(measurement)

        # Интегральная составляющая с ограничением (anti-windup)
        self._integral += error * dt
        self._integral = self._clamp(self._integral, self.min_int, self.max_int)

        # Производная по измерению (уменьшает дергаться при скачке setpoint)
        if self._prev_meas is None:
            d_term = 0.0
        else:
            d_meas = (float(measurement) - self._prev_meas) / dt
            d_term = -d_meas  # знак минус: d(error)/dt = -d(measurement)/dt

        self._prev_meas = float(measurement)

        # Сумма
        u = self.kp * error + self.ki * self._integral + self.kd * d_term
        u = self._clamp(u, self.min_out, self.max_out)
        return u

    # Вспомогательные методы
    def set_setpoint(self, sp: float) -> None:
        self.setpoint = float(sp)

    def tune(self, kp: float, ki: float, kd: float) -> None:
        self.kp, self.ki, self.kd = float(kp), float(ki), float(kd)