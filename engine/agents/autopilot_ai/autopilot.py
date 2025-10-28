# NEW: compliance check
from pathlib import Path
from shapely.geometry import Polygon
from agents.compliance.uas_zones_loader import load_zones
from agents.compliance.uas_zones_check import check_polygon_against_zones

def ensure_zone_compliance(poly_coords_latlon, zone_files):
    """
    Check mission polygon vs UAS geo-zones.
    poly_coords_latlon: [(lat, lon), ...]
    zone_files: [Path|str, ...] – GeoJSON list
    """
    mission_poly = Polygon([(lon, lat) for (lat, lon) in poly_coords_latlon])
    files = [Path(p) for p in zone_files]
    zones = load_zones(files)
    hits = check_polygon_against_zones(mission_poly, zones)
    if hits:
        names = ", ".join(h.get("zone", "unknown") for h in hits)
        raise RuntimeError(
            f"Маршрут пересекает запретные/ограниченные зоны: {names}. "
            f"Скорректируйте полигон или получите разрешение."
        )