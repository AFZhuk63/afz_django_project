# Рефакторинг системы миграций и сигналов для статей

## Описание изменений

Этот коммит решает комплекс задач по:
1. Исправлению миграций для полей дайджеста статей (`card_size`, `is_featured`, `level`, `last_level_update`)
2. Реализации автоматического обновления уровня статей
3. Настройке фоновых задач с поддержкой работы без Celery
4. Улучшению логирования и обработки ошибок

## Ключевые изменения

### 1. Миграции
- Создана кастомная миграция `0009_add_digest_fields.py` с использованием `SeparateDatabaseAndState`
- Добавлена миграция `0010_fill_digest_values.py` для заполнения NULL-значений
- Исправлена миграция `0011_remove_null_from_last_level_update.py`

### 2. Модель Article
Добавлен метод `update_level()`:

```python
def update_level(self):
    now = timezone.now()
    hours_passed = (now - self.publication_date).total_seconds() / 3600
    
    if hours_passed > 48:
        new_level = self.Level.OLD
    elif hours_passed > 24:
        new_level = self.Level.ARCHIVE
    elif hours_passed > 12:
        new_level = self.Level.HOT
    else:
        new_level = self.Level.TOP
        
    if self.level != new_level:
        self.level = new_level
        self.last_level_update = now
        self.save(update_fields=['level', 'last_level_update'])

3. Сигналы (signals.py)
Обработка сохранения статей с отложенным обновлением

Поддержка работы с Celery и без него

Улучшенное логирование операций

Оптимизированные запросы к БД

4. Конфигурация приложения (apps.py)
Проверка наличия Celery

Улучшенная система логирования

Гибкая система регистрации сигналов

Тестирование
Применить миграции:
python manage.py migrate news

Проверить состояние данных:
python manage.py shell

from news.models import Article
print(Article.objects.filter(last_level_update__isnull=True).count())  # Должно быть 0

Проверить работу сигналов:

Создать/обновить статью и проверить логи

Убедиться, что уровень статьи корректно обновляется

Примечания
Система автоматически определяет наличие Celery

Все критические операции логируются

Для фоновых задач без Celery можно использовать django-crontab

Измененные файлы
news/migrations/0009_add_digest_fields.py

news/migrations/0010_fill_digest_values.py

news/migrations/0011_remove_null_from_last_level_update.py

news/models.py

news/signals.py

news/apps.py

news/tasks.py (новый файл)

Проверить работу сигналов:

Создать/обновить статью и проверить логи

Убедиться, что уровень статьи корректно обновляется

Примечания
Система автоматически определяет наличие Celery

Все критические операции логируются

Для фоновых задач без Celery можно использовать django-crontab

Измененные файлы
news/migrations/0009_add_digest_fields.py

news/migrations/0010_fill_digest_values.py

news/migrations/0011_remove_null_from_last_level_update.py

news/models.py

news/signals.py

news/apps.py

news/tasks.py (новый файл)


Файл готов к сохранению как `migration_and_signals_refactoring.md` и
добавлению в репозиторий. Он содержит полное описание всех изменений в формате Markdown, 
которое будет удобно читать в GitHub.