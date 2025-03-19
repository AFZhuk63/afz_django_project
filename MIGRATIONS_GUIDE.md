# 🛠 Правила работы с миграциями Django

## 1️⃣ Основные правила:
- Каждый разработчик **всегда коммитит и пушит миграции вместе с изменениями в models.py**.
- Не удаляйте миграции локально без согласования!

### Схема работы при изменениях в models.py:
```bash
python manage.py makemigrations
python manage.py migrate
git add .
git commit -m "Изменения в models.py: описание"
git push origin main
```

---

## 2️⃣ Проверка перед началом работы:
```bash
git pull origin main
python manage.py showmigrations
```
Проверьте, что миграции актуальны.

---

## 3️⃣ Сброс миграций (по договорённости):

### Шаги:
1. Удалить папку migrations (кроме `__init__.py`):
```bash
rm -rf your_app/migrations/*
touch your_app/migrations/__init__.py
```

2. Сбросить базу данных:
```bash
python manage.py flush
```

3. Создать новую миграцию:
```bash
python manage.py makemigrations
python manage.py migrate
```

4. Зафиксировать и отправить:
```bash
git add .
git commit -m "Сброс миграций и новая initial"
git push origin main
```

---

## 4️⃣ Единое имя приложения
Для одинаковых миграций нужно договориться об однаковом названии приложений (news, blog и т.д.).

---

## 📉 Всегда в начале и конце сессии:
```bash
git pull origin main
python manage.py showmigrations
```

