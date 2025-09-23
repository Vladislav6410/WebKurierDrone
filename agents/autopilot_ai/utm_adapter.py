# EU U-space / ASTM F3411 адаптер (заглушка интерфейса + точки интеграции)
# Реальная интеграция делается через провайдера U-space (Network/Direct Remote ID).
# Здесь оставлены "hook-и" под HTTP/API провайдера + локальные NOTAM зоны.
from dataclasses import dataclass
from typing import List, Optional, Tuple

@dataclass
class AirspaceAlert:
    kind: str         # e.g. "NOTAM", "GEOZONE", "WEATHER"
    message: str
    polygon: Optional[List[Tuple[float,float]]] = None

class USpaceAdapter:
    def __init__(self):
        # TODO: внедрить провайдера (EU: U-space USSP). Добавить ключи в config/settings.yaml
        self.enabled = True

    def check_airspace(self, lat: float, lon: float, alt_m: float = 120.0) -> List[AirspaceAlert]:
        """Быстрая пред-проверка: тут должны быть запросы:
        - U-space (GeoZones, в т.ч. UAS.Restricted/Prohibited)
        - Локальные NOTAM (через провайдера)
        - Погода/ветер (опц.)
        Сейчас возвращаем заглушку — всегда ОК.
        """
        if not self.enabled:
            return []
        return []  # пусто = нет блокирующих алертов

    def ensure_remote_id(self) -> bool:
        """Проверка готовности Remote ID (F3411). В бою: проверяем модуль/сертификат/регистрацию."""
        return True