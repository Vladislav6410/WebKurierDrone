# engine/agents/autopilot_ai/presets/validate_all.py
from __future__ import annotations
import sys
import argparse
import json
from typing import List, Tuple

from . import (
    list_presets,
    validate_preset_by_name,
    PRESETS_DIR,
)

MAX_ALT = 120  # Жёсткий лимит ≤120 м, должен совпадать со схемой
NOTE_TAG = "≤120 м AGL"

def clamp_altitudes_and_notes(mission: dict) -> Tuple[bool, List[str]]:
    """Ограничивает высоты и добавляет пометку в notes. Возвращает (изменено, лог)."""
    changed = False
    log: List[str] = []

    # Основная высота
    if isinstance(mission.get("altitude_m"), (int, float)) and mission["altitude_m"] > MAX_ALT:
        old = mission["altitude_m"]
        mission["altitude_m"] = MAX_ALT
        changed = True
        log.append(f"altitude_m: {old} → {MAX_ALT}")

    # Переходы VTOL↔крыло
    tr = mission.get("transition") or {}
    if isinstance(tr.get("vtol_to_wing_alt_m"), (int, float)) and tr["vtol_to_wing_alt_m"] > MAX_ALT:
        old = tr["vtol_to_wing_alt_m"]
        tr["vtol_to_wing_alt_m"] = MAX_ALT
        changed = True
        log.append(f"transition.vtol_to_wing_alt_m: {old} → {MAX_ALT}")
    if isinstance(tr.get("wing_to_vtol_alt_m"), (int, float)) and tr["wing_to_vtol_alt_m"] > MAX_ALT:
        old = tr["wing_to_vtol_alt_m"]
        tr["wing_to_vtol_alt_m"] = MAX_ALT
        changed = True
        log.append(f"transition.wing_to_vtol_alt_m: {old} → {MAX_ALT}")
    if changed:
        mission["transition"] = tr

    # Пометка в notes
    notes = mission.get("notes", "").strip()
    if NOTE_TAG not in notes:
        if notes:
            mission["notes"] = f"{notes.rstrip('.')} Соблюдать лимит высоты {NOTE_TAG}."
        else:
            mission["notes"] = f"Соблюдать лимит высоты {NOTE_TAG}."
        changed = True
        log.append(f"notes: добавлена пометка '{NOTE_TAG}'")

    return changed, log

def fix_file(name: str) -> List[str]:
    """Читает пресет, фиксит высоты и notes, сохраняет при изменениях."""
    path = PRESETS_DIR / f"{name}.json"
    with path.open("r", encoding="utf-8") as f:
        mission = json.load(f)

    changed, log = clamp_altitudes_and_notes(mission)
    if changed:
        with path.open("w", encoding="utf-8") as f:
            json.dump(mission, f, ensure_ascii=False, indent=2)
            f.write("\n")
    return log

def run(names: List[str], fix_alt: bool) -> Tuple[int, int]:
    total = 0
    failed = 0
    for name in names:
        total += 1
        if fix_alt:
            changes = fix_file(name)
            if changes:
                print(f"[FIX] {name}:")
                for c in changes:
                    print("   -", c)

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
        description="Validate VTOL mission presets against mission_schema.json (с авто-чинкой высоты и notes)"
    )
    parser.add_argument(
        "--only",
        type=str,
        help="Проверить только перечисленные через запятую пресеты (без .json). Пример: mapping_area,delivery_drop",
    )
    parser.add_argument(
        "--fix-alt",
        action="store_true",
        help="Автоматически ограничивать высоты >120 м, править transition.* и добавлять пометку в notes",
    )
    args = parser.parse_args()

    names = list_presets()
    if args.only:
        wanted = {n.strip() for n in args.only.split(",") if n.strip()}
        names = [n for n in names if n in wanted]

    if not names:
        print("Нет пресетов для проверки.")
        return 0

    total, failed = run(names, fix_alt=args.fix_alt)
    print(f"\nИтог: {total - failed}/{total} валидно.")
    return 1 if failed else 0

if __name__ == "__main__":
    sys.exit(main())