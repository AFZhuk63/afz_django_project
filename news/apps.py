from django.apps import AppConfig


class NewsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'news'
    verbose_name = 'Новость' # Этот атрибут задает человеко-читаемое имя для модели или поля в единственном числе.
    verbose_name_plural = 'Новости' # Этот атрибут задает человеко-читаемое имя для модели или поля в множественном числе.