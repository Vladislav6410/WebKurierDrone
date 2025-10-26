# -*- coding: utf-8 -*-
"""
Высший пилотаж (без обязательной миссии проекта).
Допустимы только безопасные фигуры для VTOL/Mapping:
 - orbit (радиус, угловая скорость/скорость обхода)
 - figure_eight (восьмёрка — две полуокружности)
 - s_curve (S-кривая)
 - loiter (висение/кружение на месте)

⚠️ Не выполняем трюки уровня loop/roll/inverted.

Архитектура:
 - Наследуемся от базового Autopilot (autopilot_basic.Autopilot)
 - Профили пилотажа задают «намеки» внешнему слою курса (course_offset_deg) и
   мягко подмешивают «pitch» (±0.0x), не выходя за лимиты.
 - При failsafe/выходе из геозоны — возвращаем поведение базового АП, пилотаж отключается.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Optional
from math import pi, sin, cos

from .autopilot_basic import Autopilot as BaseAutopilot


# ───────────────────────── Параметры профилей ─────────────────────────

@dataclass
class OrbitParams:
    radius_m: float = 60.0          # радиус орбиты
    omega_deg_s: float = 12.0       # угловая скорость (°/с)
    pitch_bias: float = 0.02        # мягкий подхват тангажа

@dataclass
class FigureEightParams:
    radius_m: float = 50.0
    omega_deg_s: float = 14.0
    pitch_bias: float = 0.03

@dataclass
class SCurveParams:
    amplitude_m: float = 40.0       # «размах» S-кривой
    period_s: float = 20.0          # период изменения
    pitch_bias: float = 0.025

@dataclass
class LoiterParams:
    pitch_bias: float = 0.01        # минимальный подхват
    orbit_radius_m: float = 0.0     # 0 = точка; >0 = маленький кружок
    omega_deg_s: float = 15.0


# ───────────────────────── Аэробатический АП ─────────────────────────

class AerobaticsAutopilot(BaseAutopilot):
    """
    Профили:
      - "orbit"
      - "figure_eight"
      - "s_curve"
      - "loiter"
    """
    SAFE_PITCH_LIMIT = 0.10   # абсолютный предел подмешивания тангажа

    def __init__(self):
        super().__init__()
        self.profile: Optional[str] = None
        self._orbit = OrbitParams()
        self._eight = FigureEightParams()
        self._s = SCurveParams()
        self._loiter = LoiterParams()

        # внутренняя фаза для непрерывных фигур
        self._phase_rad: float = 0.0

    # ――― Настройка профиля ―――
    def set_profile(self, profile: str, **kwargs):
        """
        profile ∈ {"orbit","figure_eight","s_curve","loiter"}
        kwargs — переопределение параметров профиля, например:
          radius_m=80, omega_deg_s=10, pitch_bias=0.02 ...
        """
        profile = str(profile).lower().strip()
        if profile not in {"orbit", "figure_eight", "s_curve", "loiter"}:
            raise ValueError(f"Unknown aerobatics profile: {profile}")

        self.profile = profile
        self._phase_rad = 0.0  # сброс фазы при смене профиля

        # применяем параметры
        target = {
            "orbit": self._orbit,
            "figure_eight": self._eight,
            "s_curve": self._s,
            "loiter": self._loiter,
        }[profile]
        for k, v in kwargs.items():
            if hasattr(target, k):
                setattr(target, k, float(v))

    # ――― Основной апдейт ―――
    def update(self, sensors: Dict[str, Any], sys: Dict[str, Any],
               manual_cmd: Optional[Dict[str, float]] = None) -> Dict[str, Any]:

        dt = float(sys.get("dt", 0.1))
        out = super().update(sensors, sys, manual_cmd)

        # если базовый АП в failsafe/RTL/LAND — пилотаж не вмешивается
        if out.get("failsafe") or self.mode in {"RTL", "LAND"}:
            return out

        # пилотаж активен только в удерживающих режимах
        if self.profile and self.mode in {"HOLD_ALT", "CRUISE"}:
            # что отдаём внешнему слою: desired course offset (градусы)
            course_offset_deg = 0.0
            added_pitch = 0.0

            if self.profile == "orbit":
                course_offset_deg, added_pitch = self._do_orbit(dt)

            elif self.profile == "figure_eight":
                course_offset_deg, added_pitch = self._do_figure_eight(dt)

            elif self.profile == "s_curve":
                course_offset_deg, added_pitch = self._do_s_curve(dt)

            elif self.profile == "loiter":
                course_offset_deg, added_pitch = self._do_loiter(dt)

            # подмешиваем ограниченно
            out["pitch"] = self._clamp(out.get("pitch", 0.0) + added_pitch,
                                       -self.SAFE_PITCH_LIMIT, self.SAFE_PITCH_LIMIT)

            # подсказка внешнему слою (планировщик курса/крен)
            out.setdefault("guidance", {})
            out["guidance"]["course_offset_deg"] = course_offset_deg

        return out

    # ――― Реализация профилей ―――
    def _do_orbit(self, dt: float) -> tuple[float, float]:
        # фаза по угловой скорости
        self._phase_rad += (self._orbit.omega_deg_s * pi / 180.0) * dt
        # смещение курса ~90° к радиальному вектору, здесь возвращаем просто «крутить» вправо
        course_offset_deg = +90.0  # внешняя система пусть интерпретирует как орбиту вокруг текущей цели
        return course_offset_deg, self._orbit.pitch_bias

    def _do_figure_eight(self, dt: float) -> tuple[float, float]:
        # восьмёрка: медленная синусоида курса с переходом знака
        self._phase_rad += (self._eight.omega_deg_s * pi / 180.0) * dt
        # курс гуляет от -90 до +90
        course_offset_deg = 90.0 * sin(self._phase_rad)
        return course_offset_deg, self._eight.pitch_bias

    def _do_s_curve(self, dt: float) -> tuple[float, float]:
        # S-кривая: боковое отклонение по синусу, курс компенсируем пропорционально производной
        self._phase_rad += (2 * pi / max(1e-3, self._s.period_s)) * dt
        # производная синуса = косинус → поворот курса
        course_offset_deg = 45.0 * cos(self._phase_rad)
        return course_offset_deg, self._s.pitch_bias

    def _do_loiter(self, dt: float) -> tuple[float, float]:
        # loiter по точке: минимальные изменения; по маленькому радиусу — как orbit, но быстрее
        if self._loiter.orbit_radius_m > 0.0:
            self._phase_rad += (self._loiter.omega_deg_s * pi / 180.0) * dt
            course_offset_deg = +90.0
        else:
            course_offset_deg = 0.0
        return course_offset_deg, self._loiter.pitch_bias

    # ――― Утилиты ―――
    @staticmethod
    def _clamp(x: float, a: float, b: float) -> float:
        return a if x < a else b if x > b else x