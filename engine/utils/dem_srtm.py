# Лёгкая обёртка под высоты SRTM (offline-тайлы заранее положить в /data/srtm/)
# В реальном проекте лучше использовать rasterio/xarray. Здесь простой каркас.
import os
from typing import Optional

class DEM:
    def __init__(self, root="data/srtm"):
        self.root = root

    def altitude_agl(self, lat: float, lon: float, ref_home_alt_m: float) -> Optional[float]:
        # TODO: прочитать нужный тайл HGT/GeoTIFF, интерполировать, вернуть alt AGL
        # Заглушка — возвращаем ту же высоту: полёт на константной высоте
        return ref_home_alt_m