Решение для реализации профиля пользователя с вкладками в вашем Django-проекте.

1. Добавляем модель UserAction для истории действий
В models.py добавляем:

python

class UserAction(models.Model):
    ACTION_CHOICES = [
        ('article_create', 'Создание статьи'),
        ('article_edit', 'Редактирование статьи'),
        ('article_delete', 'Удаление статьи'),
        ('comment_add', 'Добавление комментария'),
        ('profile_update', 'Обновление профиля'),
    ]
    
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    action_type = models.CharField(max_length=50, choices=ACTION_CHOICES)
    description = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Действие пользователя'
        verbose_name_plural = 'Действия пользователей'
    
    def __str__(self):
        return f"{self.user.username} - {self.get_action_type_display()} - {self.timestamp}"
2. Создаем представление для профиля
В views.py добавляем:


class UserProfileView(LoginRequiredMixin, BaseMixin, TemplateView):
    template_name = 'news/profile.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Информация о пользователе
        context['profile_user'] = user
        
        # Статьи пользователя
        context['user_articles'] = Article.objects.filter(author=user).order_by('-publication_date')
        
        # История действий
        context['user_actions'] = UserAction.objects.filter(user=user).order_by('-timestamp')[:50]
        
        return context
3. Добавляем URL для профиля
В urls.py добавляем:

path('profile/', views.UserProfileView.as_view(), name='profile'),
4. Обновляем меню в BaseMixin
В **views.py** обновляем меню в классе BaseMixin:

"menu": [
    {"title": "Главная", "url": "/", "url_name": "index"},
    {"title": "О проекте", "url": "/about/", "url_name": "about"},
    {"title": "Каталог", "url": "/news/catalog/", "url_name": "news:catalog"},
    {"title": "Добавить статью", "url": "/news/add/", "url_name": "news:add_article"},
    {"title": "Избранное", "url": "/news/favorites/", "url_name": "news:favorites"},
    {"title": "Мой профиль", "url": "/news/profile/", "url_name": "news:profile"},
],
5. Создаем шаблон профиля
Создаем файл news/profile.html:

{% extends "base.html" %}
{% load static %}

{% block content %}
<div class="profile-container">
  <!-- Шапка профиля -->
  <div class="profile-header card card-shadow mb-4">
    <div class="card-body">
      <div class="d-flex align-items-center">
        <div class="avatar-container me-4">
          <img src="{% static 'img/default-avatar.png' %}" alt="Аватар" class="profile-avatar rounded-circle">
        </div>
        <div>
          <h2>{{ profile_user.get_full_name|default:profile_user.username }}</h2>
          <p class="text-muted mb-1">@{{ profile_user.username }}</p>
          <p class="text-muted mb-0">{{ profile_user.email }}</p>
        </div>
      </div>
    </div>
  </div>

  <!-- Вкладки -->
  <ul class="nav nav-tabs mb-4" id="profileTabs" role="tablist">
    <li class="nav-item" role="presentation">
      <button class="nav-link active" id="info-tab" data-bs-toggle="tab" data-bs-target="#info" type="button" role="tab">Информация</button>
    </li>
    <li class="nav-item" role="presentation">
      <button class="nav-link" id="articles-tab" data-bs-toggle="tab" data-bs-target="#articles" type="button" role="tab">Мои статьи</button>
    </li>
    <li class="nav-item" role="presentation">
      <button class="nav-link" id="history-tab" data-bs-toggle="tab" data-bs-target="#history" type="button" role="tab">История действий</button>
    </li>
  </ul>

  <!-- Содержимое вкладок -->
  <div class="tab-content" id="profileTabsContent">
    <!-- Вкладка информации -->
    <div class="tab-pane fade show active" id="info" role="tabpanel">
      <div class="card card-shadow">
        <div class="card-body">
          <div class="mb-3">
            <h5 class="card-title">Основная информация</h5>
            <p><strong>Имя пользователя:</strong> {{ profile_user.username }}</p>
            <p><strong>Email:</strong> {{ profile_user.email }}</p>
            <p><strong>Дата регистрации:</strong> {{ profile_user.date_joined|date:"d.m.Y" }}</p>
          </div>
          <div class="d-flex gap-2">
            <a href="{% url 'account_change_password' %}" class="btn btn-primary">Изменить пароль</a>
            <a href="{% url 'account_email' %}" class="btn btn-outline-secondary">Управление email</a>
          </div>
        </div>
      </div>
    </div>

    <!-- Вкладка статей -->
    <div class="tab-pane fade" id="articles" role="tabpanel">
      <div class="card card-shadow">
        <div class="card-body">
          <div class="d-flex justify-content-between align-items-center mb-3">
            <h5 class="card-title mb-0">Мои статьи</h5>
            <a href="{% url 'news:add_article' %}" class="btn btn-primary btn-sm">Добавить статью</a>
          </div>
          
          {% if user_articles %}
            <div class="list-group">
              {% for article in user_articles %}
                <div class="list-group-item">
                  <div class="d-flex justify-content-between align-items-center">
                    <div>
                      <h6 class="mb-1">{{ article.title }}</h6>
                      <small class="text-muted">
                        {{ article.publication_date|date:"d.m.Y" }} | 
                        Просмотры: {{ article.views }} | 
                        Комментарии: {{ article.comments.count }}
                      </small>
                    </div>
                    <div class="btn-group">
                      <a href="{% url 'news:detail_article_by_id' article.id %}" class="btn btn-sm btn-outline-primary">Просмотр</a>
                      <a href="{% url 'news:article_update' article.id %}" class="btn btn-sm btn-outline-secondary">Редактировать</a>
                    </div>
                  </div>
                </div>
              {% endfor %}
            </div>
          {% else %}
            <div class="alert alert-info">У вас пока нет статей.</div>
          {% endif %}
        </div>
      </div>
    </div>

    <!-- Вкладка истории -->
    <div class="tab-pane fade" id="history" role="tabpanel">
      <div class="card card-shadow">
        <div class="card-body">
          <h5 class="card-title mb-3">История действий</h5>
          
          {% if user_actions %}
            <div class="timeline">
              {% for action in user_actions %}
                <div class="timeline-item">
                  <div class="timeline-icon">
                    {% if action.action_type == "article_create" %}
                      <i class="bi bi-file-earmark-plus"></i>
                    {% elif action.action_type == "article_edit" %}
                      <i class="bi bi-pencil-square"></i>
                    {% elif action.action_type == "article_delete" %}
                      <i class="bi bi-trash"></i>
                    {% elif action.action_type == "comment_add" %}
                      <i class="bi bi-chat-square-text"></i>
                    {% else %}
                      <i class="bi bi-person-circle"></i>
                    {% endif %}
                  </div>
                  <div class="timeline-content">
                    <p class="mb-1">{{ action.description }}</p>
                    <small class="text-muted">{{ action.timestamp|date:"d.m.Y H:i" }}</small>
                  </div>
                </div>
              {% endfor %}
            </div>
          {% else %}
            <div class="alert alert-info">История действий пуста.</div>
          {% endif %}
        </div>
      </div>
    </div>
  </div>
</div>

<style>
  .profile-avatar {
    width: 120px;
    height: 120px;
    object-fit: cover;
  }
  
  .timeline {
    position: relative;
    padding-left: 30px;
  }
  
  .timeline-item {
    position: relative;
    padding-bottom: 20px;
  }
  
  .timeline-icon {
    position: absolute;
    left: -30px;
    top: 0;
    width: 24px;
    height: 24px;
    background: #f8f9fa;
    border: 2px solid #dee2e6;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  .timeline-content {
    padding-left: 15px;
    border-left: 2px solid #dee2e6;
  }
  
  .timeline-item:last-child .timeline-content {
    border-left: 2px solid transparent;
  }
</style>
{% endblock %}

6. Добавляем логирование действий
Создаем файл signals.py:


from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Article, Comment, UserAction

User = get_user_model()

@receiver(post_save, sender=Article)
def log_article_action(sender, instance, created, **kwargs):
    if created:
        UserAction.objects.create(
            user=instance.author,
            action_type='article_create',
            description=f'Создал статью "{instance.title}"'
        )
    else:
        UserAction.objects.create(
            user=instance.author,
            action_type='article_edit',
            description=f'Обновил статью "{instance.title}"'
        )

@receiver(post_delete, sender=Article)
def log_article_deletion(sender, instance, **kwargs):
    UserAction.objects.create(
        user=instance.author,
        action_type='article_delete',
        description=f'Удалил статью "{instance.title}"'
    )

@receiver(post_save, sender=Comment)
def log_comment_action(sender, instance, created, **kwargs):
    if created:
        UserAction.objects.create(
            user=instance.author,
            action_type='comment_add',
            description=f'Добавил комментарий к статье "{instance.article.title}"'
        )

@receiver(post_save, sender=User)
def log_profile_update(sender, instance, created, **kwargs):
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
Подключить сигналы в apps.py вашего приложения.

7. Дополнительные улучшения
Загрузка аватара: Можно добавить модель UserProfile с аватаром и расширить стандартную модель пользователя.

Пагинация: Добавить пагинацию для списка статей и истории действий.

Фильтрация: Реализовать фильтрацию истории по типу действия и дате.

Это решение органично впишется в ваш проект, используя уже существующие стили (card-shadow и другие) и структуру. Вкладки реализованы на Bootstrap, что соответствует вашему текущему стилю.