from shapely.geometry import shape, Polygon, mapping
from typing import List, Tuple, Dict, Any

class ZoneHit(Exception):
    def __init__(self, zone_name: str, reason: str):
        super().__init__(f"Mission intersects restricted zone: {zone_name} ({reason})")
        self.zone_name = zone_name
        self.reason = reason

def check_polygon_against_zones(mission_poly: Polygon, zones_fc: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Возвращает список пересекающихся зон."""
    hits = []
    for feat in zones_fc:
        geom = feat.get("geometry")
        props = feat.get("properties", {})
        if not geom: 
            continue
        try:
            z = shape(geom)
            if mission_poly.intersects(z):
                hits.append({"zone": props.get("name") or props.get("id") or "unknown", "props": props})
        except Exception:
            continue
    return hits