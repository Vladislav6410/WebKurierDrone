# Планировщик грид-миссии: bbox -> линии облёта с учётом перекрытий и DEM (опционально)
from dataclasses import dataclass
from typing import List, Tuple, Optional
import math

@dataclass
class GridParams:
    front_overlap: float = 0.75  # продольное перекрытие
    side_overlap: float = 0.65   # поперечное перекрытие
    gsd_cm: float = 2.5          # целевой GSD (см/пкс) - опционально
    altitude_m: float = 100.0    # высота полёта AGL
    speed_ms: float = 6.0
    heading_deg: float = 0.0     # азимут сетки

@dataclass
class Waypoint:
    lat: float
    lon: float
    rel_alt: float
    gimbal_pitch: float = -90.0
    take_photo: bool = True

def _rotate(x: float, y: float, deg: float) -> Tuple[float,float]:
    r = math.radians(deg)
    return (x*math.cos(r)-y*math.sin(r), x*math.sin(r)+y*math.cos(r))

def generate_grid(bbox: Tuple[float,float,float,float], p: GridParams) -> List[Waypoint]:
    """
    bbox: (lat_min, lon_min, lat_max, lon_max) — малая область (поля/участки).
    Упростим шаг как ~ расстояние между полосами по side_overlap.
    Примечание: для реала лучше проецировать в UTM. Здесь — упрощённая геометрия (градусы).
    """
    lat_min, lon_min, lat_max, lon_max = bbox
    # Прибл. конверсии: 1 deg lat ≈ 111_000 м; 1 deg lon ≈ 111_000 * cos(lat)
    lat0 = (lat_min+lat_max)/2
    m_per_deg_lat = 111_000.0
    m_per_deg_lon = 111_000.0*math.cos(math.radians(lat0))

    width_m  = (lon_max - lon_min)*m_per_deg_lon
    height_m = (lat_max - lat_min)*m_per_deg_lat

    # Шаг полосы по side_overlap (камерный FOV/px тут не считаем — берём эмпирику по alt)
    # Для простоты: шаг между линиями ~ 30 м при 100 м высоте и side_overlap=0.65
    base_swath = max(5.0, p.altitude_m * 0.6)  # очень грубая аппроксимация ширины полосы
    line_spacing = base_swath*(1.0 - p.side_overlap)

    n_lines = max(1, int(width_m/line_spacing)+1)
    step_lon = (line_spacing / m_per_deg_lon)

    waypoints: List[Waypoint] = []
    for i in range(n_lines):
        x_lon = lon_min + i*step_lon
        # Чередуем направление (змейка)
        strip = [
            Waypoint(lat=lat_min, lon=x_lon, rel_alt=p.altitude_m),
            Waypoint(lat=lat_max, lon=x_lon, rel_alt=p.altitude_m),
        ]
        if i % 2 == 1:
            strip.reverse()
        waypoints.extend(strip)

    # Поворот сетки по heading_deg — для простоты не вращаем географически,
    # а оставляем как есть (реально нужно едать в UTM, вращать, возвращать в WGS84).
    return waypoints