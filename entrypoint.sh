#!/bin/sh
set -e

# Ожидаем доступности БД
./wait-for-db.sh "$PG_HOST:$PG_PORT"

# Выполняем миграции
echo "📦 Applying migrations..."
python manage.py migrate

# Создаем суперпользователя, если его нет
echo "👤 Creating superuser (if needed)..."
python /app/create_admin.py

# Запускаем Django (используя Gunicorn или runserver)
echo "🚀 Starting Gunicorn..."
exec gunicorn itg.wsgi:application --bind 0.0.0.0:8000
# или просто:
# exec python manage.py runserver 0.0.0.0:8000
