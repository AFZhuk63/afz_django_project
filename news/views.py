import json
from datetime import timedelta

from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db.models import F, Q, Count
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.decorators.http import require_POST
from django.views.generic.base import ContextMixin
from django.views.generic import CreateView, DeleteView, ListView, TemplateView, UpdateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import FormView
import logging
from firstproject import settings
from .forms import ArticleForm, ArticleUploadForm, CommentForm
from .models import Article, Favorite, Category, Like, Tag, Dislike, Comment, UserAction

from django.core.cache import cache
import unidecode
from django.db import models
from django.utils.text import slugify

# Инициализация логгера
logger = logging.getLogger(__name__)

class BaseMixin(ContextMixin):
    def __init__(self):
        self.request = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        menu = [
            {"title": "Главная", "url": "/", "url_name": "index"},
            {"title": "О проекте", "url": "/about/", "url_name": "about"},
            {"title": "Каталог", "url": "/news/catalog/", "url_name": "news:catalog"},
            {"title": "Добавить статью", "url": "/news/add/", "url_name": "news:add_article"},
            {"title": "Избранное", "url": "/news/favorites/", "url_name": "news:favorites"},
        ]

        if self.request.user.is_authenticated:
            menu.append({
                "title": "avatar",
                "username": self.request.user.username,
                "avatar_url": self.request.user.profile.get_avatar_url() if hasattr(self.request.user,
                                                                                    'profile') else f'{settings.MEDIA_URL}avatars/default-avatar.png',
                "url": "/news/profile/",
                "url_name": "news:profile"
            })

        context.update({
            "users_count": get_user_model().objects.count(),
            "news_count": Article.objects.count(),
            "categories": Category.objects.all(),
            "menu": menu,
        })
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


class ToggleDislikeView(BaseToggleStatusView):
    model = Dislike


def get_comments_count(request, article_id):
    """Получение количества комментариев"""
    comments = Comment.objects.filter(article_id=article_id, is_active=True)
    data = [{
        'author': c.author.username,
        'text': c.text,
        'created_at': c.created_at.strftime("%d.%m.%Y %H:%M")
    } for c in comments]
    return JsonResponse(data, safe=False)


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
            self.set_articles_data(data)
            self.set_current_index(0)
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
    cache_timeout = 60 * 5  # 5 минут кеширования

    def get_featured_news(self):
        """Топ-новость (самая популярная за последние 12 часов)"""
        cache_key = 'main_featured_news'
        featured = cache.get(cache_key)

        if not featured:
            featured = Article.objects.filter(
                publication_date__gte=timezone.now() - timedelta(hours=12),
                is_active=True,
                status=True
            ).select_related('category', 'author') \
                .prefetch_related('tags') \
                .order_by('-likes', '-publication_date') \
                .first()

            cache.set(cache_key, featured, self.cache_timeout)

        return featured

    def get_news_by_time_period(self, hours_start, hours_end, limit):
        """Новости за определенный временной период"""
        now = timezone.now()
        return Article.objects.filter(
            publication_date__range=(now - timedelta(hours=hours_end),
                                     now - timedelta(hours=hours_start)),
            is_active=True,
            status=True
        ).select_related('category', 'author') \
                   .prefetch_related('tags') \
                   .order_by('-likes', '-publication_date')[:limit]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        try:
            # Топ-новость (горизонтальная карточка)
            context['featured_news'] = self.get_featured_news()

            # Новости по временным периодам
            context['top_news'] = self.get_news_by_time_period(0, 12, 8)  # 0-12 часов
            context['hot_news'] = self.get_news_by_time_period(12, 24, 12)  # 12-24 часа
            context['archive_news'] = self.get_news_by_time_period(24, 48, 16)  # 24-48 часов

            # Для отладки
            context['news_counts'] = {
                'featured': 1 if context['featured_news'] else 0,
                'top': len(context['top_news']),
                'hot': len(context['hot_news']),
                'archive': len(context['archive_news'])
            }

        except Exception as e:
            logger.error(f"Error in MainView: {str(e)}", exc_info=True)
            context.update({
                'featured_news': None,
                'top_news': [],
                'hot_news': [],
                'archive_news': [],
                'error': str(e)
            })

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


class AddArtilceView(LoginRequiredMixin, BaseMixin, CreateView):
    model = Article
    form_class = ArticleForm
    template_name = 'news/add_article.html'
    redirect_field_name = 'next'  # Имя параметра URL, используемого для перенаправления после успешного входа в систему
    success_url = reverse_lazy('news:catalog')

    def form_valid(self, form):
        form.instance.author = self.request.user
        # Если пользователь не модератор и не админ, устанавливаем статус "не проверено"
        if not (self.request.user.is_superuser or self.request.user.groups.filter(name="Moderator").exists()):
            form.instance.status = 0  # или False, в зависимости от типа поля
        return super().form_valid(form)

    def generate_unique_slug(self, title):
        base_slug = slugify(unidecode.unidecode(title))
        unique_slug = base_slug
        num = 1
        while Article.objects.filter(slug=unique_slug).exists():
            unique_slug = f"{base_slug}-{num}"
            num += 1
        return unique_slug


class ArticleUpdateView(LoginRequiredMixin, BaseMixin, UpdateView):
    model = Article
    form_class = ArticleForm
    template_name = 'news/edit_article.html'
    context_object_name = 'article'
    redirect_field_name = 'next'  # Имя параметра URL, используемого для перенаправления после успешного входа в систему
    success_url = reverse_lazy('news:catalog')

    def get_queryset(self):
        qs = super().get_queryset()
        # Если пользователь - администратор или модератор, разрешаем редактировать любые статьи
        if self.request.user.is_superuser or self.request.user.groups.filter(name="Moderator").exists():
            return qs
        # Иначе разрешаем редактировать только статьи, автором которых является пользователь
        return qs.filter(author=self.request.user)

    def get_success_url(self):
        return reverse_lazy('news:detail_article_by_id', kwargs={'pk': self.object.pk})


class ArticleDeleteView(LoginRequiredMixin, BaseMixin, DeleteView):
    model = Article
    template_name = 'news/delete_article.html'
    context_object_name = 'article'
    success_url = reverse_lazy('news:catalog')
    redirect_field_name = 'next'  # Имя параметра URL, используемого для перенаправления после успешного входа в систему

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.is_superuser or self.request.user.groups.filter(name="Moderator").exists():
            return qs
        return qs.filter(author=self.request.user)


class UserProfileView(LoginRequiredMixin, BaseMixin, TemplateView):
    template_name = 'news/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Информация о пользователе
        context['profile_user'] = user

        # Статьи пользователя
        context['user_articles'] = Article.objects.filter(author=user).order_by('-publication_date')

        # История действий
        context['user_actions'] = UserAction.objects.filter(user=user).order_by('-timestamp')[:50]

        return context


@login_required
def add_comment(request, article_id):
    article = get_object_or_404(Article, pk=article_id)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.article = article
            comment.author = request.user
            parent_id = request.POST.get('parent_id')
            if parent_id:
                comment.parent = Comment.objects.get(id=parent_id)
            comment.save()
    return redirect('news:detail_article_by_id', pk=article_id)


def like_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if request.user in comment.dislikes.all():
        comment.dislikes.remove(request.user)
    if request.user in comment.likes.all():
        comment.likes.remove(request.user)
    else:
        comment.likes.add(request.user)
    return JsonResponse({'likes': comment.likes.count(), 'dislikes': comment.dislikes.count()})

@login_required
@require_POST
def dislike_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if request.user in comment.likes.all():
        comment.likes.remove(request.user)
    if request.user in comment.dislikes.all():
        comment.dislikes.remove(request.user)
    else:
        comment.dislikes.add(request.user)
    return JsonResponse({'likes': comment.likes.count(), 'dislikes': comment.dislikes.count()})


class MainView(TemplateView):
    template_name = 'main.html'
    cache_timeout = 60 * 15  # 15 минут (если используешь кэш)

    def get_news_by_level(self, level, limit):
        return Article.objects.filter(
            level=level,
            is_active=True,
            status=True
        ).annotate(
            like_count=Count('likes')
        ).order_by('-like_count', '-publication_date')[:limit]

    def get_top_news(self):
        # 1. Попробовать is_featured + level TOP
        top_news = Article.objects.filter(
            is_featured=True,
            level=Article.Level.TOP,
            is_active=True,
            status=True,
            image__isnull=False
        ).annotate(
            like_count=Count('likes')
        ).order_by('-like_count', '-publication_date').first()

        # 2. Иначе — любую TOP статью по лайкам
        if not top_news:
            top_news = Article.objects.filter(
                level=Article.Level.TOP,
                is_active=True,
                status=True,
                image__isnull=False
            ).annotate(
                like_count=Count('likes')
            ).order_by('-like_count', '-publication_date').first()

        # 3. Иначе — любую свежую статью с картинкой
        if not top_news:
            top_news = Article.objects.filter(
                is_active=True,
                status=True,
                image__isnull=False
            ).annotate(
                like_count=Count('likes')
            ).order_by('-publication_date').last()

        return top_news

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Получаем уровни
        context['level1'] = self.get_news_by_level(Article.Level.TOP, 8)
        context['level2'] = self.get_news_by_level(Article.Level.HOT, 12)
        context['level3'] = self.get_news_by_level(Article.Level.ARCHIVE, 6)

        # Формируем общую структуру
        context['news_grid'] = {
            'level1': context['level1'],
            'level2': context['level2'],
            'level3': context['level3'],
        }

        # Главная статья
        context['top_news'] = self.get_top_news()

        # Отладочная инфа
        context['cache_info'] = {
            'top_news': context['top_news'].title if context['top_news'] else "None",
            'level_1_count': len(context['level1']),
            'level_2_count': len(context['level2']),
            'level_3_count': len(context['level3']),
        }

        return context


def index(request):
    return None