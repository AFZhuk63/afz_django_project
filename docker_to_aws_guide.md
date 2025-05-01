## Полный гайд по настройке Docker, Nginx и Django для деплоя на AWS

Этот документ описывает логику сборки проекта на Django с использованием Docker и Nginx, а также предоставляет подробную пошаговую инструкцию по настройке и запуску приложения вплоть до деплоя на сервере AWS.

---

### Необходимые требования

Перед началом убедитесь, что у вас установлены:

* Docker ([https://docs.docker.com/get-docker/](https://docs.docker.com/get-docker/))
* Docker Compose ([https://docs.docker.com/compose/install/](https://docs.docker.com/compose/install/))
* AWS EC2-инстанс с Ubuntu или Amazon Linux 2
* Открыты порты 22 (SSH), 80 (HTTP) и 443 (HTTPS) в настройках EC2
* Установлен git (опционально)
* Подготовленный Django-проект со следующей структурой:

  * manage.py
  * requirements.txt
  * settings.py (настройки базы, static, media, allowed hosts)
  * Dockerfile
  * docker-compose.yml
  * entrypoint.sh
  * create\_admin.py
  * nginx.conf
  * wait-for-db.sh

---

### Шаг 1. Подготовка файлов структуры проекта

Создайте и настройте следующие файлы в корне проекта:

#### 1. Dockerfile

Для сборки контейнера Django-приложения.

#### 2. docker-compose.yml

Оркестрация контейнеров: web (Django), db (PostgreSQL), nginx.

#### 3. entrypoint.sh

Скрипт инициализации: миграции, создание суперпользователя, сборка статики.

#### 4. create\_admin.py

Python-скрипт для создания суперпользователя (используется в entrypoint.sh).

#### 5. nginx.conf

Конфигурация Nginx для проксирования на Django (через Gunicorn).

#### 6. wait-for-db.sh

Ожидание запуска базы данных перед стартом Django-приложения.

#### 7. settings.py (Django)

Настройки подключения к базе данных, статических и медиа файлов, разрешенных хостов, и т.д.

---

### Шаг 2. Последовательность сборки и запуска

1. **Сборка контейнеров:**

```bash
docker-compose build
```

2. **Запуск контейнеров:**

```bash
docker-compose up -d
```

3. **Проверка контейнеров:**

```bash
docker-compose ps
```

4. **Просмотр логов:**

```bash
docker-compose logs nginx
```

или

```bash
docker-compose logs web
```

---

### Шаг 3. Настройка Django внутри контейнера

1. **Миграции базы данных:**

```bash
docker-compose exec web python manage.py migrate
```

2. **Создание суперпользователя:**

```bash
docker-compose exec web python manage.py createsuperuser
```

3. **Сбор статики:**

```bash
docker-compose exec web python manage.py collectstatic --noinput
```

4. **Запуск тестов (опционально):**

```bash
docker-compose exec web python manage.py test
```

---

### Шаг 4. Проверка Nginx

1. **Проверка конфигурации:**

```bash
docker-compose exec nginx nginx -t
```

2. **Проверка работы сайта:**
   Перейдите по адресу: [http://localhost](http://localhost)

3. **Проверка статики и медиа:**

```url
http://localhost/static/
http://localhost/media/
```

---

### Шаг 5. Размещение на AWS

1. **Подключение к серверу AWS EC2:**

```bash
ssh -i <your-key.pem> ec2-user@<your-ec2-public-ip>
```

2. **Копирование проекта на сервер:**

```bash
scp -i <your-key.pem> -r ./project_folder ec2-user@<your-ec2-public-ip>:/home/ec2-user
```

3. **Установка Docker и Docker Compose:**

```bash
sudo yum update -y
sudo yum install docker
sudo service docker start
sudo usermod -a -G docker ec2-user
logout
# Подключитесь снова, затем:
docker --version
```

4. **Запуск проекта на AWS:**

```bash
cd project_folder
docker-compose build
docker-compose up -d
```

5. **Проверка логов и доступности:**

```bash
docker-compose ps
docker-compose logs nginx
```

Откройте в браузере:

```url
http://<your-ec2-public-ip>
```

---

### Шаг 6. Проверка работоспособности файлов и компонентов

#### Проверка Dockerfile:

```bash
docker build -t test-django-app .
```

#### Проверка docker-compose.yml:

```bash
docker-compose config
```

#### Проверка entrypoint.sh:

Убедитесь, что файл исполняемый:

```bash
chmod +x entrypoint.sh
```

Можно протестировать внутри контейнера:

```bash
docker-compose exec web ./entrypoint.sh
```

#### Проверка create\_admin.py:

```bash
docker-compose exec web python manage.py shell < create_admin.py
```

#### Проверка wait-for-db.sh:

```bash
chmod +x wait-for-db.sh
```

Можно вручную запустить:

```bash
./wait-for-db.sh db 5432
```

#### Проверка nginx.conf:

```bash
docker-compose exec nginx nginx -t
```

#### Проверка переменных окружения и подключения:

Если вы используете .env файл:

```bash
docker-compose config | grep -i env
```

Проверка подключения к БД:

```bash
docker-compose exec web python manage.py dbshell
```

Проверка успешного рендеринга главной страницы:

```bash
curl http://localhost
```

или на AWS:

```bash
curl http://<your-ec2-public-ip>
```

---

### Заключение

Если все шаги выполнены верно, вы получите развернутое Django-приложение, работающее через Nginx и Gunicorn, в контейнерах Docker, готовое для продакшн-среды на AWS.

Для защиты приложения настройте SSL (например, через Let's Encrypt + Certbot), добавьте firewall и настройте переменные окружения (например, через `.env`).
