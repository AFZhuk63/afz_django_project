from allauth.socialaccount import providers
from django.contrib.auth import get_user_model


def socialaccount_providers(request):
    """
    Контекстный процессор для добавления списка социальных провайдеров в контекст шаблона
    """
    return {
        'socialaccount_providers': list(providers.registry.provider_map.values())
    }


def user_profile(request):
    """
    Контекстный процессор для добавления профиля пользователя в контекст шаблона
    Возвращает None если пользователь не аутентифицирован или у него нет профиля
    """
    User = get_user_model()
    context = {'user_profile': None}

    if request.user.is_authenticated:
        try:
            # Предполагаем, что профиль доступен через related_name 'profile'
            context['user_profile'] = request.user.profile
        except AttributeError:
            # Если у пользователя нет профиля
            pass

    return context