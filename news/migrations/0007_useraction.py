# Generated by Django 5.1.5 on 2025-04-03 18:55

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0006_alter_dislike_options_alter_dislike_unique_together_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UserAction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action_type', models.CharField(choices=[('article_create', 'Создание статьи'), ('article_edit', 'Редактирование статьи'), ('article_delete', 'Удаление статьи'), ('comment_add', 'Добавление комментария'), ('profile_update', 'Обновление профиля')], max_length=50)),
                ('description', models.CharField(max_length=255)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Действие пользователя',
                'verbose_name_plural': 'Действия пользователей',
                'ordering': ['-timestamp'],
            },
        ),
    ]
