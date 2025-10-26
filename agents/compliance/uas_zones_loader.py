# -*- coding: utf-8 -*-
from pathlib import Path
import json
from typing import List, Dict, Any


def load_zones(paths: List[Path]) -> List[Dict[str, Any]]:
    """
    Загружает UAS геозоны из списка GeoJSON-файлов или директорий.

    Args:
        paths: список путей (файлы или каталоги)

    Returns:
        zones: список GeoJSON features (dict)
    """
    zones: List[Dict[str, Any]] = []

    for p in paths:
        try:
            if not p.exists():
                print(f"[WARN] File not found: {p}")
                continue

            # если указан каталог — рекурсивно ищем все GeoJSON
            if p.is_dir():
                files = list(p.rglob("*.geojson")) + list(p.rglob("*.json"))
                if not files:
                    print(f"[INFO] No GeoJSON files in directory: {p}")
                for fp in files:
                    zones.extend(_load_geojson_file(fp))
            else:
                zones.extend(_load_geojson_file(p))

        except Exception as e:
            print(f"[ERROR] Failed to load zones from {p}: {e}")

    print(f"[INFO] Loaded {len(zones)} UAS zone features from {len(paths)} source(s)")
    return zones


def _load_geojson_file(path: Path) -> List[Dict[str, Any]]:
    """Загружает и проверяет один GeoJSON файл."""
    try:
        with path.open("r", encoding="utf-8") as f:
            gj = json.load(f)
    except json.JSONDecodeError as e:
        print(f"[ERROR] Invalid JSON in {path}: {e}")
        return []
    except Exception as e:
        print(f"[ERROR] Failed to open {path}: {e}")
        return []

    if not isinstance(gj, dict):
        print(f"[WARN] Unexpected JSON structure in {path}")
        return []

    feats = gj.get("features")
    if not feats or not isinstance(feats, list):
        print(f"[WARN] No 'features' in {path}")
        return []

    # фильтруем только корректные объекты
    valid_feats = []
    for feat in feats:
        if not isinstance(feat, dict):
            continue
        geom = feat.get("geometry")
        if not geom or not isinstance(geom, dict):
            continue
        valid_feats.append(feat)

    print(f"[OK] {path.name}: {len(valid_feats)} feature(s) loaded")
    return valid_feats