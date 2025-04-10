from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views


app_name = 'users'

urlpatterns = [
    path('logout/', views.LogoutUser.as_view(), name='logout'),
    path('register_done/', views.RegisterDoneView.as_view(), name='register_done'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('profile/update_avatar/', views.update_avatar, name='update_avatar'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

