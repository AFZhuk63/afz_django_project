Урок 18. первые два задания
1. Добавление поисковика

Чтобы реализовать функциональность поиска новостей по заголовку и содержанию, выполняя фильтрацию с использованием Q из django.db.models, вам нужно выполнить следующие шаги:

1. Создание представления для поиска новостей в views.py

from django.shortcuts import render
from django.db.models import Q
from .models import News  # Предполагается, что модель News существует

def search_news(request):
    query = request.GET.get('q', '')
    if query:
        # Используем Q для сложных запросов
        news = News.objects.filter(
            Q(title__icontains=query) | Q(content__icontains=query)
        )
    else:
        news = News.objects.all()

    return render(request, 'news/search_results.html', {'news': news, 'query': query})
Мы получаем ключевое слово поиска через request.GET.get('q', '').
Используем Q для того, чтобы фильтровать новости по заголовку (title) и содержанию (content). icontains выполняет поиск без учета регистра.
Если ключевое слово пустое, возвращаем все новости.

1.2 Обновление шаблона base.html для добавления формы поиска
В вашем шаблоне base.html добавьте форму для поиска новостей:

<form method="GET" action="{% url 'news:search_news' %}" class="form-inline my-2 my-lg-0">
    <input class="form-control mr-sm-2" type="search" placeholder="Поиск" aria-label="Search" name="q" value="{{ query }}">
    <button class="btn btn-outline-success my-2 my-sm-0" type="submit">Поиск</button>
</form>
Форма отправляет GET-запрос на представление search_news.
Значение поля поиска сохраняется в переменной query, чтобы форма могла отображать текущий запрос.

1.3. Обновление файла urls.py
В файле urls.py добавьте маршрут для представления search_news:

from django.urls import path
from . import views

app_name = 'news'

urlpatterns = [
    # другие маршруты
    path('search/', views.search_news, name='search_news'),
]
Мы добавили новый маршрут, который будет вызывать представление search_news.

1.4. Шаблон для отображения результатов поиска
Создайте новый шаблон search_results.html для отображения результатов поиска:


<h2>Результаты поиска для "{{ query }}"</h2>

{% if news %}
    <ul>
        {% for item in news %}
            <li>
                <h3>{{ item.title }}</h3>
                <p>{{ item.content }}</p>
            </li>
        {% endfor %}
    </ul>
{% else %}
    <p>Новостей не найдено по запросу "{{ query }}".</p>
{% endif %}
В шаблоне отображаются результаты поиска или сообщение, если новости не найдены.
Заключение
Теперь, когда вы настроили представление для поиска новостей, обновили форму поиска в шаблоне и добавили соответствующий маршрут, пользователи смогут искать новости по заголовку и содержанию.

2. Добавление пагинатора

Пошаговое руководство по добавлению пагинации в проект Django
🔹 Шаг 1: Добавление пагинации в представление get_all_news (views.py)
Первоначально представление get_all_news возвращало все статьи сразу. Мы добавили поддержку пагинации с помощью Paginator, чтобы разделить новости на страницы (по 10 новостей на страницу).

✅ Внесенные изменения в views.py:

Добавлен импорт Paginator:

from django.core.paginator import Paginator
#Обновлено представление get_all_news:

def get_all_news(request):
    """Каталог новостей с пагинацией и сортировкой"""
    sort = request.GET.get('sort', 'publication_date')
    order = request.GET.get('order', 'desc')

    valid_sort_fields = {'publication_date', 'views'}
    if sort not in valid_sort_fields:
        sort = 'publication_date'

    order_by = sort if order == 'asc' else f'-{sort}'

    articles = Article.objects.select_related('category').prefetch_related('tags').order_by(order_by)

    # Добавляем пагинацию
    paginator = Paginator(articles, 10)  # 10 новостей на страницу
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {**info, 'page_obj': page_obj, 'news_count': paginator.count}
    return render(request, 'news/catalog.html', context)
Теперь page_obj передается в шаблон, а не news.

🔹 Шаг 2: Добавление пагинации в представления для категорий и тегов (views.py)
Фильтрация по категориям и тегам также должна поддерживать постраничный вывод.

✅ Внесенные изменения в views.py:
Добавлена пагинация в news_list_by_category и news_list_by_tag:

def news_list_by_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    articles = Article.objects.filter(category=category)

    paginator = Paginator(articles, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {**info, 'page_obj': page_obj, 'category': category, 'news_count': paginator.count}
    return render(request, 'news/catalog.html', context)

def news_list_by_tag(request, tag_id):
    tag = get_object_or_404(Tag, pk=tag_id)
    articles = Article.objects.filter(tags=tag)

    paginator = Paginator(articles, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {**info, 'page_obj': page_obj, 'tag': tag, 'news_count': paginator.count}
    return render(request, 'news/catalog.html', context)
Теперь на страницах с фильтрацией также работает постраничный вывод.

🔹 Шаг 3: Обновление catalog.html для отображения пагинации
В шаблоне catalog.html ранее выводился список статей через news, теперь он заменен на page_obj, а также добавлены кнопки переключения страниц.

✅ Внесенные изменения в catalog.html:

Используем page_obj вместо news:

{% for article in page_obj %}

Добавлен блок навигации для пагинации:
<div class="pagination mt-4 text-center">
    <span class="step-links">
        {% if page_obj.has_previous %}
            <a href="?page=1" class="btn btn-primary">&laquo; Первая</a>
            <a href="?page={{ page_obj.previous_page_number }}" class="btn btn-primary">Предыдущая</a>
        {% endif %}

        <span class="current">Страница {{ page_obj.number }} из {{ page_obj.paginator.num_pages }}</span>

        {% if page_obj.has_next %}
            <a href="?page={{ page_obj.next_page_number }}" class="btn btn-primary">Следующая</a>
            <a href="?page={{ page_obj.paginator.num_pages }}" class="btn btn-primary">Последняя &raquo;</a>
        {% endif %}
    </span>
</div>
Теперь на странице каталога отображается постраничная навигация.

🔹 Шаг 4: Исправление ошибки AttributeError: module 'news.views' has no attribute 'catalog_view'
В файле news/urls.py был указан catalog_view, которого в views.py не существует.

✅ Исправленный код в news/urls.py:

from django.urls import path
from . import views

app_name = 'news'

urlpatterns = [
    path('catalog/', views.get_all_news, name='catalog'),
]
Заменили views.catalog_view на views.get_all_news.

🔹 Шаг 5: Перезапуск сервера
После всех изменений остановили сервер (CTRL + C) и перезапустили его:

python manage.py runserver
Пагинация работает корректно! 🚀

📌 Итог
✅ Paginator теперь разбивает новости на страницы.
✅ Все представления (get_all_news, news_list_by_category, news_list_by_tag) поддерживают пагинацию.
✅ catalog.html обновлен и показывает кнопки переключения страниц.
✅ Исправлена ошибка с catalog_view в urls.py.

Что делает page_obj?
page_obj — это специальный объект Paginator, который содержит:

page_obj.object_list — список статей для текущей страницы.
page_obj.number — номер текущей страницы.
page_obj.paginator.num_pages — общее количество страниц.
page_obj.has_next / page_obj.has_previous — проверяет, есть ли следующая или предыдущая страница.
👉 Благодаря page_obj, шаблон catalog.html теперь правильно отображает только нужные новости для каждой страницы. 