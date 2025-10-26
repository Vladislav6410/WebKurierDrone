from pathlib import Path
import json
from typing import List, Dict, Any

def load_zones(paths: List[Path]) -> List[Dict[str, Any]]:
    """Загружает UAS геозоны из списка GeoJSON файлов."""
    zones = []
    for p in paths:
        with p.open("r", encoding="utf-8") as f:
            gj = json.load(f)
            # ожидаем FeatureCollection
            feats = gj.get("features", [])
            zones.extend(feats)
    return zones