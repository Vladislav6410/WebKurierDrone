# Bootstrap для импорта из корневой папки agents/
import os, sys
ROOT = os.path.dirname(os.path.abspath(__file__))          # .../engine
PROJECT_ROOT = os.path.dirname(ROOT)                        # корень репо
AGENTS_DIR = os.path.join(PROJECT_ROOT, "agents")

if os.path.isdir(AGENTS_DIR) and AGENTS_DIR not in sys.path:
    sys.path.insert(0, AGENTS_DIR)