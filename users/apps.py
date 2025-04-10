from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'
    label = 'users'  # Добавьте уникальный label

    def ready(self):
        import users.signals  # Активация сигналов пользователей


