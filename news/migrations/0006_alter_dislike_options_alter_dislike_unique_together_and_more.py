# Generated by Django 5.1.5 on 2025-04-03 00:15

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0005_comment_dislike'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='dislike',
            options={},
        ),
        migrations.AlterUniqueTogether(
            name='dislike',
            unique_together=set(),
        ),
        migrations.RemoveField(
            model_name='dislike',
            name='created_at',
        ),
    ]
