from django.contrib import admin
from django.http import HttpResponseNotFound
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from news import views
from users.views import (
    CustomConfirmEmailView, CustomPasswordResetDoneView,
    CustomPasswordResetFromKeyView, CustomPasswordResetFromKeyDoneView,
    CustomPasswordResetView, CustomLoginView, CustomSignupView,
    update_avatar
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.MainView.as_view(), name='index'),
    path('about/', views.AboutView.as_view(), name='about'),
    path('news/', include('news.urls', namespace='news')),
# Заглушка favicon.ico
    path('favicon.ico', lambda request: HttpResponseNotFound()),

    # Пути для работы с аватаром
    path('profile/update_avatar/', update_avatar, name='update_avatar'),

    # Allauth пути
    path('accounts/confirm-email/<str:key>/', CustomConfirmEmailView.as_view(), name='account_confirm_email'),
    path('accounts/password/reset/', CustomPasswordResetView.as_view(), name='account_reset_password'),
    path('accounts/password/reset/done/', CustomPasswordResetDoneView.as_view(), name='account_reset_password_done'),
    path('accounts/password/reset/key/<uidb36>/<str:key>/', CustomPasswordResetFromKeyView.as_view(),
         name='account_reset_password_from_key'),
    path('accounts/password/reset/key/done/', CustomPasswordResetFromKeyDoneView.as_view(),
         name='account_reset_password_from_key_done'),
    path('accounts/login/', CustomLoginView.as_view(), name='account_login'),
    path('accounts/signup/', CustomSignupView.as_view(), name='account_signup'),
    path('accounts/', include('allauth.urls')),

    # Специальный путь для сброса пароля
    path(
        'accounts/password/reset/key/q-set-password/',
        CustomPasswordResetFromKeyView.as_view(),
        kwargs={'uidb36': 'q', 'key': 'set-password'},
        name='special_password_reset'
    ),
]

# Добавляем обработку медиа-файлов только в DEBUG режиме
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # Подключаем debug_toolbar
    import debug_toolbar

    urlpatterns = [
                      path('__debug__/', include(debug_toolbar.urls)),
                  ] + urlpatterns