from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from django.core.cache import cache
from .models import Article, Category, UserAction
import logging

logger = logging.getLogger(__name__)

# Check for Celery availability
try:
    from celery import shared_task
    HAS_CELERY = True
except ImportError:
    HAS_CELERY = False
    logger = logging.getLogger(__name__)
    logger.info("Celery not available, background tasks disabled")


@receiver([post_save, post_delete], sender=Category)
def handle_category_changes(sender, instance, **kwargs):
    """
    Очистка кеша при изменении категорий.
    Логирование изменений.
    """
    cache_keys = ['categories_list', 'categories_menu', 'category_stats']
    cache.delete_many(cache_keys)
    logger.info(f"Cache cleared for keys: {cache_keys}")


@receiver(post_save, sender=Article)
def handle_article_save(sender, instance, created, **kwargs):
    """
    Расширенный обработчик сохранения статьи:
    1. Для новых статей - запускает фоновое обновление через 12 часов
    2. Для существующих - немедленно обновляет уровень
    3. Логирует все действия
    """
    if created:
        # Для новых статей откладываем проверку уровня
        if HAS_CELERY:
            schedule_level_update.apply_async(
                args=[instance.id],
                countdown=12 * 3600  # Через 12 часов
            )
        else:
            logger.warning("Celery not available, scheduling level update synchronously")
            # Run synchronously after 12 hours would require a different approach,
            # so we'll just run it immediately with a warning
            update_article_level(instance)
    else:
        # Немедленное обновление для существующих статей
        update_article_level(instance)

    log_article_action(instance, created)


if HAS_CELERY:
    @shared_task
    def schedule_level_update(article_id):
        """
        Фоновая задача для обновления уровня статьи
        """
        try:
            article = Article.objects.get(id=article_id)
            update_article_level(article)
        except Article.DoesNotExist:
            logger.error(f"Article {article_id} not found for level update")
else:
    def schedule_level_update(article_id):
        """
        Синхронная версия функции обновления уровня статьи
        """
        logger.warning("Celery not available, running schedule_level_update synchronously")
        try:
            article = Article.objects.get(id=article_id)
            update_article_level(article)
        except Article.DoesNotExist:
            logger.error(f"Article {article_id} not found for level update")


def update_article_level(article):
    """
    Общая функция обновления уровня статьи
    """
    if hasattr(article, 'update_level'):
        article.update_level()
        logger.debug(f"Updated level for article {article.id}")


if HAS_CELERY:
    @shared_task
    def update_old_articles():
        """
        Периодическая задача для массового обновления старейших статей
        """
        from .models import Article
        old_articles = Article.objects.filter(
            level__lt=Article.Level.OLD,
            publication_date__lt=timezone.now() - timezone.timedelta(hours=48)
        ).select_related('author')

        for article in old_articles:
            update_article_level(article)
        logger.info(f"Updated {old_articles.count()} old articles")
else:
    def update_old_articles():
        """
        Синхронная версия функции обновления старых статей
        """
        logger.warning("Celery not available, running update_old_articles synchronously")
        from .models import Article
        old_articles = Article.objects.filter(
            level__lt=Article.Level.OLD,
            publication_date__lt=timezone.now() - timezone.timedelta(hours=48)
        ).select_related('author')

        for article in old_articles:
            update_article_level(article)
        logger.info(f"Updated {old_articles.count()} old articles")


def log_article_action(instance, created):
    """
    Логирование действий со статьями
    """
    if instance.author:
        action = 'article_create' if created else 'article_edit'
        UserAction.objects.create(
            user=instance.author,
            action_type=action,
            description=f'Статья "{instance.title[:50]}"',
            metadata={
                'article_id': instance.pk,
                'title': instance.title,
                'action': action,
                'level': instance.level
            }
        )


@receiver(pre_save, sender=Article)
def update_article_flags(sender, instance, **kwargs):
    """
    Комплексное обновление флагов статьи:
    - is_archived (старше 48 часов)
    - is_featured (топ + популярные)
    """
    if instance.pk:  # Только для существующих статей
        hours_passed = (timezone.now() - instance.publication_date).total_seconds() / 3600

        instance.is_archived = hours_passed > 48
        instance.is_featured = (
                instance.level == Article.Level.TOP and
                instance.likes.count() > 5 and
                not instance.is_archived
        )