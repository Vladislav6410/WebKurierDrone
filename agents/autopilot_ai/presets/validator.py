# engine/agents/autopilot_ai/presets/validator.py
from __future__ import annotations
from pathlib import Path
from typing import Tuple, List, Optional
import json

from jsonschema import Draft202012Validator, exceptions as js_exc

PRESETS_DIR = Path(__file__).parent
SCHEMA_PATH = PRESETS_DIR / "mission_schema.json"

def load_schema() -> dict:
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema not found: {SCHEMA_PATH}")
    with SCHEMA_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)

def validate_dict(data: dict) -> Tuple[bool, List[str]]:
    """Проверка словаря миссии по JSON‑схеме. Возвращает (ok, errors)."""
    schema = load_schema()
    validator = Draft202012Validator(schema)
    errors = [f"{e.message} @ {'/'.join(map(str, e.path))}" for e in validator.iter_errors(data)]
    return (len(errors) == 0, errors)

def validate_file(path: Path | str) -> Tuple[bool, List[str]]:
    """Проверка JSON‑файла миссии по JSON‑схеме. Возвращает (ok, errors)."""
    p = Path(path)
    if not p.exists():
        return False, [f"File not found: {p}"]
    with p.open("r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            return False, [f"JSON parse error: {e}"]
    return validate_dict(data)

def validate_preset_by_name(name: str) -> Tuple[bool, List[str]]:
    """Проверка пресета по имени (без .json), лежащего в presets/."""
    p = PRESETS_DIR / f"{name}.json"
    return validate_file(p)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Validate VTOL mission JSON against mission_schema.json")
    g = parser.add_mutually_exclusive_group(required=True)
    g.add_argument("--file", type=str, help="Путь к JSON‑файлу миссии")
    g.add_argument("--preset", type=str, help="Имя пресета из presets/ без .json")
    args = parser.parse_args()

    if args.file:
        ok, errs = validate_file(args.file)
    else:
        ok, errs = validate_preset_by_name(args.preset)

    if ok:
        print("OK: mission JSON is valid ✅")
    else:
        print("❌ Validation failed:")
        for e in errs:
            print(" -", e)
        exit(1)