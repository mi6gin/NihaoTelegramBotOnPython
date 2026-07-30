FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Установка системных утилит (build-essential и ffmpeg для TikTok-аудио)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

# Папки для СУБД и логов
RUN mkdir -p data logs

# Запуск миграций и основного процесса бота
CMD ["/bin/sh", "-c", "alembic upgrade head && python bot.py"]
