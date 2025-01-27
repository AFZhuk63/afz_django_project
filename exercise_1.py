## Цель практики
# Освоение базовых навыков работы с шаблонами Django, 
# включая создание и использование базовых шаблонов, блоков, включений и динамической вставки данных.

## Задачи

### 1. Создание базового шаблона `base.html`

#### Описание
# Создайте базовый шаблон `base.html` в папке `templates` в корне проекта. 
# Укажите кастомный путь для Django в файле `settings.py` в разделе `TEMPLATES`.

#### Шаги
# 1. Создайте папку `templates` в корне проекта.
# 2. Внутри папки `templates` создайте файл `base.html`.
# 3. В файле `settings.py` в разделе `TEMPLATES` укажите путь к папке `templates`:
#    ```python
#    'DIRS': [BASE_DIR / 'templates'],
#    ```
# 4. Подключите базовый шаблон для теста функции `main` в файле `views.py`.

### 2. Синтаксис блоков в шаблонах. `{% block %}` и `{% extends %}`

#### Описание
# Опишите блок `content` в базовом шаблоне `base.html`. Создайте шаблон `main.html`,
# который расширяет базовый шаблон `base.html` через `{% extends %}` и переопределите 
# блоки `content` и `footer` через `{% block %}`.

#### Шаги
# 1. В файле `base.html` опишите блок `content`:
#    ```html
#    {% block content %}
#    {% endblock %}
#    ```
# 2. Создайте файл `main.html` в папке `templates`.
# 3. В файле `main.html` расширьте базовый шаблон `base.html`:
#    ```html
#    {% extends 'base.html' %}
#    ```
# 4. Переопределите блоки `content` и `footer` в файле `main.html`:
#    ```html
#    {% block content %}
#    <!-- Ваш контент -->
#    {% endblock %}

#    {% block footer %}
#    <!-- Ваш футер -->
#    {% endblock %}
#    ```
# 5. Подключите шаблон `main.html` в функции `main` в файле `views.py`.

### 3. Создание шаблона `nav_menu.html` и подключение его в базовом шаблоне через `{% include %}`

#### Описание
# Создайте каталог `includes` в папке `templates` в корне проекта. 
# Создайте шаблон `nav_menu.html` в папке `includes` и подключите его в базовом
# шаблоне `base.html` через `{% include %}`.

#### Шаги
# 1. Создайте папку `includes` в папке `templates`.
# 2. Внутри папки `includes` создайте файл `nav_menu.html`.
# 3. В файле `nav_menu.html` напишите навигационное меню,
# используя шаблонный тег `{% url %}` для создания ссылок на страницы по их именам в файле `urls.py`.
# 4. Подключите шаблон `nav_menu.html` в базовом шаблоне `base.html`:
#    ```html
#    {% include 'includes/nav_menu.html' %}
#    ```
# 5. Добавьте датасет с новостями и меню, чтобы проверить работу шаблона.

### 4. Начало работы над каталогом новостей (динамическая вставка данных в шаблон, цикл + `include`)

#### Описание
# Создайте `include` в папке `templates` в приложении `news`.
# Внутри создайте шаблон `article_preview.html`,
# который принимает на вход словарь с данными о новости и возвращает новость,
# которая будет вставлена в каталог новостей в шаблоне `catalog.html` в цикле.

#### Шаги
# 1. Создайте папку `includes` в папке `templates` в приложении `news`.
# 2. Внутри папки `includes` создайте файл `article_preview.html`.
# 3. В файле `article_preview.html` напишите шаблон,
# который принимает на вход словарь с данными о новости и возвращает новость.
# 4. В шаблоне `catalog.html` используйте цикл для вставки новостей из словаря,
# подключая шаблон `article_preview.html` через `{% include %}`.

### 5. Продолжение работы над каталогом статей (динамическая вставка данных в шаблон, цикл + `include`)

#### Описание
# Добавьте шаблон `article_detail.html` в папке `templates/news`.
# Доделайте `include` в шаблоне `catalog.html` и вставьте в него новости из словаря.
# Обновите функцию `get_detail_article_by_id` для поиска статьи по ID в словаре и возврата
# шаблона `article_detail.html` или `404`.

#### Шаги
# 1. Создайте файл `article_detail.html` в папке `templates/news`.
# 2. В файле `article_detail.html` напишите шаблон для детального отображения статьи.
# 3. В шаблоне `catalog.html` доделайте `include` для вставки новостей из словаря.
# 4. Обновите функцию `get_detail_article_by_id` в файле `views.py`:
#    ```python
#    def get_detail_article_by_id(request, article_id):
#        # Ваш код для поиска статьи по ID в словаре
#        if article:
#            return render(request, 'news/article_detail.html', {'article': article})
#        else:
#            return HttpResponseNotFound("Статья не найдена")
#    ```

## Финальный результат:
# 1. Создание и подключение базового шаблона `base.html`.
# 2. Правильное использование блоков `{% block %}` и `{% extends %}`.
# 3. Создание и подключение шаблона `nav_menu.html` через `{% include %}`.
# 4. Динамическая вставка данных в шаблон с использованием цикла и `{% include %}`.
# 5. Обновление функции для поиска статьи по ID и возврата шаблона `article_detail.html` или `404`.
