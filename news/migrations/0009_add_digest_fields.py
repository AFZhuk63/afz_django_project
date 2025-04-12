# news/migrations/0009_add_digest_fields.py
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('news', '0008_alter_comment_options_comment_dislikes_comment_likes_and_more'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name='article',
                    name='card_size',
                    field=models.CharField(
                        choices=[('sm', '6.8x6.8 см'), ('md', '7x14 см'), ('lg', '14x14 см')],
                        default='md',
                        max_length=2,
                        verbose_name='Размер карточки'
                    ),
                ),
                migrations.AddField(
                    model_name='article',
                    name='is_featured',
                    field=models.BooleanField(
                        default=False,
                        verbose_name='В избранном дайджеста'
                    ),
                ),
                migrations.AddField(
                    model_name='article',
                    name='last_level_update',
                    field=models.DateTimeField(
                        auto_now_add=True,
                        null=True,
                        verbose_name='Последнее обновление уровня'
                    ),
                ),
                migrations.AddField(
                    model_name='article',
                    name='level',
                    field=models.PositiveSmallIntegerField(
                        choices=[(1, 'Топ (0-12 часов)'), (2, 'Горячее (12-24 часа)'),
                                (3, 'Архив (24-48 часов)'), (4, 'Устаревшие (>48 часов)')],
                        default=1,
                        verbose_name='Уровень важности'
                    ),
                ),
            ],
            database_operations=[],  # Поля уже есть в БД, ничего не меняем
        )
    ]