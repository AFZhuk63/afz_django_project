from django.urls import path
from . import views
from news.views import GetAllNewsViews

app_name = 'news'

# будет иметь префикс в urlах /news/
urlpatterns = [
    path('catalog/', views.GetAllNewsViews.as_view(), name='catalog'),
    path('catalog/<int:pk>/', views.ArticleDetailView.as_view(), name='detail_article_by_id'),
    path('catalog/<slug:slug>/', views.ArticleDetailView.as_view(), name='detail_article_by_slag'),
    path('tag/<int:tag_id>/', views.GetNewsByTagView.as_view(), name='get_news_by_tag'),
    path('category/<int:category_id>/', views.GetNewsByCategoryView.as_view(), name='get_news_by_category'),
    path('search/', views.SearchNewsView.as_view(), name='search_news'),
    path('like/<int:article_id>/', views.ToggleLikeView.as_view(), name='toggle_like'),
    path('dislike/<int:article_id>/', views.ToggleDislikeView.as_view(), name='toggle_dislike'),
    path('article/<int:article_id>/comment/', views.add_comment, name='add_comment'),  # Добавлен маршрут для комментариев
    path('article/<int:article_id>/comments/count/', views.get_comments_count, name='get_comments_count'),
    path('favorite/<int:article_id>/', views.ToggleFavoriteView.as_view(), name='toggle_favorite'),
    path('favorites/', views.FavoritesView.as_view(), name='favorites'),
    path('add/', views.AddArtilceView.as_view(), name='add_article'),
    path('edit/<int:pk>/', views.ArticleUpdateView.as_view(), name='article_update'),
    path('delete/<int:pk>/', views.ArticleDeleteView.as_view(), name='article_delete'),
    path('upload_json/', views.UploadJsonView.as_view(), name='upload_json'),
    path('edit_article_from_json/<int:index>/', views.EditArticleFromJsonView.as_view(), name='edit_article_from_json'),
]