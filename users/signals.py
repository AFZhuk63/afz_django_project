from django.db.models.signals import post_save
from django.dispatch import receiver
from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model
from news.models import UserAction  # Импортируем модель для логирования

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