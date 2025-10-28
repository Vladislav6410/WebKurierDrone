from pathlib import Path
import json
from typing import List, Dict, Any

def load_zones(paths: List[Path]) -> List[Dict[str, Any]]:
    """Load UAS geo-zones from a list of GeoJSON files."""
    zones: List[Dict[str, Any]] = []
    for p in paths:
        if not p.exists():
            continue
        with p.open("r", encoding="utf-8") as f:
            gj = json.load(f)
            zones.extend(gj.get("features", []))
    return zones