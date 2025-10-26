# -*- coding: utf-8 -*-
from shapely.geometry import shape, Polygon, mapping
from typing import List, Tuple, Dict, Any, Optional


class ZoneHit(Exception):
    def __init__(self, zone_name: str, reason: str):
        super().__init__(f"Mission intersects restricted zone: {zone_name} ({reason})")
        self.zone_name = zone_name
        self.reason = reason


def _zone_name(props: Dict[str, Any]) -> str:
    return props.get("zone") or props.get("name") or props.get("id") or "unknown"


def _is_permissive(props: Dict[str, Any]) -> bool:
    """
    Зоны, которые НЕ должны блокировать миссию.
    """
    if props.get("allow_flight") is True:
        return True
    cat = str(props.get("category", "")).lower()
    restr = str(props.get("restriction", "")).lower()
    # training/allowed/green считаем разрешающими
    if cat in {"training", "allowed", "green"}:
        return True
    if "training" in restr or "practice" in restr:
        return True
    return False


def check_polygon_against_zones(
    mission_poly: Polygon,
    zones_fc: List[Dict[str, Any]],
    *,
    flight_alt_m: Optional[float] = None,
    raise_on_first: bool = False,
) -> List[Dict[str, Any]]:
    """
    Возвращает список пересечений с ОГРАНИЧИВАЮЩИМИ зонами.
    Разрешающие зоны (training/allow_flight) пропускаются.
    Если указан flight_alt_m, учитывает max_altitude_m зоны.

    Args:
        mission_poly: полигон миссии (в lon/lat, как Shapely Polygon)
        zones_fc: список GeoJSON-фич (features)
        flight_alt_m: рабочая высота полёта над уровнем моря (ASL) или AGL — см. вашу модель
        raise_on_first: при первом нарушении бросить ZoneHit

    Returns:
        hits: список словарей { "zone": <name>, "reason": <text>, "props": <properties> }
    """
    hits: List[Dict[str, Any]] = []

    for feat in zones_fc:
        geom = feat.get("geometry")
        props = feat.get("properties", {}) or {}
        if not geom:
            continue

        try:
            zone_geom = shape(geom)
        except Exception:
            continue

        if not mission_poly.intersects(zone_geom):
            continue

        # пропускаем разрешающие зоны
        if _is_permissive(props):
            continue

        # причина и имя
        name = _zone_name(props)
        reason = str(props.get("restriction") or "restricted zone")

        # проверка высоты, если указана
        z_max = props.get("max_altitude_m")
        if isinstance(z_max, (int, float)) and flight_alt_m is not None:
            if float(flight_alt_m) <= float(z_max):
                # пересечение есть, но по высоте не нарушаем ограничение — предупреждение не создаём
                continue
            else:
                reason = f"{reason}; max_altitude={z_max}m, flight_alt={flight_alt_m}m"

        hit = {"zone": name, "reason": reason, "props": props}
        hits.append(hit)

        if raise_on_first:
            raise ZoneHit(name, reason)

    return hits