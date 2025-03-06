from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from .models import Article, Category, Tag, News, Like
from django.db.models import F
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt

info = {
    "users_count": 5,
    "news_count": 10,
    "categories": Category.objects.all(),
    "menu": [
        {"title": "Главная",
         "url": "/",
         "url_name": "index"},
        {"title": "О проекте",
         "url": "/about/",
         "url_name": "about"},
        {"title": "Каталог",
         "url": "/news/catalog/",
         "url_name": "news:catalog"},
    ],
}


def main(request):
    """
    Представление рендерит шаблон main.html
    """
    return render(request, 'main.html', context=info)


def about(request):
    """Представление рендерит шаблон about.html"""
    return render(request, 'about.html', context=info)


def catalog(request):
    return HttpResponse('Каталог новостей')


def get_categories(request):
    """
    Возвращает все категории для представления в каталоге
    """
    return HttpResponse('All categories')


def search_news(request):
    query = request.GET.get('q', '')
    categories = Category.objects.all()
    if query:
        articles = Article.objects.filter(Q(title__icontains=query) | Q(content__icontains=query))
    else:
        articles = Article.objects.all()

    paginator = Paginator(articles, 10)  # 10 новостей на страницу
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # categories = Category.objects.all()
    context = {**info, 'page_obj': page_obj, 'news_count': len(articles), 'page_obj': page_obj,} # It`s my variant
    # context = {**info, 'news': articles, 'news_count': len(articles), 'page_obj': page_obj, } # It`s variant of Maks
    return render(request, 'news/catalog.html', context)


def get_all_news(request):
    """Каталог новостей с пагинацией и сортировкой"""
    sort = request.GET.get('sort', 'publication_date')
    order = request.GET.get('order', 'desc')

    valid_sort_fields = {'publication_date', 'views'}
    if sort not in valid_sort_fields:
        sort = 'publication_date'

    # Обрабатываем направление сортировки
    if order == 'asc':
        order_by = sort
    else:
        order_by = f'-{sort}'

    articles = Article.objects.select_related('category').prefetch_related('tags').order_by(order_by)

    paginator = Paginator(articles, 10)  # 10 новостей на страницу
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    # categories = Category.objects.all()
    # context = {**info, 'page_obj': page_obj, 'category': categories, 'news_count': paginator.count}
    context = {**info, 'page_obj': page_obj, 'news_count': len(articles), 'page_obj': page_obj, }  # стало
    return render(request, 'news/catalog.html', context)

def news_list_by_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    articles = Article.objects.filter(category=category)

    paginator = Paginator(articles, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # categories = Category.objects.all() # было
    # context = {**info, 'page_obj': page_obj, 'category': categories, 'news_count': paginator.count}# было
    context = {**info, 'page_obj': page_obj, 'news_count': len(articles), 'page_obj': page_obj,} # стало

    return render(request, 'news/catalog.html', context)


def news_list_by_tag(request, tag_id):
    tag = get_object_or_404(Tag, pk=tag_id)
    articles = Article.objects.filter(tags=tag)

    paginator = Paginator(articles, 10) # Показывать 10 новостей на странице
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # categories = Category.objects.all()
    # context = {**info, 'page_obj': page_obj, 'category': categories, 'news_count': paginator.count}
    context = {**info, 'page_obj': page_obj, 'news_count': len(articles), 'page_obj': page_obj, }  # стало
    return render(request, 'news/catalog.html', context)

def get_detail_article_by_id(request, article_id):
    article = get_object_or_404(Article, id=article_id)

    # Увеличиваем счетчик просмотров
    Article.objects.filter(pk=article_id).update(views=F('views') + 1)
    article.refresh_from_db()  # Обновить объект article из базы данных

    context = {**info, 'article': article}
    return render(request, 'news/article_detail.html', context)

def get_detail_article_by_title(request, title):
    article = get_object_or_404(Article, slug=title)

    context = {**info, 'article': article}
    return render(request, 'news/article_detail.html', context)


@csrf_exempt
def toggle_like(request, article_id):
    article = get_object_or_404(Article, id=article_id)
    ip_address = request.META.get('REMOTE_ADDR')
    like, created = Like.objects.get_or_create(article=article, ip_address=ip_address)

    if not created:
        like.delete()
        liked = False
    else:
        liked = True

    return JsonResponse({'liked': liked, 'like_count': article.likes.count()})
