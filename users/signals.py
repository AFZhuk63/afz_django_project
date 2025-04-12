from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model
from news.models import UserAction, Category, Article # Импортируем модель для логирования
from django.core.cache import cache
User = get_user_model()


@receiver(post_save, sender=EmailAddress)
def update_verified_status(sender, instance, **kwargs):
    """Обработчик для подтверждения email"""
    if instance.verified:
        print(f"[SIGNAL] Email подтвержден: {instance.email}")
        EmailAddress.objects.filter(user=instance.user).exclude(pk=instance.pk).update(verified=True)


@receiver(post_save, sender=User)
def log_user_actions(sender, instance, created, **kwargs):
    """Логирование действий с пользователем"""
    if created:
        UserAction.objects.create(
            user=instance,
            action_type='profile_update',
            description='Зарегистрировался в системе'
        )
    else:
        UserAction.objects.create(
            user=instance,
            action_type='profile_update',
            description='Обновил профиль'
        )


@receiver([post_save, post_delete], sender=Category)
def clear_category_cache(sender, **kwargs):
    """Очищает кеш категорий новостей."""
    cache.delete("categories")

