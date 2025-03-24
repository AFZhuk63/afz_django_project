
# 🚀 Django Проект с Авторизацией, Подтверждением Email, Celery, Docker, SSL и Бэкапами

## 📋 Содержание:
1. Установка и запуск
2. Регистрация, подтверждение email, восстановление пароля
3. Docker-инфраструктура
4. Flower мониторинг
5. Let's Encrypt SSL
6. PostgreSQL бэкапы

---

## 1️⃣ Установка и Запуск

### Клонировать проект:

```bash
git clone https://github.com/vetrof/Django-In-Docker.git
cd Django-In-Docker
```

### Создать `.env` файл:

```env
SERVER_NAME=localhost
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=http://localhost,http://127.0.0.1
POSTGRES_DB=postgres_database
POSTGRES_USER=postgres_user
POSTGRES_PASSWORD=password
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
CELERY_BROKER_URL=redis://redis:6379/0
```

---

## 2️⃣ Авторизация / Регистрация с Подтверждением Email

- Регистрация пользователя: `/users/signup/`
- Email подтверждение с токеном.
- После подтверждения активируется аккаунт.
- Сброс пароля: `/users/password_reset/`

### Формы:
- Используется `UserCreationForm`.
- Подключён `Django Messages Framework`.

---

## 3️⃣ Docker Сервисы

| Сервис          | Назначение                             | Порт      |
|-----------------|----------------------------------------|-----------|
| Django + Gunicorn | Backend-сервер                      | 8000      |
| Nginx           | Обработка HTTP/HTTPS и статики         | 80 / 443  |
| PostgreSQL      | База данных                           | 5432      |
| Redis           | Брокер задач для Celery               | 6379      |
| Celery Worker   | Выполнение фоновых задач              | —         |
| Celery Beat     | Периодические задачи                  | —         |
| Flower          | Мониторинг задач Celery               | 5555      |
| Certbot         | SSL-сертификаты Let's Encrypt         | —         |
| PostgreSQL Backup | Автобэкапы БД в ./postgres_backups  | —         |

---

## 4️⃣ Flower Мониторинг

- URL: `http://localhost:5555`
- Отображение очередей, задач, времени выполнения.

---

## 5️⃣ SSL Let's Encrypt

### Получение сертификата:

```bash
docker-compose run certbot certonly --webroot --webroot-path=/var/www/certbot \
  --email your_email@domain.com --agree-tos --no-eff-email \
  -d yourdomain.com -d www.yourdomain.com
```

### Перезапуск Nginx:

```bash
docker-compose restart nginx
```

---

## 6️⃣ PostgreSQL Бэкапы

- Контейнер `postgres_backup`
- Бэкап каждый день, хранится 7 дней
- Путь к бэкапам: `./postgres_backups`

---

## 🛠 Полезные команды

| Команда                                       | Описание                                 |
|----------------------------------------------|------------------------------------------|
| `docker-compose up --build`                  | Собрать и запустить проект               |
| `docker-compose exec django bash`            | Войти внутрь Django контейнера           |
| `docker-compose exec django python manage.py migrate` | Применить миграции             |
| `docker-compose exec django python manage.py collectstatic --noinput` | Статика |
| `docker-compose logs -f celery`              | Логи Celery worker                       |

---

## 💻 Полезные ресурсы

- [Django Docs](https://docs.djangoproject.com/)
- [Celery Docs](https://docs.celeryq.dev/)
- [Flower Monitor](https://flower.readthedocs.io/)
- [Docker Compose](https://docs.docker.com/compose/)

---

## ✅ Готово!

Проект готов к продакшену с авторизацией, подтверждением email, фоновыми задачами и бэкапами.

**Есть вопросы или хочешь настроить CI/CD?** Напиши! 🎯
