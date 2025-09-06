# -*- coding: utf-8 -*-
"""
AutopilotAI — минимальное ядро автопилота (PID) + справочник (Advisor).
✅ Учтено всё из старой версии (AirframeSpec, AutopilotAdvisor: libs, rules, capabilities, mission_presets, checklist).
✅ Добавлено рабочее ядро автопилота с режимами MANUAL/HOLD_ALT/CRUISE, failsafe и мини-симулятором.

Зависимости: utils.pid.PID
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Tuple, List
from utils.pid import PID

# ========================== ЧАСТЬ 1. РАБОЧИЙ АВТОПИЛОТ ==========================

@dataclass
class AltitudeController:
    """Контроллер высоты (барометрический замкнутый контур). Выход: thrust [0..1]."""
    kp: float = 0.9
    ki: float = 0.25
    kd: float = 0.05
    out_min: float = 0.0
    out_max: float = 1.0
    int_min: float = -0.5
    int_max: float = 0.5
    target_alt_m: float = 0.0
    pid: PID = field(init=False)

    def __post_init__(self):
        self.pid = PID(
            kp=self.kp, ki=self.ki, kd=self.kd,
            setpoint=self.target_alt_m,
            output_limits=(self.out_min, self.out_max),
            integral_limits=(self.int_min, self.int_max),
        )

    def set_target(self, alt_m: float) -> None:
        self.target_alt_m = float(alt_m)
        self.pid.set_setpoint(self.target_alt_m)

    def reset(self) -> None:
        self.pid.reset()

    def update(self, baro_alt_m: float, dt: float) -> float:
        thrust = self.pid.update(measurement=baro_alt_m, dt=dt)
        if thrust != thrust:  # NaN guard
            thrust = 0.0
        return max(self.out_min, min(self.out_max, thrust))


@dataclass
class SpeedController:
    """Контроллер воздушной скорости. Выход: pitch [-1..1] (условная нормализация)."""
    kp: float = 0.4
    ki: float = 0.05
    kd: float = 0.02
    out_min: float = -1.0
    out_max: float = 1.0
    int_min: float = -0.2
    int_max: float = 0.2
    target_ms: float = 18.0
    pid: PID = field(init=False)

    def __post_init__(self):
        self.pid = PID(
            kp=self.kp, ki=self.ki, kd=self.kd,
            setpoint=self.target_ms,
            output_limits=(self.out_min, self.out_max),
            integral_limits=(self.int_min, self.int_max),
        )

    def set_target(self, v_ms: float) -> None:
        self.target_ms = float(v_ms)
        self.pid.set_setpoint(self.target_ms)

    def reset(self) -> None:
        self.pid.reset()

    def update(self, airspeed_ms: float, dt: float) -> float:
        pitch_cmd = self.pid.update(measurement=airspeed_ms, dt=dt)
        if pitch_cmd != pitch_cmd:  # NaN guard
            pitch_cmd = 0.0
        return max(self.out_min, min(self.out_max, pitch_cmd))


class Autopilot:
    """
    Мини-ядро автопилота с режимами:
      - MANUAL: pass-through ручных команд
      - HOLD_ALT: удержание высоты
      - CRUISE: удержание высоты + воздушной скорости

    update(...) -> команды на исполнительные механизмы:
      {
        "thrust": 0..1,
        "pitch": -1..1,
        "roll": -1..1,
        "yaw": -1..1,
        "failsafe": bool,
        "failsafe_reason": str,
        "mode": str,
        "targets": {"alt_m": float, "airspeed_ms": float}
      }
    """
    MODES = {"MANUAL", "HOLD_ALT", "CRUISE"}

    def __init__(self):
        self.mode: str = "MANUAL"
        self.alt_ctl = AltitudeController()
        self.spd_ctl = SpeedController()

        # Пороговые значения безопасности
        self.min_batt_v: float = 19.2  # 6S ≈ 3.2В/ячейку
        self.link_timeout_s: float = 2.0
        self._link_timer: float = 0.0

    # ---- Режимы и цели ----
    def set_mode(self, mode: str,
                 target_alt_m: Optional[float] = None,
                 target_airspeed_ms: Optional[float] = None) -> None:
        if mode not in self.MODES:
            raise ValueError(f"Unknown mode: {mode}")
        self.mode = mode
        if target_alt_m is not None:
            self.alt_ctl.set_target(target_alt_m)
        if target_airspeed_ms is not None:
            self.spd_ctl.set_target(target_airspeed_ms)
        self.alt_ctl.reset()
        self.spd_ctl.reset()

    def set_targets(self, alt_m: Optional[float] = None, airspeed_ms: Optional[float] = None) -> None:
        if alt_m is not None:
            self.alt_ctl.set_target(alt_m)
        if airspeed_ms is not None:
            self.spd_ctl.set_target(airspeed_ms)

    # ---- Failsafe ----
    def _failsafe_check(self, sys: Dict[str, Any], sensors: Dict[str, Any]) -> Tuple[bool, str]:
        batt_v: float = float(sys.get("battery_v", 0.0))
        link_ok: bool = bool(sys.get("link_ok", True))
        dt: float = float(sys.get("dt", 0.1))

        if link_ok:
            self._link_timer = 0.0
        else:
            self._link_timer += dt

        baro_alt_m = sensors.get("baro_alt_m", None)

        if batt_v <= 0 or batt_v < self.min_batt_v:
            return True, "LOW_BATTERY"
        if self._link_timer > self.link_timeout_s:
            return True, "LINK_LOSS"
        if baro_alt_m is None or not isinstance(baro_alt_m, (int, float)):
            return True, "BARO_FAULT"
        return False, ""

    # ---- Основной апдейт ----
    def update(self, sensors: Dict[str, Any], sys: Dict[str, Any],
               manual_cmd: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        dt = float(sys.get("dt", 0.1))
        failsafe, reason = self._failsafe_check(sys, sensors)

        out = {
            "thrust": 0.0, "pitch": 0.0, "roll": 0.0, "yaw": 0.0,
            "failsafe": failsafe, "failsafe_reason": reason,
            "mode": self.mode,
            "targets": {"alt_m": self.alt_ctl.target_alt_m, "airspeed_ms": self.spd_ctl.target_ms},
        }

        if failsafe:
            out["thrust"] = 0.3
            out["pitch"] = 0.1
            return out

        if self.mode == "MANUAL":
            cmd = manual_cmd or {}
            out["thrust"] = float(cmd.get("thrust", 0.0))
            out["pitch"]  = float(cmd.get("pitch",  0.0))
            out["roll"]   = float(cmd.get("roll",   0.0))
            out["yaw"]    = float(cmd.get("yaw",    0.0))
            return out

        baro_alt_m: float = float(sensors.get("baro_alt_m", 0.0))
        airspeed_ms: float = float(sensors.get("airspeed", 0.0))

        if self.mode == "HOLD_ALT":
            out["thrust"] = self.alt_ctl.update(baro_alt_m=baro_alt_m, dt=dt)
            out["pitch"] = 0.0
            return out

        if self.mode == "CRUISE":
            out["thrust"] = self.alt_ctl.update(baro_alt_m=baro_alt_m, dt=dt)
            out["pitch"] = self.spd_ctl.update(airspeed_ms=airspeed_ms, dt=dt)
            return out

        return out


# --------- Мини-симуляция для ручных проверок ---------
def _simulate_step(state: Dict[str, float], cmd: Dict[str, float], dt: float) -> Dict[str, float]:
    """
    Игрушечная динамика:
      alt_dot ≈ kT*(thrust - hover) + kP*pitch
      v_dot   ≈ kV*pitch - drag*v
    """
    kT, hover = 6.0, 0.45
    kP = 2.0
    kV, drag = 10.0, 0.12

    alt = state["alt_m"]
    v = state["airspeed"]

    alt_dot = kT * (cmd["thrust"] - hover) + kP * cmd["pitch"]
    v_dot = kV * cmd["pitch"] - drag * v

    alt = max(0.0, alt + alt_dot * dt)
    v = max(0.0, v + v_dot * dt)

    state["alt_m"] = alt
    state["airspeed"] = v
    return state


def demo_cruise(seconds: float = 20.0, dt: float = 0.1, target_alt: float = 50.0, target_ms: float = 18.0) -> None:
    ap = Autopilot()
    ap.set_mode("CRUISE", target_alt_m=target_alt, target_airspeed_ms=target_ms)

    state = {"alt_m": 0.0, "airspeed": 0.0}
    for _ in range(int(seconds / dt)):
        sensors = {"baro_alt_m": state["alt_m"], "airspeed": state["airspeed"]}
        sys = {"dt": dt, "battery_v": 23.5, "link_ok": True}
        cmd = ap.update(sensors, sys)
        state = _simulate_step(state, cmd, dt)

    print(f"[CRUISE DEMO] alt={state['alt_m']:.1f} m, airspeed={state['airspeed']:.1f} m/s, "
          f"targets={ap.alt_ctl.target_alt_m}/{ap.spd_ctl.target_ms}")

# ======================= ЧАСТЬ 2. СПРАВОЧНИК (СТАРЫЙ МОДУЛЬ) =======================
# (сохранён без потерь; можно использовать параллельно с Autopilot)

@dataclass
class AirframeSpec:
    model: str = "FIXAR 007 NG"
    vtol: bool = True
    wingspan_mm: int = 1620
    mtow_kg: float = 7.0
    payload_kg: float = 2.0
    cruise_ms: float = 18.0
    max_ms: float = 24.0
    max_alt_asl_m: int = 6115
    max_wind_ms: float = 15.0
    ip_rate: str = "IP54"
    battery: str = "Li-Ion 25V 27Ah"
    gps_denied_basic: str = "IMU-based"
    gps_denied_advanced: str = "CV+AI nav"
    autopilot: str = "FIXAR Autopilot 2.0 (proprietary)"
    gcs: str = "FIXAR xGroundControl (proprietary)"


@dataclass
class AutopilotAdvisor:
    """Справочник по возможностям/ПО/миссиям для класса FIXAR."""
    spec: AirframeSpec = field(default_factory=AirframeSpec)

    def recommended_libs(self) -> Dict[str, List[str]]:
        return {
            "core_flight_stack": [
                "ArduPilot / PX4 (C++/NuttX, uORB/MAVLink)",
                "MAVSDK (Python/C++)", "pymavlink"
            ],
            "nav_estimation": [
                "filterpy (EKF/UKF)", "numpy", "scipy", "pymap3d"
            ],
            "computer_vision_ai": [
                "OpenCV", "ultralytics/YOLO", "onnxruntime", "torch",
                "RTAB-Map или ORB-SLAM3 (SLAM)"
            ],
            "lidar_depth": ["open3d", "pcl (C++)", "lidarview/io parsers"],
            "routing_geodesy": ["shapely", "geopandas", "pyproj", "rasterio"],
            "terrain_follow": ["GDAL", "SRTM/DSM readers", "scipy.interpolate"],
            "telemetry_ui": ["Flask/FastAPI", "websockets", "plotly dash (опц.)"],
            "safety_compliance": ["jsonschema (SORA forms)", "pydantic"]
        }

    def flight_rules_eu(self) -> Dict[str, str]:
        return {
            "category": "Specific (по умолчанию для BVLOS/VTOL коммерческих миссий)",
            "method": "SORA 10 steps + Operational Authorisation",
            "remote_id": "Обязателен с 01.01.2024 (DRI/Remote ID)",
            "adsb_remote_id_note": "ADSB/Remote ID опционально/по сценарию; следуйте NAA/UTM",
        }

    def capabilities(self) -> Dict[str, List[str]]:
        return {
            "autonomy": [
                "Автономный взлёт/посадка VTOL",
                "Автономный полёт по миссии (area/waypoints)",
                "Переход VTOL↔крейсер (fixed-wing)",
                "Полёт без компаса (устойчив к магнитным помехам)",
                "Работа при GPS-помехах: IMU-fallback; расширенный режим CV+AI",
                "Черный ящик/логирование (BlackBox аналог)"
            ],
            "safety": [
                "Terrain following: LiDAR-базир. коррекция AGL на малых высотах",
                "Failsafe: RTH/hold/land по триггерам",
                "Ограничение по ветру/скорости/углам атаки"
            ],
            "manual_supervision": [
                "Ручное вмешательство через GCS",
                "Быстрая развёртка (≈5 мин) для выезда"
            ]
        }

    def aerobatics_policy(self) -> Dict[str, List[str]]:
        return {
            "not_allowed": [
                "Петля (loop), бочка (roll), штопор, иммельман, перевёрнутый полёт"
            ],
            "allowed_training_patterns": [
                "Широкие развороты, восьмёрка на высоте, орбита (loiter)",
                "Плавные набор/снижение, S-кривые для калибровки"
            ],
            "reason": [
                "Рабочая платформа VTOL для картографии/инспекций, не аэрошоу",
                "Риск перегрузок и срыва потока на крыле с полезной нагрузкой"
            ]
        }

    def mission_presets(self) -> Dict[str, Dict]:
        return {
            "mapping_area": {
                "pattern": "lawnmower", "overlap": {"front": 75, "side": 65},
                "gsd_control": True, "terrain_follow": True,
                "cruise_ms": min(18.0, self.spec.cruise_ms)
            },
            "corridor_inspection": {
                "pattern": "corridor", "buffer_m": 50, "terrain_follow": True,
                "sensors": ["RGB", "Thermal", "LiDAR"]
            },
            "surveillance_patrol": {
                "pattern": "waypoints+loiter", "on_event": "revisit/spiral",
                "geofences": ["keep-in", "no-fly"]
            },
            "delivery_drop": {
                "vtol_only_zone": True, "precision_land": True,
                "failsafe": "abort_and_RTH_if_accuracy<1.5m"
            }
        }

    def preflight_checklist(self) -> List[str]:
        return [
            "Оценить SORA/авторизацию NAA; активен Remote ID",
            "Погода: ветер ≤ 15 м/с, дождь/пыли по IP54",
            "Батарея 25V 27Ah заряжена; расчёт энергии по профилю миссии",
            "LiDAR/баро/IMU калиброваны; GNSS/RTK (если есть) готов",
            "Геозоны/нотамы проверены; связь устойчива",
            "Параметры камеры/GSD заданы; payload ≤ 2 кг; MTOW ≤ 7 кг"
        ]


if __name__ == "__main__":
    # Быстрый smoke-тест обоих блоков
    advisor = AutopilotAdvisor()
    print("CAPABILITIES:", advisor.capabilities())
    print("LIBS:", advisor.recommended_libs())
    print("EU RULES:", advisor.flight_rules_eu())
    print("AEROBATICS:", advisor.aerobatics_policy())
    print("PRESETS:", advisor.mission_presets())
    print("PREFLIGHT:", advisor.preflight_checklist())

    # Мини-демо крейза
    demo_cruise()