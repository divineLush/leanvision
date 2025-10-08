# Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Установка системных зависимостей для OpenCV (даже headless!)
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Копируем зависимости и устанавливаем Python-пакеты
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код
COPY . .

# Создаём директории (на случай, если их нет)
RUN mkdir -p uploads results_shift

# Экспонируем порт
EXPOSE 8000

# Запуск
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]