from django.core.files.storage import default_storage
from django.db import models
from django.contrib.auth import get_user_model
from django.dispatch import receiver
from django.db.models.signals import post_save
import os

from firstproject import settings

User = get_user_model()


class Profile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,  # Удаление профиля при удалении пользователя
        related_name='profile',    # Доступ через user.profile
        verbose_name='Пользователь' # Человекочитаемое имя
    )
    avatar = models.ImageField(
        upload_to='avatars/%Y/%m/%d/',  # Автоматическая сортировка по дате
        blank=True,                     # Необязательное поле
        null=True,                      # Разрешено NULL в БД
        verbose_name='Аватар',          # Подпись в админке
        default='avatars/default-avatar.png'   # Дефолтный аватар
    )

    def __str__(self):
        return f'Profile of {self.user.username}'

    def get_avatar_url(self):
        if self.avatar and self.avatar.name != 'avatars/default-avatar.png':
            try:
                if default_storage.exists(self.avatar.name):
                    return self.avatar.url
            except:
                pass
        return '/media/avatars/default-avatar.png'  # Явный абсолютный путь # Убедитесь, что файл существует по этому пути

    def save(self, *args, **kwargs):
        # Удаляем старый аватар при загрузке нового
        if self.pk:
            old_avatar = Profile.objects.get(pk=self.pk).avatar
            if old_avatar and old_avatar != self.avatar and old_avatar.name != 'avatars/default-avatar.png':
                if os.path.isfile(old_avatar.path):
                    os.remove(old_avatar.path)
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Удаляем файл аватара при удалении профиля
        if self.avatar and self.avatar.name != 'avatars/default-avatar.png':
            if os.path.isfile(self.avatar.path):
                os.remove(self.avatar.path)
        super().delete(*args, **kwargs)

@receiver(post_save, sender=get_user_model())
def create_user_profile(sender, instance, created, **kwargs):
    """Автоматически создает профиль при создании пользователя"""
    if created:
        Profile.objects.get_or_create(user=instance)


@receiver(post_save, sender=get_user_model())
def save_user_profile(sender, instance, **kwargs):
    """Автоматически сохраняет профиль при сохранении пользователя"""
    if hasattr(instance, 'profile'):
        instance.profile.save()
    else:
        # На случай, если профиль был удален
        Profile.objects.get_or_create(user=instance)