#!/bin/bash
# Автоматические коммиты с проверками для autopilot_ai

set -euo pipefail

REQ_FILES=(
  "engine/agents/autopilot_ai/utm_adapter.py"
  "engine/agents/autopilot_ai/mission_grid.py"
  "engine/agents/autopilot_ai/mavsdk_mission.py"
  "engine/agents/autopilot_ai/hyperspectral_ndvi.py"
  "engine/utils/dem_srtm.py"
  "config/settings.yaml"
  "requirements.txt"
  "README.md"
)

echo "▶ Проверка: git-репозиторий"
git rev-parse --is-inside-work-tree >/dev/null

echo "▶ Проверка наличия нужных файлов"
missing=0
for f in "${REQ_FILES[@]}"; do
  if [ ! -f "$f" ]; then
    echo "  ✗ нет файла: $f"
    missing=1
  else
    echo "  ✓ $f"
  fi
done
if [ $missing -ne 0 ]; then
  echo "⛔ Создай отсутствующие файлы и запусти скрипт снова."
  exit 1
fi

echo "▶ Проверка чистоты индекса"
git status --porcelain

read -r -p "Продолжить коммиты? [y/N] " ans
[[ "${ans:-N}" == "y" || "${ans:-N}" == "Y" ]] || { echo "Отменено."; exit 0; }

echo "=== 1/3: feat(autopilot_ai) ==="
git add engine/agents/autopilot_ai/utm_adapter.py \
        engine/agents/autopilot_ai/mission_grid.py \
        engine/agents/autopilot_ai/mavsdk_mission.py \
        engine/agents/autopilot_ai/hyperspectral_ndvi.py \
        engine/utils/dem_srtm.py
git commit -m "feat(autopilot_ai): add U-space adapter, grid planner, MAVSDK mission launcher, NDVI" || true

echo "=== 2/3: chore(config) ==="
git add requirements.txt config/settings.yaml
git commit -m "chore(config): add deps (mavsdk, spectral, Pillow)" || true

echo "=== 3/3: docs ==="
git add README.md
git commit -m "docs: note U-space/Remote ID and EU flow in README" || true

# Опционально: чистка дублей лицензий
if [ -f LICENSE ] && [ -f LICENSE.md ]; then
  echo "⚠ Найдены LICENSE и LICENSE.md. Рекомендую оставить LICENSE.md."
  read -r -p "Удалить LICENSE (y/N)? " drop
  if [[ "${drop:-N}" =~ ^[yY]$ ]]; then
    git rm -f LICENSE
    git commit -m "chore(license): remove duplicate LICENSE, keep LICENSE.md"
  fi
fi

echo "=== Push ==="
git push origin main
echo "✅ Готово."