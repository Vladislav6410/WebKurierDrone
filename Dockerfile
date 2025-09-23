# Базовый образ Python
FROM python:3.11-slim

# Рабочая директория внутри контейнера
WORKDIR /app

# Устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код проекта
COPY engine/ ./engine/

# Точка входа (автопилот-агент)
CMD ["python", "-m", "engine.agents.autopilot_ai"]