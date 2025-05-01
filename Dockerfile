FROM python:3.12-slim

# 1. Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    netcat-openbsd \
    gcc \
    libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# 2. Рабочая директория
WORKDIR /app

# 3. Сначала копируем ТОЛЬКО requirements.txt
COPY requirements.txt .

# 4. Установка зависимостей (явно указываем полный путь к pip)
RUN python -m pip install --upgrade pip && \
    python -m pip install -r requirements.txt


# После установки зависимостей
RUN python -m pip list && \
    python -c "import sys; print(sys.path)"

# 5. Копируем скрипты
COPY entrypoint.sh wait-for-db.sh ./
RUN chmod +x entrypoint.sh wait-for-db.sh

# 6. Переменные окружения
ENV DOCKERIZED=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# 7. Копируем весь проект
COPY . .

# 8. Проверяем установку Django перед collectstatic
RUN python -c "import django; print(django.__version__)" && \
    mkdir -p /static && \
    python manage.py collectstatic --no-input

# 9. Запуск

ENTRYPOINT ["./entrypoint.sh"]