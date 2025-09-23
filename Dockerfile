FROM python:3.11-slim

WORKDIR /app

# 1) зависимости
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 2) код проекта
COPY engine/ ./engine/
COPY agents/ ./agents/

# 3) точка входа
# если у тебя основной запуск через модуль автопилота:
CMD ["python", "-m", "engine.agents.autopilot_ai"]

# если хочешь стартовать общий скрипт дрона, замени строку выше на:
# CMD ["python", "agents/Drone.py"]