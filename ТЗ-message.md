## Техническое задание (ТЗ)

### Цель  
Добавить в существующий проект **подписку на авторов и теги**. Всё размещается внутри приложения **`news`**.

### Функциональные требования  
1. **Модель подписки**  
   * Хранит связь «пользователь → объект подписки (автор или тег)».  
   * Запрещает дубли (одна подписка — одна запись).  
   * Фиксирует дату создания.

2. **Сервисная функция**  
   * `toggle_subscription(user, obj)`  
     *Создаёт* подписку, если её нет; *удаляет*, если уже есть.  
     *Возвращает* `True`, если пользователь подписался, `False` — если отписался.

3. **Вью‑слой**  
   * `POST /subscribe/<str:model>/<int:pk>/`  
     *Доступен* только авторизованным.  
     *Меняет* статус подписки и возвращает JSON `{"status": "subscribed" | "unsubscribed"}`.

4. **Уведомления по e‑mail**  
   * При **успешной публикации** новой статьи отправляется одно письмо **каждому** подписчику автора или тегов.  
   * Отправка выполняется:
     * после коммита транзакции (`transaction.on_commit`);
     * в текущем процессе Django;  
       допускается вынести вызов `send_mass_mail()` в поток `threading.Thread`, чтобы не блокировать ответ.

5. **Лента «Для вас»**  
   * URL `/feed/` доступен авторизованным.  
   * Отображает статьи авторов и тегов, на которые подписан пользователь.  
   * Сортировка — по дате публикации (новые сверху).  

### Нефункциональные требования  
* Код размещается в `news/`.  
* Используются стандартные средства Django ≥ 3.2.  
* Email‑backend по умолчанию — `django.core.mail.backends.console.EmailBackend`.  

### Критерии правильной работы  
1. При нажатии «Подписаться» в интерфейсе в БД появляется запись, повторное нажатие удаляет её.  
2. После публикации статьи в консоли выводятся письма с правильными адресатами.  
3. Страница `/feed/` показывает ожидаемые статьи, у пользователя без подписок выводится заглушка «Лента пуста».  

---

## Инструкция по реализации

---

### 1. Модель `Subscription`
*Файлы*: `news/models.py`, миграции  

```python
from django.conf import settings
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

class Subscription(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subscriptions",
    )
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    target = GenericForeignKey("content_type", "object_id")
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "content_type", "object_id")
        indexes = [models.Index(fields=["content_type", "object_id"])]

    def __str__(self):
        return f"{self.user} → {self.target}"
```

```bash
python manage.py makemigrations
python manage.py migrate
```

---

### 2. Сервис `toggle_subscription`
*Файл*: `news/services.py` (создайте, если его нет)

```python
from django.contrib.contenttypes.models import ContentType
from .models import Subscription

def toggle_subscription(user, obj):
    ct = ContentType.objects.get_for_model(obj.__class__)
    sub, created = Subscription.objects.get_or_create(
        user=user, content_type=ct, object_id=obj.pk
    )
    if not created:
        sub.delete()
    return created        # True = подписался, False = отписался
```

---

### 3. Контроллер подписки
*Файлы*: `news/views.py`, `news/urls.py`, шаблоны

```python
# views.py
from django.views import View
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from .services import toggle_subscription
from .models import User, Tag   # поправьте импорт под ваш проект

class ToggleSubscriptionView(LoginRequiredMixin, View):
    def post(self, request, model, pk):
        obj = {
            "author": get_object_or_404(User, pk=pk),
            "tag":    get_object_or_404(Tag, pk=pk),
        }.get(model)
        if obj is None:
            return HttpResponseForbidden("Unknown model")
        status = "subscribed" if toggle_subscription(request.user, obj) else "unsubscribed"
        return JsonResponse({"status": status})
```

```python
# urls.py
path("subscribe/<str:model>/<int:pk>/", ToggleSubscriptionView.as_view(), name="toggle-sub"),
```

В шаблоне статьи (пример на Django‑template):

```django
<form method="post"
      action="{% url 'toggle-sub' 'author' article.author.id %}"
      hx-post="{% url 'toggle-sub' 'author' article.author.id %}"
      hx-swap="outerHTML">
  {% csrf_token %}
  <button type="submit">
      {% if user|is_subscribed:article.author %}Отписаться{% else %}Подписаться{% endif %}
  </button>
</form>
```

(Фильтр `is_subscribed` реализуйте по желанию.)

---

### 4. Сигнал публикации статьи
*Файлы*: `news/signals.py`, `news/apps.py`

```python
# signals.py
import threading
from django.db.models.signals import post_save
from django.db import transaction
from django.dispatch import receiver
from django.core.mail import send_mass_mail
from django.contrib.contenttypes.models import ContentType

from .models import Article, Tag, Subscription

@receiver(post_save, sender=Article)
def notify_on_publish(sender, instance, created, **kwargs):
    if not created or instance.is_draft:
        return
    transaction.on_commit(lambda: _send_notifications(instance))

def _send_notifications(article):
    ct_author = ContentType.objects.get_for_model(article.author.__class__)
    ct_tag = ContentType.objects.get_for_model(Tag)

    emails = set(
        Subscription.objects.filter(
            content_type=ct_author, object_id=article.author_id
        ).values_list("user__email", flat=True)
    )
    emails |= set(
        Subscription.objects.filter(
            content_type=ct_tag,
            object_id__in=article.tags.values_list("id", flat=True),
        ).values_list("user__email", flat=True)
    )
    if not emails:
        return

    subject = f"Новая статья: «{article.title}»"
    body = f"{article.title}\n\nЧитайте: {article.get_absolute_url()}"
    messages = [(subject, body, None, [e]) for e in emails]

    # Поток, чтобы не блокировать ответ браузеру
    threading.Thread(
        target=send_mass_mail,
        args=(tuple(messages),),
        kwargs={"fail_silently": True},
        daemon=True,
    ).start()
```

```python
# apps.py
class NewsConfig(AppConfig):
    name = "news"
    def ready(self):
        from . import signals  # noqa: F401
```

---

### 5. Лента «Для вас»
*Файлы*: `news/services.py`, `news/views.py`, шаблон

```python
# services.py
from django.db.models import Q
from .models import Article, Subscription, Tag
from django.contrib.contenttypes.models import ContentType

def personalized_feed(user):
    ct_author = ContentType.objects.get_for_model(user.__class__)
    ct_tag = ContentType.objects.get_for_model(Tag)

    author_ids = Subscription.objects.filter(
        user=user, content_type=ct_author
    ).values_list("object_id", flat=True)

    tag_ids = Subscription.objects.filter(
        user=user, content_type=ct_tag
    ).values_list("object_id", flat=True)

    return (
        Article.objects.filter(
            Q(author_id__in=author_ids) | Q(tags__id__in=tag_ids),
            is_draft=False,
        )
        .distinct()
        .select_related("author")
        .prefetch_related("tags")
        .order_by("-published_at")
    )
```

```python
# views.py
from django.views.generic import ListView
from .services import personalized_feed

class MyFeedView(LoginRequiredMixin, ListView):
    template_name = "news/feed.html"
    paginate_by = 10

    def get_queryset(self):
        return personalized_feed(self.request.user)
```

```python
# urls.py
path("feed/", MyFeedView.as_view(), name="my-feed"),
```

Добавьте пункт меню «Для вас» и шаблон `feed.html` с пагинацией.

---

### 6. Проверка вручную
1. Создайте два пользователя: автора и читателя.  
2. Под читателем нажмите «Подписаться» на автора и на пару тегов.  
3. Зайдите под автором, опубликуйте новую статью.  
4. В терминале (console email backend) должны появиться письма на адрес читателя.  
5. Под читателем откройте `/feed/` — статья должна быть в списке.