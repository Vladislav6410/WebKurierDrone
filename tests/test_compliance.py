from pathlib import Path
from shapely.geometry import Polygon
from agents.compliance.uas_zones_loader import load_zones
from agents.compliance.uas_zones_check import check_polygon_against_zones

def test_zone_intersection():
    zones = load_zones([Path("config/uas_zones/de_sample.geojson")])
    mission_poly = Polygon([(13.40,52.50),(13.41,52.50),(13.41,52.51),(13.40,52.51)])
    hits = check_polygon_against_zones(mission_poly, zones)
    assert isinstance(hits, list)