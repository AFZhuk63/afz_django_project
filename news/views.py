from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from .models import Article, Category, Tag, News
from django.db.models import F
from django.db.models import Q

info = {
    "users_count": 5,
    "news_count": 10,
    "menu": [
        {"title": "Главная", "url": "/", "url_name": "index"},
        {"title": "О проекте", "url": "/about/", "url_name": "about"},
        {"title": "Каталог", "url": "/news/catalog/", "url_name": "news:catalog"},
    ],
}

def main(request):
    return render(request, 'main.html', context=info)

def about(request):
    return render(request, 'about.html', context=info)

def search_news(request):
    query = request.GET.get('q', '')
    if query:
        articles = Article.objects.filter(
            Q(title__icontains=query) | Q(content__icontains=query)
        )
    else:
        articles = Article.objects.all()

    paginator = Paginator(articles, 15)  # 15 новостей на страницу
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    categories = Category.objects.all()
    context = {**info, 'page_obj': page_obj, 'category': categories, 'news_count': paginator.count, 'query': query}
    return render(request, 'news/catalog.html', context)

def get_all_news(request):
    """Каталог новостей с пагинацией и сортировкой"""
    sort = request.GET.get('sort', 'publication_date')
    order = request.GET.get('order', 'desc')

    valid_sort_fields = {'publication_date', 'views'}
    if sort not in valid_sort_fields:
        sort = 'publication_date'

    order_by = sort if order == 'asc' else f'-{sort}'
    articles = Article.objects.select_related('category').prefetch_related('tags').order_by(order_by)

    paginator = Paginator(articles, 15)  # 15 новостей на страницу
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    categories = Category.objects.all()
    context = {**info, 'page_obj': page_obj, 'category': categories, 'news_count': paginator.count}
    return render(request, 'news/catalog.html', context)

def news_list_by_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    articles = Article.objects.filter(category=category)

    paginator = Paginator(articles, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    categories = Category.objects.all()
    context = {**info, 'page_obj': page_obj, 'category': categories, 'news_count': paginator.count}
    return render(request, 'news/catalog.html', context)

def news_list_by_tag(request, tag_id):
    tag = get_object_or_404(Tag, pk=tag_id)
    articles = Article.objects.filter(tags=tag)

    paginator = Paginator(articles, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    categories = Category.objects.all()
    context = {**info, 'page_obj': page_obj, 'category': categories, 'news_count': paginator.count}
    return render(request, 'news/catalog.html', context)

def get_detail_article_by_id(request, article_id):
    article = get_object_or_404(Article, id=article_id)

    # Увеличиваем счетчик просмотров
    article.views += 1
    article.save()

    context = {**info, 'article': article}
    return render(request, 'news/article_detail.html', context)

def get_detail_article_by_title(request, title):
    article = get_object_or_404(Article, slug=title)

    # Увеличиваем счетчик просмотров
    article.views += 1
    article.save()

    context = {**info, 'article': article}
    return render(request, 'news/article_detail.html', context)
