def setup_periodic_tasks():
    """
    Инициализация периодических задач для Celery
    """
    from celery import current_app
    from .signals import update_old_articles

    current_app.add_periodic_task(
        3600 * 2,  # Каждые 2 часа
        update_old_articles.s(),
        name='update-old-articles'
    )