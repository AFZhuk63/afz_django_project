import unidecode

from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Q, F
from django.utils import timezone
from django.utils.text import slugify
from django.contrib.auth.models import User


class ArticleQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)

    def by_category(self, category_id):
        return self.active().filter(category_id=category_id)

    def by_tag(self, tag_id):
        return self.active().filter(tags__id=tag_id)

    def search(self, query):
        return self.active().filter(Q(title__icontains=query) | Q(content__icontains=query))

    def sorted(self, sort='publication_date', order='desc'):
        valid_sort_fields = {'publication_date', 'views'}
        if sort not in valid_sort_fields:
            sort = 'publication_date'
        order_by = f'-{sort}' if order == 'desc' else sort
        return self.active().order_by(order_by)


class AllArticleManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset()


class ArticleManager(models.Manager):
    def get_queryset(self):
        return ArticleQuerySet(self.model, using=self._db)

    def active(self):
        return self.get_queryset().active()

    def by_category(self, category_id):
        return self.get_queryset().by_category(category_id)

    def by_tag(self, tag_id):
        return self.get_queryset().by_tag(tag_id)

    def search(self, query):
        return self.get_queryset().search(query)

    def sorted(self, sort='publication_date', order='desc'):
        return self.get_queryset().sorted(sort, order)


class Category(models.Model):
    name = models.CharField(max_length=255, verbose_name='Категория')

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'Categories'  # без указания этого параметра, таблица в БД будет называться вида 'news_categorys'
        verbose_name = 'Категория'  # единственное число для отображения в админке
        verbose_name_plural = 'Категории'  # множественное число для отображения в админке
        ordering = ['name']  # указывает порядок сортировки модели по умолчанию


class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name='Тег')

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'Tags'  # без указания этого параметра, таблица в БД будет называться вида 'news_tags'
        verbose_name = 'Тег'  # единственное число для отображения в админке
        verbose_name_plural = 'Теги'  # множественное число для отображения в админке


#
#
class Article(models.Model):
    # === ИСХОДНЫЙ КОД (НАЧАЛО) ===
    class Status(models.IntegerChoices):
        UNCHECKED = 0, 'не проверено'
        CHECKED = 1, 'проверено'

    title = models.CharField(max_length=255, verbose_name='Заголовок')
    content = models.TextField(verbose_name='Содержание')
    publication_date = models.DateTimeField(auto_now_add=True, verbose_name='Дата публикации')
    views = models.IntegerField(default=0, verbose_name='Просмотры')
    category = models.ForeignKey('Category', on_delete=models.CASCADE, default=1, verbose_name='Категория')
    tags = models.ManyToManyField('Tag', related_name='article', verbose_name='Теги')
    slug = models.SlugField(unique=True, blank=True, verbose_name='Слаг')
    is_active = models.BooleanField(default=True, verbose_name='Активна')
    status = models.BooleanField(default=0,
                               choices=(map(lambda x: (bool(x[0]), x[1]), Status.choices)),
                               verbose_name='Проверено')

    author = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, default=None,
                             verbose_name='Автор')

    image = models.ImageField(
        upload_to='articles/%Y/%m/%d/',
        blank=True,
        null=True,
        verbose_name='Изображение'

    )
    # === ИСХОДНЫЙ КОД (КОНЕЦ) ===

    # === ДОБАВЛЕНИЯ (НАЧАЛО) ===
    class Level(models.IntegerChoices):
        TOP = 1, 'Топ (0-12 часов)'
        HOT = 2, 'Горячее (12-24 часа)'
        ARCHIVE = 3, 'Архив (24-48 часов)'
        OLD = 4, 'Устаревшие (>48 часов)'

    level = models.PositiveSmallIntegerField(
        choices=Level.choices,
        default=Level.TOP,
        verbose_name='Уровень важности'
    )

    class CardSize(models.TextChoices):
        SMALL = 'sm', '6.8x6.8 см'
        MEDIUM = 'md', '7x14 см'
        LARGE = 'lg', '14x14 см'

    card_size = models.CharField(
        max_length=2,
        choices=[('sm', '6.8x6.8 см'), ('md', '7x14 см'), ('lg', '14x14 см')],
        default='md',
        verbose_name='Размер карточки'
    )

    is_featured = models.BooleanField(
        default=False,
        verbose_name='В избранном дайджеста'
    )

    level = models.PositiveSmallIntegerField(
        choices=[(1, 'Топ (0-12 часов)'), (2, 'Горячее (12-24 часа)'),
                 (3, 'Архив (24-48 часов)'), (4, 'Устаревшие (>48 часов)')],
        default=1,
        verbose_name='Уровень важности'
    )

    last_level_update = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Последнее обновление уровня',

    )

    def update_level(self):
        """
        Автоматически обновляет уровень статьи на основе времени с момента публикации.
        Обновляет last_level_update при изменении уровня.
        """
        now = timezone.now()
        hours_passed = (now - self.publication_date).total_seconds() / 3600

        # Определяем новый уровень
        if hours_passed > 48:
            new_level = self.Level.OLD  # Устаревшие (>48 часов)
        elif hours_passed > 24:
            new_level = self.Level.ARCHIVE  # Архив (24-48 часов)
        elif hours_passed > 12:
            new_level = self.Level.HOT  # Горячее (12-24 часа)
        else:
            new_level = self.Level.TOP  # Топ (0-12 часов)

        # Если уровень изменился - сохраняем
        if self.level != new_level:
            self.level = new_level
            self.last_level_update = now
            self.save(update_fields=['level', 'last_level_update'])
    # === ДОБАВЛЕНИЯ (КОНЕЦ) ===
    original_url = models.URLField(
        blank=True,
        null=True,
        verbose_name='Оригинальная ссылка'
    )
    external_author = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='Автор (оригинал)'
    )
    # === ИСХОДНЫЙ КОД (НАЧАЛО) ===
    objects = ArticleManager()
    all_objects = AllArticleManager()

    def save(self, *args, **kwargs):
        # Сохраняем статью, чтобы получить id
        super().save(*args, **kwargs)
        if not self.slug:
            base_slug = slugify(unidecode.unidecode(self.title))  # чтобы у них был уникальный код
            base_slug = "untitled"  # Установите значение по умолчанию (моя фантазия 22.03.25)
            base_slug = base_slug[:100]  # Обрезаем slug до 100 символов (моя фантазия 22.03.25)
            unique_slug = base_slug
            num = 1
            while Article.objects.filter(slug=unique_slug).exists():
                unique_slug = f"{base_slug}-{num}"
                num += 1
            self.slug = unique_slug
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'Articles'  # без указания этого параметра, таблица в БД будет называться 'news_artcile'
        verbose_name = 'Статья'  # единственное число для отображения в админке
        verbose_name_plural = 'Статьи'  # множественное число для отображения в админке
        # Добавлены новые индексы для оптимизации
        indexes = [
            models.Index(fields=['level']),
            models.Index(fields=['is_featured']),
            models.Index(fields=['publication_date']),
        ]

    def __str__(self):
        return self.title

    # === ИСХОДНЫЙ КОД (КОНЕЦ) ===


class Like(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='likes')
    ip_address = models.GenericIPAddressField()

    def __str__(self):
        return f'Like by {self.ip_address} on {self.article}'

    class Meta:
        unique_together = [['article', 'ip_address']]  # Для Like

class Dislike(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='dislikes')
    ip_address = models.GenericIPAddressField()

    def __str__(self):
        return f'Dislike by {self.ip_address} on {self.article}'

    class Meta:
        unique_together = [['article', 'ip_address']]  # Для Dislike


class Comment(models.Model):
    article = models.ForeignKey('Article', on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    text = models.TextField(verbose_name='Текст комментария')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    parent = models.ForeignKey('self', null=True, blank=True, related_name='children', on_delete=models.CASCADE)
    likes = models.ManyToManyField(get_user_model(), related_name='liked_comments', blank=True)
    dislikes = models.ManyToManyField(get_user_model(), related_name='disliked_comments', blank=True)

    @property
    def is_parent(self):
        return self.parent is None

    def get_indent_level(self):
        level = 0
        parent = self.parent
        while parent:
            level += 1
            parent = parent.parent
        return level * 3

    class Meta:
        ordering = ['created_at']


class Favorite(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='favorites')
    ip_address = models.GenericIPAddressField()

    def __str__(self):
        return f'Favorite by {self.ip_address} on {self.article}'


class UserAction(models.Model):
    ACTION_CHOICES = [
        ('article_create', 'Создание статьи'),
        ('article_edit', 'Редактирование статьи'),
        ('article_delete', 'Удаление статьи'),
        ('comment_add', 'Добавление комментария'),
        ('profile_update', 'Обновление профиля'),
        ('digest_update', 'Обновление дайджеста')  # Добавили новый тип действия
    ]

    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name='actions',
        verbose_name='Пользователь'
    )
    action_type = models.CharField(
        max_length=50,
        choices=ACTION_CHOICES,
        verbose_name='Тип действия'
    )
    description = models.CharField(
        max_length=255,
        verbose_name='Описание'
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Время действия'
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Дополнительные данные'
    )

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Действие пользователя'
        verbose_name_plural = 'Действия пользователей'
        indexes = [
            models.Index(fields=['user', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.user_id} - {self.get_action_type_display()} - {self.timestamp}"

