from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404

from news.models import Article
from .models import Article
"""
Информация в шаблоны будет браться из базы данных
Но пока, мы сделаем переменные, куда будем записывать информацию, которая пойдет в 
контекст шаблона
"""


def main(request):
    """
    Представление рендерит шаблон main.html
    """
    # return HttpResponse('Hello, world!')  # Вернёт страницу с надписью "Hello world!"
    return render(request, 'main.html', context=info)


def about(request):
    """Представление рендерит шаблон about.html"""
    # return HttpResponse('information page')
    return render(request, 'about.html', context=info)


def catalog(request):
    return HttpResponse('Каталог новостей')


def get_categories(request):
    """
    Возвращает все категории для представления в каталоге
    """
    return HttpResponse('All categories')


def get_news_by_category(request, slug):
    """
    Возвращает новости по категории для представления в каталоге
    """
    return HttpResponse(f'News by category {slug}')


def get_news_by_tag(request, slug):
    """
    Возвращает новости по тегу для представления в каталоге
    """
    return HttpResponse(f'News by tag {slug}')


def get_category_by_name(request, slug):
    return HttpResponse(f"Категория {slug}")


def get_all_news(request):
    """
   Принимает информацию о проекте (словарь info)
   """
    # return render(request, 'news/catalog.html', context=info)
    articles = Article.objects.all()


info = {
    "users_count": 100600,
    "news_count": 100600,
    "menu": [
        {"title": "Главная", "url": "/", "url_name": "index"},
        {"title": "О проекте", "url": "/about/", "url_name": "about"},
        {"title": "Каталог", "url": "/news/catalog/", "url_name": "catalog"},
    ]
}

# def get_news_by_id(request, news_id):
#     if news_id > 10:
#         return HttpResponse('Такой новости нет', status=404)
#     return HttpResponse(f'Вы открыли новость {news_id}')  # Вернёт страницу с надписью "Вы открыли новость {news_id}"


def get_detail_article_by_id(request, article_id):
    """
    Возвращает детальную информацию по новости для представления
    """
    article = get_object_or_404(Article, id=article_id)
    info = {
        'article': article,
        "users_count": 5,
        "news_count": 10,
        "menu": [
            {"title": "Главная", "url": "/", "url_name": "index"},
            {"title": "О проекте", "url": "/about/", "url_name": "about"},
            {"title": "Каталог", "url": "/news/catalog/", "url_name": "catalog"},
        ],
    }
    return render(request, 'news/article_detail.html', context=info)