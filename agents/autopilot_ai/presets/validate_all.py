# engine/agents/autopilot_ai/presets/validate_all.py
from __future__ import annotations
import sys
import argparse
from typing import List, Tuple

from . import list_presets, validate_preset_by_name

def run(names: List[str]) -> Tuple[int, int]:
    total = 0
    failed = 0
    for name in names:
        total += 1
        ok, errs = validate_preset_by_name(name)
        if ok:
            print(f"[OK] {name} ✅")
        else:
            failed += 1
            print(f"[FAIL] {name} ❌")
            for e in errs:
                print("   -", e)
    return total, failed

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate all VTOL mission presets against mission_schema.json"
    )
    parser.add_argument(
        "--only",
        type=str,
        help="Проверить только перечисленные через запятую пресеты (без .json). Пример: mapping_area,delivery_drop",
    )
    args = parser.parse_args()

    names = list_presets()
    if args.only:
        wanted = {n.strip() for n in args.only.split(",") if n.strip()}
        names = [n for n in names if n in wanted]

    if not names:
        print("Нет пресетов для проверки.")
        return 0

    total, failed = run(names)
    print(f"\nИтог: {total - failed}/{total} валидно.")
    return 1 if failed else 0

if __name__ == "__main__":
    sys.exit(main())