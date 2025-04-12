from django.db import migrations, models
from django.utils import timezone


class Migration(migrations.Migration):
    dependencies = [
        ('news', '0010_fill_digest_values'),  # Убедитесь, что номер правильный
    ]

    operations = [
        migrations.AlterField(
            model_name='article',
            name='last_level_update',
            field=models.DateTimeField(
                default=timezone.now,  # Временное значение по умолчанию
                verbose_name='Последнее обновление уровня'
            ),
        ),
        migrations.AlterField(
            model_name='article',
            name='last_level_update',
            field=models.DateTimeField(
                auto_now_add=True,     # Финальный вариант поля
                verbose_name='Последнее обновление уровня'
            ),
        ),
    ]