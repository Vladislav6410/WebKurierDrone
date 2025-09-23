# Базовый образ Python
FROM python:3.11-slim

# Устанавливаем системные зависимости (для numpy, scipy, Pillow и др.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Рабочая директория внутри контейнера
WORKDIR /app

# Устанавливаем зависимости проекта
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код проекта
COPY engine/ ./engine/
COPY agents/ ./agents/

# Переменные окружения (пример)
ENV PYTHONUNBUFFERED=1
ENV MAVSDK_SERVER_HOST=0.0.0.0
ENV MAVSDK_SERVER_PORT=50051

# Точка входа (автопилот-агент)
CMD ["python", "-m", "engine.agents.autopilot_ai"]