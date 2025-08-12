# engine/agents/autopilot_ai/presets/validate_all.py
from __future__ import annotations
import sys
import argparse
import json
import shutil
import difflib
from typing import List, Tuple

from . import (
    list_presets,
    validate_preset_by_name,
    PRESETS_DIR,
)

MAX_ALT = 120          # лимит высоты (должен совпадать со схемой)
NOTE_TAG = "≤120 м AGL"

def _validate(name: str) -> Tuple[bool, List[str]]:
    return validate_preset_by_name(name)

def _backup_file(path, backup_enabled: bool):
    """Создаёт .bak копию файла, если включен backup."""
    if backup_enabled:
        backup_path = str(path) + ".bak"
        shutil.copy2(path, backup_path)
        print(f"[BACKUP] {path.name} → {backup_path}")

def _clamp_altitudes_and_notes(mission: dict) -> Tuple[bool, List[str]]:
    """Ограничивает высоты и добавляет пометку в notes. Возвращает (изменено, лог)."""
    changed = False
    log: List[str] = []

    # altitude_m
    if isinstance(mission.get("altitude_m"), (int, float)) and mission["altitude_m"] > MAX_ALT:
        old = mission["altitude_m"]
        mission["altitude_m"] = MAX_ALT
        changed = True
        log.append(f"altitude_m: {old} → {MAX_ALT}")

    # transition.* высоты
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

    # notes пометка
    notes = (mission.get("notes") or "").strip()
    if NOTE_TAG not in notes:
        mission["notes"] = (notes.rstrip(".") + ". " if notes else "") + f"Соблюдать лимит высоты {NOTE_TAG}."
        changed = True
        log.append(f"notes: добавлена пометка '{NOTE_TAG}'")

    return changed, log

def _pretty_dump(data: dict) -> str:
    """Возвращает JSON-строку с отступами и без ASCII-эскейпа, завершая переводом строки."""
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"

def _fix_file(name: str, backup_enabled: bool) -> List[str]:
    """Читает пресет, фиксит высоты и notes, сохраняет при изменениях. Возвращает лог изменений."""
    path = PRESETS_DIR / f"{name}.json"
    old_text: str
    with path.open("r", encoding="utf-8") as f:
        old_text = f.read()
        mission = json.loads(old_text)

    changed, log = _clamp_altitudes_and_notes(mission)
    if changed:
        _backup_file(path, backup_enabled)
        new_text = _pretty_dump(mission)
        with path.open("w", encoding="utf-8") as f:
            f.write(new_text)

        # Показать diff, если включён backup
        if backup_enabled:
            diff = difflib.unified_diff(
                old_text.splitlines(keepends=True),
                new_text.splitlines(keepends=True),
                fromfile=f"{path.name}.bak (old)",
                tofile=f"{path.name} (new)",
                lineterm=""
            )
            print(f"[DIFF] {path.name}")
            for line in diff:
                print(line, end="")  # строки уже с переводами
            print()  # финальный перенос строки
    return log

def run(names: List[str], fix_alt: bool, backup_enabled: bool) -> Tuple[int, int]:
    total = 0
    failed_after = 0

    for name in names:
        total += 1

        if fix_alt:
            # 1) Проверка ДО фикса
            ok_before, errs_before = _validate(name)
            if ok_before:
                print(f"[OK  before] {name} ✅")
            else:
                print(f"[FAIL before] {name} ❌")
                for e in errs_before:
                    print("   -", e)

            # 2) Авто-чинка
            changes = _fix_file(name, backup_enabled)
            if changes:
                print(f"[FIX] {name}:")
                for c in changes:
                    print("   -", c)

            # 3) Проверка ПОСЛЕ фикса
            ok_after, errs_after = _validate(name)
            if ok_after:
                print(f"[OK  after ] {name} ✅")
            else:
                failed_after += 1
                print(f"[FAIL after] {name} ❌")
                for e in errs_after:
                    print("   -", e)

        else:
            # Обычная проверка без фикса
            ok, errs = _validate(name)
            if ok:
                print(f"[OK] {name} ✅")
            else:
                failed_after += 1
                print(f"[FAIL] {name} ❌")
                for e in errs:
                    print("   -", e)

    return total, failed_after

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate VTOL mission presets against mission_schema.json (авто-чинка, backup и diff)"
    )
    parser.add_argument(
        "--only",
        type=str,
        help="Проверить только перечисленные через запятую пресеты (без .json). Пример: mapping_area,delivery_drop",
    )
    parser.add_argument(
        "--fix-alt",
        action="store_true",
        help="Авто-чинка: ограничить высоты >120 м, править transition.* и добавить пометку в notes, затем повторно проверить",
    )
    parser.add_argument(
        "--backup",
        action="store_true",
        help="При авто-чинке делать резервную копию .bak и показывать unified diff изменений"
    )
    args = parser.parse_args()

    names = list_presets()
    if args.only:
        wanted = {n.strip() for n in args.only.split(",") if n.strip()}
        names = [n for n in names if n in wanted]

    if not names:
        print("Нет пресетов для проверки.")
        return 0

    total, failed_after = run(names, fix_alt=args.fix_alt, backup_enabled=args.backup)
    print(f"\nИтог (после фикса, если был): {total - failed_after}/{total} валидно.")
    return 1 if failed_after else 0

if __name__ == "__main__":
    sys.exit(main())