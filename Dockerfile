FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Установка необходимых системных библиотек (например, для selenium)
RUN apt-get update && apt-get install -y \
    curl \
    unzip \
    libglib2.0-0 \
    libx11-dev \
    libgdk-pixbuf2.0-0 \
    libatk1.0-0 \
    libpango-1.0-0 \
    libgdk-pixbuf2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Копируем файл зависимостей
COPY requirements.txt .

# Обновляем pip, setuptools и wheel
RUN pip install --upgrade pip setuptools wheel



# Устанавливаем Python-зависимости
RUN pip install --no-cache-dir -r requirements.txt


# Копируем проект
COPY . .

# Открываем порт
EXPOSE 8000

# Запускаем Django сервер
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
