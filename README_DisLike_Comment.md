Инструкция по добавлению функционала Дизлайков и Комментариев
Содержание
Добавление моделей

Миграции

Настройка админ-панели

Реализация View

Настройка URL

Интеграция в шаблоны

Дополнительные настройки

<a name="модели"></a> 1. Добавление моделей
Добавьте в news/models.py:

python
from django.contrib.auth import get_user_model
from django.db import models

class Comment(models.Model):
    article = models.ForeignKey('Article', on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    text = models.TextField(verbose_name='Текст комментария')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'

class Dislike(models.Model):
    article = models.ForeignKey('Article', on_delete=models.CASCADE, related_name='dislikes')
    ip_address = models.GenericIPAddressField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('article', 'ip_address')
        verbose_name = 'Дизлайк'
        verbose_name_plural = 'Дизлайки'
<a name="миграции"></a> 2. Миграции
Выполнил в терминале:
python manage.py makemigrations news
python manage.py migrate

# Проверка миграции
python manage.py showmigrations news
(Должна быть новая миграция с отметкой [X].)

<a name="админ-панель"></a> 3. Настройка админ-панели
Добавляю в news/admin.py:

from django.contrib import admin
from .models import Comment, Dislike

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('article', 'author', 'created_at', 'is_active')
    list_filter = ('is_active', 'created_at')

@admin.register(Dislike)
class DislikeAdmin(admin.ModelAdmin):
    list_display = ('article', 'ip_address', 'created_at')
    list_filter = ('created_at',)
<a name="view-функции"></a> 4. Реализация View
Добавил в news/views.py:

from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .forms import CommentForm

@require_POST
def toggle_dislike(request, article_id):
    article = get_object_or_404(Article, pk=article_id)
    ip_address = request.META.get('REMOTE_ADDR')
    
    dislike, created = Dislike.objects.get_or_create(
        article=article,
        ip_address=ip_address
    )
    
    if not created:
        dislike.delete()
    
    return JsonResponse({
        'dislikes_count': article.dislikes.count(),
        'status': 'removed' if not created else 'added'
    })

@require_POST
def add_comment(request, article_id):
    article = get_object_or_404(Article, pk=article_id)
    form = CommentForm(request.POST)
    
    if form.is_valid() and request.user.is_authenticated:
        comment = form.save(commit=False)
        comment.article = article
        comment.author = request.user
        comment.save()
        return redirect('news:detail_article_by_id', pk=article_id)
    
    return redirect('news:detail_article_by_id', pk=article_id)
<a name="urls"></a> 5. Настройка URL
Добавил в news/urls.py:

from django.urls import path
from . import views

urlpatterns = [
    # ... другие URL ...
    path('article/<int:article_id>/dislike/', views.toggle_dislike, name='toggle_dislike'),
    path('article/<int:article_id>/comment/', views.add_comment, name='add_comment'),
]
<a name="шаблоны"></a> 6. Интеграция в шаблоны
Добавил в шаблон статьи:

html

<!-- Дизлайк -->
<form method="post" action="{% url 'news:toggle_dislike' article.id %}">
  {% csrf_token %}
  <button type="submit">
    👎 <span id="dislikes-count">{{ article.dislikes.count }}</span>
  </button>
</form>

<!-- Комментарии -->
<div class="comments">
  {% for comment in article.comments.all %}
    <div class="comment">
      <strong>{{ comment.author }}</strong>
      <p>{{ comment.text }}</p>
      <small>{{ comment.created_at }}</small>
    </div>
  {% endfor %}
  
  <form method="post" action="{% url 'news:add_comment' article.id %}">
    {% csrf_token %}
    <textarea name="text" required></textarea>
    <button type="submit">Отправить</button>
  </form>
</div>
Run HTML
<a name="дополнительно"></a> 7. Дополнительные настройки
AJAX-версия (опционально):
javascript
Copy
// Дизлайк
document.querySelector('.dislike-form').addEventListener('submit', function(e) {
  e.preventDefault();
  fetch(this.action, {method: 'POST', headers: {'X-CSRFToken': this.csrfmiddlewaretoken.value}})
    .then(response => response.json())
    .then(data => {
      document.getElementById('dislikes-count').textContent = data.dislikes_count;
    });
});

// Комментарии
document.querySelector('.comment-form').addEventListener('submit', function(e) {
  e.preventDefault();
  const formData = new FormData(this);
  fetch(this.action, {method: 'POST', body: formData})
    .then(response => response.json())
    .then(data => {
      if(data.success) {
        // Добавление нового комментария в список
      }
    });
});
Форма комментария (news/forms.py):
python

from django import forms
from .models import Comment

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            })
        }
Проверка работоспособности
Откройте страницу статьи

Проверьте:

Кнопка дизлайка (счетчик должен увеличиваться)

Форма добавления комментария

Отображение списка комментариев

Проверьте админ-панель:

Разделы "Комментарии" и "Дизлайки"

Фильтрация и поиск

Готово! Функционал комментариев и дизлайков успешно добавлен. 🚀