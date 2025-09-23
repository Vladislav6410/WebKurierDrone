# Базовый образ Python
FROM python:3.11-slim

# Рабочая директория внутри контейнера
WORKDIR /app

# Копируем код проекта
COPY engine/ ./engine/

# Устанавливаем зависимости
RUN pip install --no-cache-dir \
    mavsdk \
    pillow

# Точка входа (запускаем твой автопилот-агент)
CMD ["python", "-m", "engine.agents.autopilot_ai"]