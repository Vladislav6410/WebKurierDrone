#!/bin/bash
# Скрипт для автоматических коммитов модуля autopilot_ai

set -e

echo "=== 1/3: feat(autopilot_ai) ==="
git add engine/agents/autopilot_ai/utm_adapter.py \
        engine/agents/autopilot_ai/mission_grid.py \
        engine/agents/autopilot_ai/mavsdk_mission.py \
        engine/agents/autopilot_ai/hyperspectral_ndvi.py \
        engine/utils/dem_srtm.py
git commit -m "feat(autopilot_ai): add U-space adapter, grid planner, MAVSDK mission launcher, NDVI"

echo "=== 2/3: chore(config) ==="
git add requirements.txt config/settings.yaml
git commit -m "chore(config): add deps (mavsdk, spectral, Pillow)"

echo "=== 3/3: docs ==="
git add README.md
git commit -m "docs: note U-space/Remote ID and EU flow in README"

echo "=== Push to origin/main ==="
git push origin main

echo "✅ Все три коммита сделаны и отправлены."