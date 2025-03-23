import json

from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import F, Q
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic.base import ContextMixin
from django.views.generic import CreateView, DeleteView, ListView, TemplateView, UpdateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import FormView


from .forms import ArticleForm, ArticleUploadForm
from .models import Article, Favorite, Category, Like, Tag

import unidecode
from django.db import models
from django.utils.text import slugify


"""
Информация в шаблоны будет браться из базы данных
Но пока, мы сделаем переменные, куда будем записывать информацию, которая пойдет в 
контекст шаблона
"""
# Пример данных для новостей

class BaseMixin(ContextMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "users_count": 5,
                "news_count": len(Article.objects.all()),
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
                    {"title": "Добавить статью",
                     "url": "/news/add/",
                     "url_name": "news:add_article"},
                    {"title": "Избранное",
                     "url": "/news/favorites/",
                     "url_name": "news:favorites"},
                ],
            }
        )
        return context


class BaseArticleListView(BaseMixin, ListView):
    model = Article
    template_name = 'news/catalog.html'
    context_object_name = 'news'
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_ip'] = self.request.META.get('REMOTE_ADDR')
        return context


class FavoritesView(BaseArticleListView):
    def get_queryset(self):
        ip_address = self.request.META.get('REMOTE_ADDR')
        return Article.objects.filter(favorites__ip_address=ip_address)


class SearchNewsView(BaseArticleListView):
    def get_queryset(self):
        return Article.objects.search(self.request.GET.get('q'))


class GetNewsByCategoryView(BaseArticleListView):
    def get_queryset(self):
        return Article.objects.by_category(self.kwargs['category_id'])


class GetNewsByTagView(BaseArticleListView):
    def get_queryset(self):
        return Article.objects.by_tag(self.kwargs['tag_id'])


class GetAllNewsView(BaseArticleListView):
    def get_queryset(self):
        return Article.objects.sorted(
            sort=self.request.GET.get('sort', 'publication_date'),
            order=self.request.GET.get('order', 'desc')
        )


class BaseToggleStatusView(BaseMixin, View):
    model = None  # Дочерний класс должен определить модель

    def post(self, request, article_id, *args, **kwargs):
        article = get_object_or_404(Article, pk=article_id)
        ip_address = request.META.get('REMOTE_ADDR')
        obj, created = self.model.objects.get_or_create(article=article, ip_address=ip_address)
        if not created:
            obj.delete()
        return redirect('news:detail_article_by_id', pk=article_id)


class ToggleFavoriteView(BaseToggleStatusView):
    model = Favorite


class ToggleLikeView(BaseToggleStatusView):
    model = Like


class BaseJsonFormView(BaseMixin, FormView):
    """Базовый класс для работы с JSON-файлами статей."""

    def get_articles_data(self):
        return self.request.session.get('articles_data', [])

    def set_articles_data(self, data):
        self.request.session['articles_data'] = data

    def get_current_index(self):
        return self.request.session.get('current_index', 0)

    def set_current_index(self, index):
        self.request.session['current_index'] = index


class UploadJsonView(BaseJsonFormView):

    template_name = 'news/upload_json.html'
    form_class = ArticleUploadForm
    success_url = '/news/catalog/'

    def form_valid(self, form):
        json_file = form.cleaned_data['json_file']
        try:
            data = json.load(json_file)
            errors = form.validate_json_data(data)
            if errors:
                return self.form_invalid(form)
            self.request.session['articles_data'] = data
            self.request.session['current_index'] = 0
            return redirect('news:edit_article_from_json', index=0)
        except json.JSONDecodeError:
            form.add_error(None, 'Неверный формат JSON-файла')
            return self.form_invalid(form)


class EditArticleFromJsonView(BaseJsonFormView):
    template_name = 'news/edit_article_from_json.html'
    form_class = ArticleForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        index = self.kwargs['index']
        articles_data = self.get_articles_data()
        if index >= len(articles_data):
            return redirect('news:catalog')
        article_data = articles_data[index]
        kwargs['initial'] = {
            'title': article_data['fields']['title'],
            'content': article_data['fields']['content'],
            'category': get_object_or_404(Category, name=article_data['fields']['category']),
            'tags': [get_object_or_404(Tag, name=tag) for tag in article_data['fields']['tags']]
        }
        return kwargs

    def form_valid(self, form):
        index = self.kwargs['index']
        articles_data = self.get_articles_data()
        article_data = articles_data[index]

        if 'next' in self.request.POST:
            save_article(article_data, form)
            self.set_current_index(index + 1)
            return redirect('news:edit_article_from_json', index=index + 1)
        elif 'save_all' in self.request.POST:
            save_article(article_data, form)
            for i in range(index + 1, len(articles_data)):
                save_article(articles_data[i])
            del self.request.session['articles_data']
            del self.request.session['current_index']
            return redirect('news:catalog')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(info)
        index = self.kwargs['index']
        articles_data = self.get_articles_data()
        context['index'] = index
        context['total'] = len(articles_data)
        context['is_last'] = index == len(articles_data) - 1
        return context


def save_article(article_data, form=None):
    fields = article_data['fields']
    title = fields['title']
    content = fields['content']
    category_name = fields['category']
    tags_names = fields['tags']
    category = Category.objects.get(name=category_name)
    # Генерируем slug до создания статьи
    base_slug = slugify(unidecode.unidecode(title))
    unique_slug = base_slug
    num = 1
    while Article.objects.filter(slug=unique_slug).exists():
        unique_slug = f"{base_slug}-{num}"
        num += 1
    if form:
        article = form.save(commit=False)
        article.slug = unique_slug
        article.save()
        # Обновляем теги
        article.tags.set(form.cleaned_data['tags'])
    else:
        article = Article(
            title=title,
            content=content,
            category=category,
            slug=unique_slug
        )
        article.save()
        # Добавляем теги к статье
        for tag_name in tags_names:
            tag = Tag.objects.get(name=tag_name)
            article.tags.add(tag)
    return article


class ArticleDetailView(BaseMixin, DetailView):
    model = Article
    template_name = 'news/article_detail.html'
    context_object_name = 'article'

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        article = self.get_object()

        viewed_articles = request.session.get('viewed_articles', [])
        if article.id not in viewed_articles:
            article.views += 1
            article.save()
            viewed_articles.append(article.id)
            request.session['viewed_articles'] = viewed_articles

        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_ip'] = self.request.META.get('REMOTE_ADDR')
        return context


class MainView(BaseMixin, TemplateView):
    template_name = 'main.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_ip'] = self.request.META.get('REMOTE_ADDR')
        return context


class AboutView(BaseMixin, TemplateView):
    template_name = 'about.html'


class GetAllNewsViews(BaseMixin, ListView):
    model = Article
    template_name = 'news/catalog.html'
    context_object_name = 'news'
    paginate_by = 10

    def get_queryset(self):
        # считаем параметры из GET-запроса
        sort = self.request.GET.get('sort', 'publication_date')  # по умолчанию сортируем по дате загрузки
        order = self.request.GET.get('order', 'desc')  # по умолчанию сортируем по убыванию

        # Проверяем дали ли мы разрешение на сортировку по этому полю
        valid_sort_fields = {'publication_date', 'views'}
        if sort not in valid_sort_fields:
            sort = 'publication_date'

        # Обрабатываем направление сортировки
        order_by = f'-{sort}' if order == 'desc' else sort

        return Article.objects.select_related('category').prefetch_related('tags').order_by(order_by)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_ip'] = self.request.META.get('REMOTE_ADDR')
        return context


class AddArtilceView(BaseMixin, CreateView):
    model = Article
    form_class = ArticleForm
    template_name = 'news/add_article.html'

    def form_valid(self, form):
        article = form.save(commit=False)
        article.slug = self.generate_unique_slug(form.cleaned_data['title'])
        article.save()
        form.save_m2m()

        return redirect('news:detail_article_by_id', pk=article.id)

    def generate_unique_slug(self, title):
        base_slug = slugify(unidecode.unidecode(title))
        unique_slug = base_slug
        num = 1
        while Article.objects.filter(slug=unique_slug).exists():
            unique_slug = f"{base_slug}-{num}"
            num += 1
        return unique_slug


class ArticleUpdateView(BaseMixin, UpdateView):
    model = Article
    form_class = ArticleForm
    template_name = 'news/edit_article.html'
    context_object_name = 'article'

    def get_success_url(self):
        return reverse_lazy('news:detail_article_by_id', kwargs={'pk': self.object.pk})


class ArticleDeleteView(BaseMixin, DeleteView):
    model = Article
    template_name = 'news/delete_article.html'
    context_object_name = 'article'
    success_url = reverse_lazy('news:catalog')


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
    """
      Возвращает детальную информацию по новости для представления
    """
    article = get_object_or_404(Article, id=article_id)

    # Увеличиваем счетчик просмотров только один раз за сессию для каждой новости
    viewed_articles = request.session.get('viewed_articles', [])
    if article_id not in viewed_articles:
        article.views += 1
        article.save()
        viewed_articles.append(article_id)
        request.session['viewed_articles'] = viewed_articles

    context = {**info, 'article': article}

# Рендерим шаблон article_detail.html
    return render(request, 'news/article_detail.html', context=context)


def get_detail_article_by_title(request, title):
    article = get_object_or_404(Article, slug=title)

    context = {**info, 'article': article, 'user_ip': request.META.get('REMOTE_ADDR'), }
    return render(request, 'news/article_detail.html', context=context)


# @csrf_exempt
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


def favorites(request): # Lesson 19
    ip_address = request.META.get('REMOTE_ADDR') # Lesson 19
    favorite_articles = Article.objects.filter(favorites__ip_address=ip_address) # Lesson 19
    context = {**info, 'news': favorite_articles, 'news_count': len(favorite_articles), 'page_obj': favorite_articles, 'user_ip': request.META.get('REMOTE_ADDR'), } # Lesson 19
    return render(request, 'news/catalog.html', context=context) # Lesson 19


# @login_required
def favorites_list(request):
    favorites = Favorite.objects.filter(user=request.user).select_related('article')
    return render(request, 'news/favorites.html', {'favorites': favorites})


def add_article(request):
    if request.method == 'POST':
        form = ArticleForm(request.POST)
        if form.is_valid():
            # собираем данные формы
            title = form.cleaned_data['title']
            content = form.cleaned_data['content']
            category = form.cleaned_data['category']
            # сохраняем статью в базу данных
            article = Article(title=title, content=content, category=category)
            article.save()
            # получаем id созданной статьи
            article_id = article.pk
            return HttpResponseRedirect(f'/news/catalog/{article_id}')
    else:
        form = ArticleForm()

    context = {'form': form, 'menu': info['menu']}

    return render(request, 'news/add_article.html', context=context)
