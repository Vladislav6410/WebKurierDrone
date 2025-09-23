FROM python:3.11-slim

WORKDIR /app

# Устанавливаем Flask для веб-интерфейса
RUN pip install flask

# Копируем UI файлы
COPY . /app/ui

EXPOSE 5000

CMD ["python", "-m", "http.server", "5000", "--directory", "ui"]