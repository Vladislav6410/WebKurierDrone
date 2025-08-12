# engine/agents/autopilot_ai/presets/__init__.py
from pathlib import Path
import json

PRESETS_DIR = Path(__file__).parent

def load_preset(name: str) -> dict:
    """Загрузить один пресет по имени (без .json)."""
    p = PRESETS_DIR / f"{name}.json"
    if not p.exists():
        raise FileNotFoundError(f"Preset not found: {p}")
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)

def list_presets() -> list:
    """Список доступных пресетов (без mission_schema)."""
    return sorted([p.stem for p in PRESETS_DIR.glob("*.json") if p.stem != "mission_schema"])

def load_all_presets() -> dict:
    """Загрузить все пресеты в словарь {name: dict}."""
    return {name: load_preset(name) for name in list_presets()}

# Экспорт функций валидации
from .validator import (  # noqa: E402
    validate_dict,
    validate_file,
    validate_preset_by_name,
)

__all__ = [
    "PRESETS_DIR",
    "load_preset",
    "list_presets",
    "load_all_presets",
    "validate_dict",
    "validate_file",
    "validate_preset_by_name",
]