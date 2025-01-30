# from django.db import models

# Create your models here.
from django.db import models


class Article(models.Model):
    ...
    title = models.CharField(max_length=255, unique=True)
    content = models.TextField()
    publication_date = models.DateTimeField(auto_now_add=True)
    views = models.IntegerField(default=0)
    category = models.ForeignKey('Category', on_delete=models.CASCADE, default=1)
    tags = models.ManyToManyField('Tag', related_name='articles')

    def __str__(self):
        return self.title


class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name

