from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from firstproject import settings
from news import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.MainView.as_view(), name='index'),
    path('about/', views.AboutView.as_view(), name='about'),
    path('news/', include('news.urls', namespace='news')),# Убедитесь, что этот путь подключен
    path('users/', include('users.urls', namespace='users')), # подключили урлы для users
    path('accounts/', include('allauth.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
