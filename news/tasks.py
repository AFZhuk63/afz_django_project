from celery import shared_task
from django.core.management import call_command
from celery import current_app
from .signals import update_old_articles

def setup_periodic_tasks():
    """
    Инициализация периодических задач для Celery
    """


    current_app.add_periodic_task(
        3600 * 2,  # Каждые 2 часа
        update_old_articles.s(),
        name='update-old-articles'
    )

@shared_task
def parse_articles():
    call_command('fetch_bbc_article')
    call_command('fetch_cnn_article')