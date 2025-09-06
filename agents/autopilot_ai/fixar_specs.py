# -*- coding: utf-8 -*-
"""
FIXAR & Benchmarks — dict-модель спецификаций для WebKurierDrone.

Подключение:
    from engine.agents.autopilot_ai.fixar_specs import SPECS, print_table, to_csv

Назначение:
    - Хранит эталонные параметры FIXAR и конкурентов (VTOL/industrial)
    - Удобен для сравнения, экспорта в CSV, интеграции в UI/бота/агентов
"""

from typing import Dict, Any, List, Optional
import csv

# Единый список полей (держим порядок колонок)
FIELDS: List[str] = [
    "name",
    "class",               # vtol / multirotor / fixed-wing vtol
    "payload_kg",
    "range_km",
    "endurance_min",
    "cruise_speed_kmh",
    "max_speed_kmh",
    "ceiling_m",
    "setup_time_min",
    "link_range_km",
    "autopilot",
    "gcs",                 # ground control software
    "features",
    "ai_cv"                # on-board AI/CV capability
]

# Справочник спецификаций (значения можно расширять/уточнять по мере появления данных)
SPECS: Dict[str, Dict[str, Any]] = {
    "FIXAR 007 NG": {
        "name": "FIXAR 007 NG",
        "class": "fixed-wing vtol",
        "payload_kg": 2.0,
        "range_km": 60.0,
        "endurance_min": 60,                 # 59–60
        "cruise_speed_kmh": 72,
        "max_speed_kmh": 120,
        "ceiling_m": 6000,
        "setup_time_min": 2,
        "link_range_km": 30,
        "autopilot": "FIXAR in-house (FAR rotors)",
        "gcs": "xGroundControl",
        "features": "BVLOS-ready, FAR fixed-angle rotors, modular payload",
        "ai_cv": "planned/limited (edge-ready)"
    },
    "FIXAR 025": {
        "name": "FIXAR 025",
        "class": "fixed-wing vtol",
        "payload_kg": 10.0,
        "range_km": 300.0,
        "endurance_min": 360,                # «до 6 часов»
        "cruise_speed_kmh": 95,              # 90–100
        "max_speed_kmh": 120,
        "ceiling_m": 6000,
        "setup_time_min": 5,
        "link_range_km": 150,
        "autopilot": "FIXAR next-gen (in-house, FAR)",
        "gcs": "xGroundControl (+ BVLOS toolset)",
        "features": "heavy payload, BVLOS, blackbox, UTM API",
        "ai_cv": "Jetson/Qualcomm capable (CV/ML)"
    },
    "WingtraOne GEN II": {
        "name": "WingtraOne GEN II",
        "class": "fixed-wing vtol",
        "payload_kg": 0.8,
        "range_km": 59.0,
        "endurance_min": 59,
        "cruise_speed_kmh": 57,
        "max_speed_kmh": 72,
        "ceiling_m": 5000,
        "setup_time_min": 6,
        "link_range_km": 10,
        "autopilot": "PX4-based (proprietary stack on top)",
        "gcs": "WingtraHub",
        "features": "survey-grade photogrammetry, PPK/RTK options",
        "ai_cv": "limited (focus on mapping workflow)"
    },
    "Trinity F90+": {
        "name": "Trinity F90+",
        "class": "fixed-wing vtol",
        "payload_kg": 0.7,
        "range_km": 100.0,
        "endurance_min": 90,
        "cruise_speed_kmh": 65,              # 60–70
        "max_speed_kmh": 100,
        "ceiling_m": 5000,
        "setup_time_min": 8,
        "link_range_km": 15,
        "autopilot": "PX4 (QBase stack)",
        "gcs": "QBase 3D",
        "features": "balanced endurance/range, modular payloads",
        "ai_cv": "limited (data processing offboard)"
    },
    "DJI M300 RTK": {
        "name": "DJI M300 RTK",
        "class": "multirotor",
        "payload_kg": 2.7,
        "range_km": 15.0,
        "endurance_min": 55,
        "cruise_speed_kmh": 82,
        "max_speed_kmh": 82,
        "ceiling_m": 7000,
        "setup_time_min": 12,
        "link_range_km": 15,
        "autopilot": "DJI proprietary",
        "gcs": "DJI Pilot 2",
        "features": "RTK, LiDAR ecosystem, enterprise safety",
        "ai_cv": "onboard assistance/object detection"
    },
}

def get(item: str) -> Optional[Dict[str, Any]]:
    """Вернуть спецификацию по имени модели."""
    return SPECS.get(item)

def all_models() -> List[str]:
    """Список всех моделей в словаре."""
    return list(SPECS.keys())

def to_rows(models: Optional[List[str]] = None) -> List[List[Any]]:
    """
    Преобразовать в строки для табличного вывода/экспорта.
    """
    models = models or all_models()
    rows: List[List[Any]] = []
    for m in models:
        spec = SPECS[m]
        row = [spec.get(k, "") for k in FIELDS]
        rows.append(row)
    return rows

def to_csv(path: str, models: Optional[List[str]] = None) -> None:
    """
    Экспортировать выбранные модели в CSV (UTF-8, ; как разделитель — удобно для EU-LOCALE).
    """
    models = models or all_models()
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(FIELDS)
        for row in to_rows(models):
            writer.writerow(row)

def print_table(models: Optional[List[str]] = None) -> None:
    """
    Печать компактной таблицы в консоль (моноширинная разметка).
    """
    models = models or all_models()
    rows = [FIELDS] + to_rows(models)

    # вычислим ширины колонок
    widths = [0] * len(FIELDS)
    for r in rows:
        for i, cell in enumerate(r):
            widths[i] = max(widths[i], len(str(cell)))

    def fmt(row: List[Any]) -> str:
        return " | ".join(str(c).ljust(widths[i]) for i, c in enumerate(row))

    sep = "-+-".join("-" * w for w in widths)
    print(fmt(rows[0]))
    print(sep)
    for r in rows[1:]:
        print(fmt(r))

def best_by(metric: str, prefer_max: bool = True) -> Optional[Dict[str, Any]]:
    """
    Найти лучшую модель по метрике (например: 'range_km', 'payload_kg', 'endurance_min').
    prefer_max=True — максимальное значение лучше, иначе минимальное.
    """
    if metric not in FIELDS:
        raise ValueError(f"Unknown metric: {metric}. Allowed: {', '.join(FIELDS)}")
    candidates = [SPECS[m] for m in SPECS if isinstance(SPECS[m].get(metric), (int, float))]
    if not candidates:
        return None
    key_fn = (lambda s: s.get(metric, float("-inf"))) if prefer_max else (lambda s: s.get(metric, float("inf")))
    return max(candidates, key=key_fn) if prefer_max else min(candidates, key=key_fn)

# Демонстрация при самостоятельном запуске:
if __name__ == "__main__":
    print_table()
    print("\nBest by range_km:", best_by("range_km", prefer_max=True)["name"])
    print("Best by payload_kg:", best_by("payload_kg", prefer_max=True)["name"])
    # Пример экспорта:
    # to_csv("fixar_benchmarks.csv")