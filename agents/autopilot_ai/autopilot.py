# -*- coding: utf-8 -*-
"""
AutopilotAI — единый модуль:
  • Ядро автопилота (PID) с режимами: MANUAL / HOLD_ALT / CRUISE / RTL / LAND
  • Failsafe-профили: LOW_BATTERY→LAND, LINK_LOSS→RTL, BARO_FAULT→HOLD_ALT, NO_RTK→degrade
  • Terrain-follow (AGL) + keep-in геозона + домашняя точка (RTL)
  • Мини-симулятор динамики и демо
  • Advisor (AirframeSpec, справочник: libs, rules, capabilities, mission_presets, checklist)

Зависимости: utils.pid.PID  (и опц.: utils.gsd, utils.terrain — можно подключить позже)
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Tuple, List
from math import hypot
from utils.pid import PID

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  NEW: COMPLIANCE CHECK — ПРОВЕРКА СООТВЕТСТВИЯ UAS ZONES                 ║
# ╚══════════════════════════════════════════════════════════════════════════╝
from shapely.geometry import Polygon
from agents.compliance.uas_zones_loader import load_zones
from agents.compliance.uas_zones_check import check_polygon_against_zones

def ensure_zone_compliance(poly_coords_latlon, zone_files):
    """
    Проверка миссии на пересечение с запретными/ограниченными зонами.
    
    Args:
        poly_coords_latlon: список координат [(lat, lon), ...]
        zone_files: список путей к файлам с геозонами (GeoJSON/GeoPackage)
    
    Raises:
        RuntimeError: если маршрут пересекает запретные зоны
    """
    # poly_coords_latlon = [(lat, lon), ...]
    mission_poly = Polygon([(lon, lat) for (lat, lon) in poly_coords_latlon])
    zones = load_zones(zone_files)
    hits = check_polygon_against_zones(mission_poly, zones)
    if hits:
        names = ", ".join(h["zone"] for h in hits)
        raise RuntimeError(
            f"Маршрут пересекает запретные/ограниченные зоны: {names}. "
            f"Скорректируйте полигон или получите разрешение."
        )
# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  КОНЕЦ СЕКЦИИ COMPLIANCE CHECK                                           ║
# ╚══════════════════════════════════════════════════════════════════════════╝


# ========================== КОНТРОЛЛЕРЫ ==========================
@dataclass
class AltitudeController:
    """Удержание высоты (баро). Выход: thrust [0..1]."""
    kp: float = 0.9
    ki: float = 0.25
    kd: float = 0.05
    out_min: float = 0.0
    out_max: float = 1.0
    int_min: float = -0.5
    int_max: float = 0.5
    target_alt_m: float = 0.0
    hover_ff: float = 0.45  # feed-forward на «висение/крейз»
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
        u = self.pid.update(measurement=baro_alt_m, dt=dt)
        if u != u:  # NaN guard
            u = 0.0
        thrust = self.hover_ff + 0.8 * (u - 0.5)
        return max(self.out_min, min(self.out_max, thrust))


@dataclass
class SpeedController:
    """Удержание воздушной скорости. Выход: pitch [-1..1]."""
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


# ========================== ВСПОМОГАТЕЛИ ==========================
@dataclass
class Geofence:
    """Keep-in геозона: круг (lat0, lon0, radius_m). Упрощённая локальная проекция."""
    lat0: float
    lon0: float
    radius_m: float

    def inside(self, lat: float, lon: float) -> bool:
        dx = (lon - self.lon0) * 111320.0 * 0.6  # грубо по долготе
        dy = (lat - self.lat0) * 111320.0
        return hypot(dx, dy) <= self.radius_m


@dataclass
class TerrainFollower:
    """Целевой уровень: target_agl_m + terrain_elev."""
    target_agl_m: float = 60.0  # ← базовая высота AGL (можно менять под миссию)

    def target_asl(self, terrain_elev_m: float) -> float:
        return terrain_elev_m + self.target_agl_m


# ========================== АВТОПИЛОТ (ЯДРО) ==========================
class Autopilot:
    """
    Режимы:
      MANUAL — ручное управление
      HOLD_ALT — удержание высоты
      CRUISE — высота + скорость
      RTL — возврат домой
      LAND — посадка
    """
    MODES = {"MANUAL", "HOLD_ALT", "CRUISE", "RTL", "LAND"}

    def __init__(self):
        self.mode: str = "MANUAL"
        self.alt_ctl = AltitudeController()
        self.spd_ctl = SpeedController()

        # Безопасность
        self.min_batt_v: float = 19.2     # 6S≈3.2В/ячейку
        self.link_timeout_s: float = 2.0
        self._link_timer: float = 0.0
        self.require_rtk: bool = False

        # Геозона/рельеф
        self.keepin: Optional[Geofence] = None
        self.terrain = TerrainFollower(target_agl_m=60.0)
        self.use_terrain: bool = True

        # Дом для RTL
        self.home: Optional[Tuple[float, float, float]] = None  # lat, lon, alt_asl_m

    # ---- Публичный API ----
    def set_home(self, lat: float, lon: float, alt_asl_m: float) -> None:
        self.home = (float(lat), float(lon), float(alt_asl_m))

    def set_geofence(self, lat: float, lon: float, radius_m: float) -> None:
        self.keepin = Geofence(lat, lon, radius_m)

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
        batt_v = float(sys.get("battery_v", 0.0))
        link_ok = bool(sys.get("link_ok", True))
        dt = float(sys.get("dt", 0.1))
        rtk_fix = bool(sensors.get("rtk_fix", True))  # True = RTK fixed/float
        baro_alt_m = sensors.get("baro_alt_m", None)

        self._link_timer = 0.0 if link_ok else (self._link_timer + dt)

        if batt_v <= 0 or batt_v < self.min_batt_v:
            return True, "LOW_BATTERY"
        if self._link_timer > self.link_timeout_s:
            return True, "LINK_LOSS"
        if baro_alt_m is None or not isinstance(baro_alt_m, (int, float)):
            return True, "BARO_FAULT"
        if self.require_rtk and not rtk_fix:
            return True, "NO_RTK"
        return False, ""

    # ---- Основной апдейт ----
    def update(self, sensors: Dict[str, Any], sys: Dict[str, Any],
               manual_cmd: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        dt = float(sys.get("dt", 0.1))
        failsafe, reason = self._failsafe_check(sys, sensors)

        # Terrain-follow (если включён и режим требует высоты)
        terrain_elev_m = float(sensors.get("terrain_elev_m", 0.0))
        if self.use_terrain and self.mode in {"HOLD_ALT", "CRUISE"}:
            self.alt_ctl.set_target(self.terrain.target_asl(terrain_elev_m))

        out = {
            "thrust": 0.0, "pitch": 0.0, "roll": 0.0, "yaw": 0.0,
            "failsafe": failsafe, "failsafe_reason": reason,
            "mode": self.mode,
            "targets": {"alt_m": self.alt_ctl.target_alt_m, "airspeed_ms": self.spd_ctl.target_ms},
        }

        # Профили поведения при авариях
        if failsafe:
            if reason == "LOW_BATTERY":
                self.mode = "LAND"
            elif reason == "LINK_LOSS":
                self.mode = "RTL" if self.home else "HOLD_ALT"
            elif reason == "BARO_FAULT":
                self.mode = "HOLD_ALT"
            elif reason == "NO_RTK":
                # деградация: продолжаем без остановки миссии, но метим reason
                pass

        # Геозона: выход => RTL (если не LAND)
        lat, lon = float(sensors.get("lat", 0.0)), float(sensors.get("lon", 0.0))
        if self.keepin and not self.keepin.inside(lat, lon) and self.mode != "LAND":
            self.mode = "RTL"

        # Данные сенсоров
        baro_alt_m = float(sensors.get("baro_alt_m", 0.0))
        airspeed_ms = float(sensors.get("airspeed", 0.0))

        # Режимы
        if self.mode == "MANUAL":
            cmd = manual_cmd or {}
            out["thrust"] = float(cmd.get("thrust", 0.0))
            out["pitch"]  = float(cmd.get("pitch",  0.0))
            out["roll"]   = float(cmd.get("roll",   0.0))
            out["yaw"]    = float(cmd.get("yaw",    0.0))
            return out

        if self.mode == "HOLD_ALT":
            out["thrust"] = self.alt_ctl.update(baro_alt_m, dt)
            out["pitch"] = 0.0
            return out

        if self.mode == "CRUISE":
            out["thrust"] = self.alt_ctl.update(baro_alt_m, dt)
            out["pitch"]  = self.spd_ctl.update(airspeed_ms, dt)
            return out

        if self.mode == "RTL":
            # Упрощённо: держим высоту, слегка «тянем» нос (возврат по курсу реализуется на внешнем слое)
            out["thrust"] = self.alt_ctl.update(baro_alt_m, dt)
            out["pitch"]  = 0.15
            return out

        if self.mode == "LAND":
            # Примитивная посадка: ступенчатое снижение
            self.alt_ctl.set_target(max(0.0, self.alt_ctl.target_alt_m - 0.6))  # ≈0.6 м/шаг
            out["thrust"] = max(0.2, self.alt_ctl.update(baro_alt_m, dt) - 0.1)
            out["pitch"] = -0.05
            return out

        return out


# ========================== МИНИ-СИМУЛЯТОР ==========================
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


def demo_cruise(seconds: float = 20.0, dt: float = 0.1,
                target_agl: float = 60.0, terrain_elev_m: float = 140.0) -> None:
    """
    Демо: CRUISE с terrain-follow. Итоговая цель ≈ terrain + AGL.
    """
    ap = Autopilot()
    ap.use_terrain = True
    ap.set_mode("CRUISE", target_alt_m=terrain_elev_m + target_agl, target_airspeed_ms=18.0)

    state = {"alt_m": terrain_elev_m, "airspeed": 0.0}
    for _ in range(int(seconds / dt)):
        sensors = {
            "baro_alt_m": state["alt_m"], "airspeed": state["airspeed"],
            "terrain_elev_m": terrain_elev_m, "lat": 52.12, "lon": 13.45, "rtk_fix": True
        }
        sys = {"dt": dt, "battery_v": 23.5, "link_ok": True}
        cmd = ap.update(sensors, sys)
        state = _simulate_step(state, cmd, dt)

    print(f"[CRUISE DEMO] alt={state['alt_m']:.1f} m, v={state['airspeed']:.1f} m/s, mode={ap.mode}, "
          f"targets={ap.alt_ctl.target_alt_m:.1f}/{ap.spd_ctl.target_ms:.1f}")


# ========================== СПРАВОЧНИК (ADVISOR) ==========================
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
            "safety_compliance": ["jsonschema (SORA forms), pydantic"]
        }

    def flight_rules_eu(self) -> Dict[str, str]:
        return {
            "category": "Specific (BVLOS/VTOL коммерческие миссии)",
            "method": "SORA 10 steps + Operational Authorisation",
            "remote_id": "Обязателен с 01.01.2024 (DRI/Remote ID)",
            "adsb_remote_id_note": "ADSB/Remote ID по сценарию; следуйте NAA/UTM",
        }

    def capabilities(self) -> Dict[str, List[str]]:
        return {
            "autonomy": [
                "Автономный взлёт/посадка VTOL",
                "Миссия (area/waypoints) + переход VTOL↔fixed-wing",
                "Полёт без компаса (стойкость к магнитным помехам)",
                "IMU-fallback при GPS-помехах; CV+AI режим расширенно",
                "Черный ящик/логирование"
            ],
            "safety": [
                "Terrain-follow (LiDAR/DSM коррекция AGL)",
                "Failsafe: RTH/hold/land по триггерам",
                "Ограничения по ветру/скорости/углам атаки"
            ],
            "manual_supervision": [
                "Ручное вмешательство через GCS",
                "Быстрая развёртка (~5 мин)"
            ]
        }

    def aerobatics_policy(self) -> Dict[str, List[str]]:
        return {
            "not_allowed": ["Loop, Roll, Stall/Spin, Immelmann, Inverted"],
            "allowed_training_patterns": [
                "Широкие развороты, восьмёрка, орбита (loiter)",
                "Плавный набор/снижение, S-кривые"
            ],
            "reason": [
                "Рабочая платформа VTOL (картография/инспекции), не аэрошоу",
                "Риск перегрузок/срыва потока на крыле с payload"
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
            "SORA/авторизация NAA подтверждена; Remote ID активен",
            "Погода: ветер ≤ 15 м/с; соответствие IP-рейтингу",
            "Батарея 25V 27Ah заряжена; расчёт энергии по профилю миссии",
            "LiDAR/баро/IMU калиброваны; GNSS/RTK готов",
            "Геозоны/NOTAM проверены; связь устойчива",
            "Параметры камеры/GSD заданы; payload ≤ 2 кг; MTOW ≤ 7 кг"
        ]


# ========================== СТАРТЕР (SMOKE-TEST) ==========================
if __name__ == "__main__":
    # Advisor вывод
    advisor = AutopilotAdvisor()
    print("CAPABILITIES:", advisor.capabilities())
    print("LIBS:", advisor.recommended_libs())
    print("EU RULES:", advisor.flight_rules_eu())
    print("AEROBATICS:", advisor.aerobatics_policy())
    print("PRESETS:", advisor.mission_presets())
    print("PREFLIGHT:", advisor.preflight_checklist())

    # Демо крейза (terrain-follow: 140 м террейн + 60 м AGL = цель ~200 м ASL)
    demo_cruise()