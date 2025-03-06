from django.urls import path
from . import views

app_name = 'news'  # Добавляем эту строку!
# будет иметь префикс в urlах /news/
urlpatterns = [
    # path('', views.get_all_news),
    path('catalog/', views.get_all_news, name='catalog'),
    # path('catalog/', views.catalog, name='catalog'),
    path('catalog/<int:article_id>/', views.get_detail_article_by_id, name='detail_article_by_id'),
    # path('catalog/<slug:slug>/', views.get_category_by_name),
    path('catalog/<slug:title>/', views.get_detail_article_by_title, name='detail_article_by_title'),
    # ✅ Новый маршрут для фильтрации новостей по тегу
    path('tag/<int:tag_id>/', views.news_list_by_tag, name='news_by_tag'),
    path('category/<int:category_id>/', views.news_list_by_category, name='category_news'),
    # другие маршруты
    path('search_news/', views.search_news, name='search_news'),
    path('toggle_like/<int:article_id>/', views.toggle_like, name='toggle_like'),
]
