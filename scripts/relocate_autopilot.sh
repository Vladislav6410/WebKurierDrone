#!/bin/bash
set -euo pipefail
mkdir -p engine/agents/autopilot_ai
git mv agents/autopilot_ai/* engine/agents/autopilot_ai/ 2>/dev/null || true
rm -f agents/autopilot_ai/init.py 2>/dev/null || true
[ -d agents/autopilot_ai ] && rmdir agents/autopilot_ai 2>/dev/null || true

touch engine/agents/__init__.py
echo '# autopilot_ai package' > engine/agents/autopilot_ai/__init__.py

if [ -f LICENSE ] && [ -f LICENSE.md ]; then
  git rm -f LICENSE
fi
[ -f "Add custom license for WebKurierDrone © Vladislav6410" ] && \
  git mv "Add custom license for WebKurierDrone © Vladislav6410" docs/CUSTOM_LICENSE.txt || true

git add -A
git commit -m "refactor: move autopilot_ai into engine/, fix packages and licenses"
git push origin main
echo "✅ Перенос завершён."