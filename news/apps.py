from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)


class NewsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'news'
    verbose_name = 'Новость'
    verbose_name_plural = 'Новости'

    def ready(self):
        """
        Регистрация сигналов с проверкой наличия Celery
        """
        try:
            from . import signals  # noqa
            logger.info(f"{self.name} signals registered")

            # Пытаемся инициализировать Celery-задачи (если Celery установлен)
            try:
                from celery import current_app
                from .tasks import setup_periodic_tasks
                setup_periodic_tasks()
                logger.info("Celery tasks initialized")
            except ImportError:
                logger.info("Celery not installed, skipping periodic tasks")

        except ImportError as e:
            logger.error(f"Signal import error: {e}")