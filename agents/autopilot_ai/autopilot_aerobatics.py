# -*- coding: utf-8 -*-
"""
Высший пилотаж (без обязательной миссии проекта).
Аккуратно: только безопасные фигуры для платформ VTOL/Mapping:
 - orbit (радиус, угловая скорость)
 - figure_eight (восьмёрка) — последовательность дуг
 - s_curve (S-кривая)
 - loiter (зависание по кругу/точке)

НЕ выполняем трюки класса loop/roll/inverted — для картографических UAV это риск.
"""
from dataclasses import dataclass
from typing import Dict, Any, Optional
from .autopilot_basic import Autopilot as BaseAutopilot

@dataclass
class OrbitParams:
    radius_m: float = 60.0
    yaw_rate_dps: float = 8.0   # для внешнего слоя/ориентации

class AerobaticsAutopilot(BaseAutopilot):
    def __init__(self):
        super().__init__()
        self.profile: Optional[str] = None
        self._orbit = OrbitParams()

    def set_profile(self, profile: str, **kwargs):
        """
        profile: "orbit"|"figure_eight"|"s_curve"|"loiter"
        kwargs:   параметры профиля, например radius_m для orbit
        """
        self.profile = profile
        if profile == "orbit" and "radius_m" in kwargs:
            self._orbit.radius_m = float(kwargs["radius_m"])

    def update(self, sensors: Dict[str, Any], sys: Dict[str, Any],
               manual_cmd: Optional[Dict[str,float]]=None):
        out = super().update(sensors, sys, manual_cmd)
        if out.get("failsafe"):  # при аварии — поведение базового АП
            return out
        # Пилотажные профили управляют «pitch» (чуть) и подразумевают внешний слой course/roll.
        if self.profile == "orbit" and self.mode in {"HOLD_ALT","CRUISE"}:
            # лёгкий «нос» для удержания координат по внешнему слою, здесь только пример
            out["pitch"] += 0.02
        elif self.profile == "figure_eight" and self.mode in {"HOLD_ALT","CRUISE"}:
            out["pitch"] += 0.03
        elif self.profile == "s_curve" and self.mode in {"HOLD_ALT","CRUISE"}:
            out["pitch"] += 0.025
        elif self.profile == "loiter" and self.mode in {"HOLD_ALT","CRUISE"}:
            out["pitch"] += 0.01
        return out