# engine/agents/autopilot_ai/autopilot.py
"""
AutopilotAdvisor — справочник по возможностям, библиотекам и миссиям
для VTOL-класса FIXAR 007 NG и эквивалентных платформ.
⚠️ FIXAR Autopilot 2.0 и xGroundControl — закрытые (proprietary).
Этот модуль НЕ управляет FIXAR напрямую, а даёт рекомендации, чек‑листы и профили миссий.
"""

from dataclasses import dataclass, field
from typing import List, Dict

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
    spec: AirframeSpec = field(default_factory=AirframeSpec)

    def recommended_libs(self) -> Dict[str, List[str]]:
        """Открытые библиотеки/стек для реализации аналогичных функций в WebKurierDrone."""
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
        """Ключевые регуляторные требования EU (EASA) для BVLOS/Specific."""
        return {
            "category": "Specific (по умолчанию для BVLOS/VTOL коммерческих миссий)",
            "method": "SORA 10 steps + Operational Authorisation",
            "remote_id": "Обязателен с 01.01.2024 (DRI/Remote ID)",
            "adsb_remote_id_note": "ADSB/Remote ID опционально/по сценарию; следуйте NAA/UTM",
        }

    def capabilities(self) -> Dict[str, List[str]]:
        """Возможности автопилота/платформы применимо к классу FIXAR."""
        return {
            "autonomy": [
                "Автономный взлёт/посадка VTOL",
                "Автономный полёт по миссии (area/waypoints)",
                "Переход VTOL↔крейсер (fixed-wing)",
                "Полёт без компаса (устойчив к магнитным помехам)",
                "Работа при GPS‑помехах: IMU‑fallback; расширенный режим CV+AI",
                "Черный ящик/логирование (BlackBox аналог)"
            ],
            "safety": [
                "Terrain following: LiDAR‑базир. коррекция AGL на малых высотах",
                "Failsafe: RTH/hold/land по триггерам",
                "Ограничение по ветру/скорости/углам атаки"
            ],
            "manual_supervision": [
                "Ручное вмешательство через GCS",
                "Быстрая развёртка (≈5 мин) для выезда"
            ]
        }

    def aerobatics_policy(self) -> Dict[str, List[str]]:
        """Политика по фигурам высшего пилотажа для рабочего VTOL."""
        return {
            "not_allowed": [
                "Петля (loop), бочка (roll), штопор, иммельман, перевёрнутый полёт"
            ],
            "allowed_training_patterns": [
                "Широкие развороты, восьмёрка на высоте, орбита (loiter)",
                "Плавные набор/снижение, S‑кривые для калибровки"
            ],
            "reason": [
                "Рабочая платформа VTOL для картографии/инспекций, не аэрошоу",
                "Риск перегрузок и срыва потока на крыле с полезной нагрузкой"
            ]
        }

    def mission_presets(self) -> Dict[str, Dict]:
        """Готовые пресеты миссий под задачи геодезии/инспекций/доставки."""
        return {
            "mapping_area": {
                "pattern": "lawnmower", "overlap": {"front": 75, "side": 65},
                "gsd_control": True, "terrain_follow": True, "cruise_ms": min(18.0, self.spec.cruise_ms)
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
            "Параметры камеры/GS D заданы; payload ≤ 2 кг; MTOW ≤ 7 кг"
        ]

if __name__ == "__main__":
    advisor = AutopilotAdvisor()
    print("CAPABILITIES:", advisor.capabilities())
    print("LIBS:", advisor.recommended_libs())
    print("EU RULES:", advisor.flight_rules_eu())
    print("AEROBATICS:", advisor.aerobatics_policy())
    print("PRESETS:", advisor.mission_presets())
    print("PREFLIGHT:", advisor.preflight_checklist())