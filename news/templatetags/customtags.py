#
# from django import template
# from ..models import Like
#
# register = template.Library()
#
# @register.filter(name='has_liked')
# def has_liked(article, ip_address):
#     return Like.objects.filter(article=article, ip_address=ip_address).exists()

from django import template
from news.models import Like  # Убедитесь, что путь к модели правильный

register = template.Library()

@register.filter(name='has_liked')
def has_liked(article, user):
    """Проверяет, поставил ли пользователь лайк статье."""
    if user.is_authenticated:
        return Like.objects.filter(article=article, user=user).exists()
    return False  # Гости не могут ставить лайки