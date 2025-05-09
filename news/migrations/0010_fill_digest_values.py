# Generated by Django 5.1.5 on 2025-04-12 20:52
from django.db import migrations
from django.utils import timezone

def fill_defaults(apps, schema_editor):
    Article = apps.get_model('news', 'Article')
    # Обновляем только NULL-значения
    Article.objects.filter(last_level_update__isnull=True).update(
        last_level_update=timezone.now()
    )
    Article.objects.filter(card_size__isnull=True).update(
        card_size='md'
    )
    Article.objects.filter(level__isnull=True).update(
        level=1
    )


class Migration(migrations.Migration):
    dependencies = [
        ('news', '0009_add_digest_fields'),
    ]

    operations = [
        migrations.RunPython(
            fill_defaults,
            reverse_code=migrations.RunPython.noop
        ),
    ]