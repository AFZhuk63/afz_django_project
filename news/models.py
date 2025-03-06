import unidecode
from django.db import models
from django.utils.text import slugify
from django.utils import timezone
from django.contrib.auth.models import User


class AllArticleManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset()

class ArticleManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)

    def sorted_by_title(self):
        return self.get_queryset().order_by('-title')


class Category(models.Model):
    name = models.CharField(max_length=255, verbose_name='Категория')

    class Meta:
        db_table = 'Categories'
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['name']

    def __str__(self):
        return self.name


class News(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    publication_date = models.DateTimeField(auto_now_add=True) # Добавлено поле publication_date

    def __str__(self):
        return self.title


class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        db_table = 'Tags'
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Article(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    views = models.IntegerField(default=0)
    publication_date = models.DateTimeField(auto_now_add=True)  # Добавлено поле publication_date

    class Status(models.TextChoices):
        UNCHECKED = '0', 'Не проверено'
        CHECKED = '1', 'Проверено'

    status = models.CharField(
        max_length=1,
        choices=Status.choices,
        default=Status.UNCHECKED,
        verbose_name="Проверено"
    )

    category = models.ForeignKey('Category', on_delete=models.CASCADE, default=1, verbose_name='Категория')
    tags = models.ManyToManyField('Tag', related_name='articles', verbose_name='Теги')
    slug = models.SlugField(unique=True, blank=True, verbose_name='Слаг')
    is_active = models.BooleanField(default=True, verbose_name='Активна')

    objects = ArticleManager()
    all_objects = AllArticleManager()

    def like_count(self):
        return self.likes.count()

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(unidecode.unidecode(self.title))
            self.slug = base_slug
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'Articles'
        verbose_name = 'Статья'
        verbose_name_plural = 'Статьи'

    def __str__(self):
        return self.title


class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes', default=1)
    ip_address = models.GenericIPAddressField()
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='likes')

    class Meta:
        unique_together = ('user', 'article', 'ip_address')

    def __str__(self):
        return f"{self.ip_address} - {self.article.title}"
