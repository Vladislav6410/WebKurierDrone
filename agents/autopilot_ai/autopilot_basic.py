# -*- coding: utf-8 -*-
"""
Базовый автопилот для миссий (легковесный).
Режимы: MANUAL / HOLD_ALT / CRUISE / RTL / LAND
Failsafe: LOW_BATTERY→LAND, LINK_LOSS→RTL, BARO_FAULT→HOLD_ALT, NO_RTK→degrade
Функции: terrain-follow (AGL), keep-in геозона, RTL к дому.
Проверка UAS-зон выполняется снаружи через check_mission_zones().
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Tuple
from math import hypot

# ───────────────────────── PID (встроенный, чтобы не тянуть utils.pid) ─────────────────────────
@dataclass
class _PID:
    kp: float
    ki: float
    kd: float
    setpoint: float
    output_limits: Tuple[float, float] = (-1.0, 1.0)
    integral_limits: Tuple[float, float] = (-1.0, 1.0)
    _i: float = 0.0
    _prev: Optional[float] = None

    def set_setpoint(self, sp: float) -> None:
        self.setpoint = float(sp)

    def reset(self) -> None:
        self._i = 0.0
        self._prev = None

    def update(self, measurement: float, dt: float) -> float:
        err = self.setpoint - float(measurement)
        self._i += err * dt
        self._i = max(self.integral_limits[0], min(self.integral_limits[1], self._i))
        d = 0.0 if self._prev is None else (err - self._prev) / max(1e-6, dt)
        self._prev = err
        u = self.kp * err + self.ki * self._i + self.kd * d
        return max(self.output_limits[0], min(self.output_limits[1], u))

# ───────────────────────── Контроллеры ─────────────────────────
@dataclass
class AltitudeController:
    kp: float = 0.9;  ki: float = 0.25; kd: float = 0.05
    out_min: float = 0.0; out_max: float = 1.0
    int_min: float = -0.5; int_max: float = 0.5
    target_alt_m: float = 0.0
    hover_ff: float = 0.45
    pid: _PID = field(init=False)

    def __post_init__(self):
        self.pid = _PID(self.kp, self.ki, self.kd, self.target_alt_m,
                        (self.out_min, self.out_max), (self.int_min, self.int_max))

    def set_target(self, alt_m: float) -> None:
        self.target_alt_m = float(alt_m); self.pid.set_setpoint(self.target_alt_m)

    def reset(self) -> None: self.pid.reset()

    def update(self, baro_alt_m: float, dt: float) -> float:
        u = self.pid.update(baro_alt_m, dt)
        # простая модель тяги вокруг «hover_ff»
        thrust = self.hover_ff + 0.8 * (u - 0.5)
        return max(self.out_min, min(self.out_max, thrust))

@dataclass
class SpeedController:
    kp: float = 0.4;  ki: float = 0.05; kd: float = 0.02
    out_min: float = -1.0; out_max: float = 1.0
    int_min: float = -0.2; int_max: float = 0.2
    target_ms: float = 18.0
    pid: _PID = field(init=False)

    def __post_init__(self):
        self.pid = _PID(self.kp, self.ki, self.kd, self.target_ms,
                        (self.out_min, self.out_max), (self.int_min, self.int_max))

    def set_target(self, v_ms: float) -> None:
        self.target_ms = float(v_ms); self.pid.set_setpoint(self.target_ms)

    def reset(self) -> None: self.pid.reset()

    def update(self, airspeed_ms: float, dt: float) -> float:
        pitch_cmd = self.pid.update(airspeed_ms, dt)
        return max(self.out_min, min(self.out_max, pitch_cmd))

# ───────────────────────── Вспомогательные ─────────────────────────
@dataclass
class Geofence:
    """Простая keep-in окружность (lat0, lon0, radius_m)."""
    lat0: float; lon0: float; radius_m: float
    def inside(self, lat: float, lon: float) -> bool:
        dx = (lon - self.lon0) * 111320.0 * 0.6
        dy = (lat - self.lat0) * 111320.0
        return hypot(dx, dy) <= self.radius_m

@dataclass
class TerrainFollower:
    """Целевая высота = terrain_elev + target_agl_m."""
    target_agl_m: float = 60.0
    def target_asl(self, terrain_elev_m: float) -> float:
        return float(terrain_elev_m) + self.target_agl_m

# ───────────────────────── Базовый автопилот ─────────────────────────
class Autopilot:
    MODES = {"MANUAL","HOLD_ALT","CRUISE","RTL","LAND"}

    def __init__(self):
        self.mode: str = "MANUAL"
        self.alt_ctl = AltitudeController()
        self.spd_ctl = SpeedController()

        # Безопасность
        self.min_batt_v: float = 19.2
        self.link_timeout_s: float = 2.0
        self._link_timer: float = 0.0
        self.require_rtk: bool = False

        # Геозона/рельеф
        self.keepin: Optional[Geofence] = None
        self.terrain = TerrainFollower(target_agl_m=60.0)
        self.use_terrain: bool = True

        # Дом (lat, lon, alt_asl_m)
        self.home: Optional[Tuple[float, float, float]] = None

    # ---- API ----
    def set_home(self, lat: float, lon: float, alt_asl_m: float) -> None:
        self.home = (float(lat), float(lon), float(alt_asl_m))

    def set_geofence(self, lat: float, lon: float, radius_m: float) -> None:
        self.keepin = Geofence(lat, lon, radius_m)

    def set_mode(self, mode: str,
                 target_alt_m: Optional[float]=None,
                 target_airspeed_ms: Optional[float]=None) -> None:
        if mode not in self.MODES:
            raise ValueError(f"Unknown mode: {mode}")
        self.mode = mode
        if target_alt_m is not None: self.alt_ctl.set_target(target_alt_m)
        if target_airspeed_ms is not None: self.spd_ctl.set_target(target_airspeed_ms)
        self.alt_ctl.reset(); self.spd_ctl.reset()

    def set_targets(self, alt_m: Optional[float]=None, airspeed_ms: Optional[float]=None) -> None:
        if alt_m is not None: self.alt_ctl.set_target(alt_m)
        if airspeed_ms is not None: self.spd_ctl.set_target(airspeed_ms)

    # ---- Failsafe ----
    def _failsafe_check(self, sys: Dict[str, Any], sensors: Dict[str, Any]):
        batt_v   = float(sys.get("battery_v", 0.0))
        link_ok  = bool(sys.get("link_ok", True))
        dt       = float(sys.get("dt", 0.1))
        rtk_fix  = bool(sensors.get("rtk_fix", True))
        baro_ok  = isinstance(sensors.get("baro_alt_m", None), (int, float))

        self._link_timer = 0.0 if link_ok else (self._link_timer + dt)

        if batt_v <= 0 or batt_v < self.min_batt_v: return True, "LOW_BATTERY"
        if self._link_timer > self.link_timeout_s:  return True, "LINK_LOSS"
        if not baro_ok:                              return True, "BARO_FAULT"
        if self.require_rtk and not rtk_fix:        return True, "NO_RTK"
        return False, ""

    # ---- Основной апдейт ----
    def update(self, sensors: Dict[str, Any], sys: Dict[str, Any],
               manual_cmd: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        dt = float(sys.get("dt", 0.1))
        failsafe, reason = self._failsafe_check(sys, sensors)

        # Terrain-follow при режимах, где держим высоту
        terrain_elev_m = float(sensors.get("terrain_elev_m", 0.0))
        if self.use_terrain and self.mode in {"HOLD_ALT","CRUISE"}:
            self.alt_ctl.set_target(self.terrain.target_asl(terrain_elev_m))

        out = {
            "thrust": 0.0, "pitch": 0.0, "roll": 0.0, "yaw": 0.0,
            "failsafe": failsafe, "failsafe_reason": reason, "mode": self.mode,
            "targets": {"alt_m": self.alt_ctl.target_alt_m, "airspeed_ms": self.spd_ctl.target_ms},
        }

        # Поведение при авариях
        if failsafe:
            if   reason == "LOW_BATTERY": self.mode = "LAND"
            elif reason == "LINK_LOSS":   self.mode = "RTL" if self.home else "HOLD_ALT"
            elif reason == "BARO_FAULT":  self.mode = "HOLD_ALT"

        # Keep-in геозона → RTL
        lat, lon = float(sensors.get("lat", 0.0)), float(sensors.get("lon", 0.0))
        if self.keepin and not self.keepin.inside(lat, lon) and self.mode != "LAND":
            self.mode = "RTL"

        # Сенсоры
        baro_alt_m  = float(sensors.get("baro_alt_m", 0.0))
        airspeed_ms = float(sensors.get("airspeed",   0.0))

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
            out["pitch"]  = 0.0
            return out

        if self.mode == "CRUISE":
            out["thrust"] = self.alt_ctl.update(baro_alt_m, dt)
            out["pitch"]  = self.spd_ctl.update(airspeed_ms, dt)
            return out

        if self.mode == "RTL":
            out["thrust"] = self.alt_ctl.update(baro_alt_m, dt)
            out["pitch"]  = 0.15
            return out

        if self.mode == "LAND":
            # ступенчатое снижение
            self.alt_ctl.set_target(max(0.0, self.alt_ctl.target_alt_m - 0.6))
            out["thrust"] = max(0.2, self.alt_ctl.update(baro_alt_m, dt) - 0.1)
            out["pitch"]  = -0.05
            return out

        return out

# ───────────────────────── Проверка UAS-зон (вызов перед upload миссии) ─────────────────────────
def check_mission_zones(poly_coords_latlon, zone_files):
    """
    poly_coords_latlon: [(lat, lon), ...]
    zone_files: список путей к GeoJSON с зонами
    """
    try:
        from pathlib import Path
        from agents.compliance.utils import ensure_zone_compliance
        files = [str(Path(p)) for p in zone_files]
        ensure_zone_compliance(poly_coords_latlon, files)
    except Exception as e:
        # Специально пробрасываем, чтобы вызывающая сторона показала текст ошибки оператору
        raise