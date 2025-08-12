# engine/agents/autopilot_ai/presets/__init__.py
from pathlib import Path
import json

PRESETS_DIR = Path(__file__).parent

def load_preset(name: str) -> dict:
    p = PRESETS_DIR / f"{name}.json"
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)

def list_presets() -> list:
    return [p.stem for p in PRESETS_DIR.glob("*.json") if p.stem != "mission_schema"]