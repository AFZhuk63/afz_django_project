from allauth.account.views import (ConfirmEmailView, PasswordResetDoneView, PasswordResetFromKeyView,
                                   PasswordResetFromKeyDoneView, PasswordResetView, LoginView, SignupView)
from django.contrib import messages
from django.core.files.storage import default_storage

from news.views import BaseMixin
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .forms import ProfileForm
from .models import Profile

# Кастомные представления с BaseMixin
class CustomConfirmEmailView(BaseMixin, ConfirmEmailView):
    template_name = 'account/confirm_email.html'

class CustomPasswordResetDoneView(BaseMixin, PasswordResetDoneView):
    template_name = 'account/password_reset_done.html'


class CustomLoginView(BaseMixin, LoginView):
    template_name = 'account/login.html'

class CustomPasswordResetFromKeyView(BaseMixin, PasswordResetFromKeyView):
    template_name = 'account/password_reset_from_key.html'

class CustomPasswordResetFromKeyDoneView(BaseMixin, PasswordResetFromKeyDoneView):
    template_name = 'account/password_reset_from_key_done.html'

class CustomPasswordResetView(BaseMixin, PasswordResetView):
    template_name = 'account/password_reset.html'

class CustomSignupView(BaseMixin, SignupView):
    template_name = 'account/signup.html'


from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .forms import ProfileForm

@login_required
def profile_view(request):
    # Получаем или создаем профиль для пользователя
    profile, created = Profile.objects.get_or_create(user=request.user)
    return render(request, 'users/profile.html', {
        'user': request.user,
        'profile': profile,  # Явно передаем профиль
    })

@login_required
def profile_edit(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = ProfileForm(instance=request.user.profile)

    return render(request, 'users/profile_edit.html', {'form': form})


@login_required
def update_avatar(request):
    if request.method == 'POST' and request.FILES.get('avatar'):
        try:
            profile = request.user.profile
            avatar_file = request.FILES['avatar']

            # Проверка типа файла
            if not avatar_file.content_type.startswith('image/'):
                messages.error(request, 'Можно загружать только изображения')
                return redirect('users:profile_edit')

            # Удаляем старый аватар (если не дефолтный)
            if (profile.avatar and
                    profile.avatar.name != 'avatars/default-avatar.png' and
                    default_storage.exists(profile.avatar.name)):
                default_storage.delete(profile.avatar.name)

            # Сохраняем новый
            profile.avatar.save(
                f'avatar_{request.user.id}_{avatar_file.name}',
                avatar_file
            )
            messages.success(request, 'Аватар успешно обновлён!')
        except Exception as e:
            messages.error(request, f'Ошибка: {str(e)}')

    return redirect('users:profile_edit')