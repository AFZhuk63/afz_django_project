from django.contrib import admin
from django.utils.html import format_html
from django.contrib.admin import SimpleListFilter

from .models import Article, Category, Tag


admin.site.site_header = "Админка Info to Go"
admin.site.site_title = "Админка"
admin.site.index_title = "Привет админ! Не сломай ничего."


class ArticleSpiderFilter(SimpleListFilter):
    title = 'Внутри пауки'
    parameter_name = 'has_spiders'

    def lookups(self, request, model_admin):
        return (
            ('yes', "Есть"),
            ('no', 'Нет')
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(content__contains='пауки')
        if self.value() == 'no':
            return queryset.exclude(content__contains='пауки')
        return queryset


class TagInline(admin.TabularInline):
    model = Article.tags.through
    extra = 1


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    # list_display отображает поля в таблице
    list_display = ('pk', 'title', 'category', 'publication_date', 'views', 'status', 'is_active', 'has_spiders')
    # list_display_links позволяет указать в качестве ссылок на объект другие поля
    list_display_links = ('pk', 'title')
    # list_filter позволяет фильтровать по полям
    list_filter = ('category', 'is_active', 'status', ArticleSpiderFilter)
    # сортировка, возможна по нескольким полям, по возрастанию или по убыванию
    ordering = ('category', '-is_active')
    # search_fields позволяет искать по полям
    search_fields = ('title', 'content')
    # actions позволяет выполнять действия над выбранными записями
    actions = ('make_inactive', 'make_active', 'set_checked', 'set_unchecked')
    list_per_page = 15
    # включение иерархического отображения по дате
    date_hierarchy = 'publication_date'
    # перенос кнопок сохранения в верхнюю часть формы
    save_on_top = True # Добавили Дополнительную информацию 24.02.2025
    # fields позволяет выбирать поля для редактирования (не fieldsets)
    # fields = ('title', 'category', 'content', 'tags', 'is_active')

    # fieldsets позволяет выбирать группы полей (не работает с fields)
    fieldsets = (
        ('Главная информация', {'fields': ('title', 'content')}),
        ('Дополнительные параметры', {'fields': ('category', 'tags', 'is_active')}),
        ('Доп. инфо', {'fields': ('views', 'slug')}), # Добавили Дополнительную информацию 24.02.2025
    )

    # inlines позволяет добавлять дополнительные поля
    inlines = [TagInline]

    def get_queryset(self, request):
        return Article.all_objects.get_queryset()

    @admin.display(description='Пауки внутри')
    def has_spiders(self, article):
        return 'Да' if 'пауки' in article.content else 'Нет'

    # ВАЖНО! Убрал лишний отступ перед `@admin.action`, теперь все методы корректно оформлены
    @admin.action(description='Сделать неактивными выбранные статьи')
    def make_inactive(self, request, queryset):
        queryset.update(is_active=False)

    @admin.action(description='Сделать активными выбранные статьи')
    def make_active(self, request, queryset):
        queryset.update(is_active=True)  # исправлено (раньше ставился False)

    @admin.action(description='Отметить статьи как проверенные')
    def set_checked(self, request, queryset):
        update = queryset.update(status=Article.Status.CHECKED)
        self.message_user(request, f'{update} статей было отмечено как проверенные')

    @admin.action(description='Отметить статьи как не проверенные')
    def set_unchecked(self, request, queryset):
        update = queryset.update(status=Article.Status.UNCHECKED)
        self.message_user(request, f'{update} статей было отмечено как не проверенные', 'warning')


admin.site.register(Category)
admin.site.register(Tag)

# from django.contrib import admin
# from django.utils.html import format_html
# from django.contrib.admin import SimpleListFilter
# from django.urls import path
# from django.shortcuts import redirect
# from django.http import HttpRequest
# from .models import Article, Category, Tag
#
#
# class ArticleSpiderFilter(SimpleListFilter):
#     title = 'Внутри пауки'
#     parameter_name = 'has_spiders'
#
#     def lookups(self, request, model_admin):
#         return (
#             ('yes', "Есть"),
#             ('no', 'Нет')
#         )
#
#     def queryset(self, request, queryset):
#         if self.value() == 'yes':
#             return queryset.filter(content__contains='пауки')
#         if self.value() == 'no':
#             return queryset.exclude(content__contains='пауки')
#         return queryset
#
#
# class TagInline(admin.TabularInline):
#     model = Article.tags.through
#     extra = 1
#
#
# class ArticleAdmin(admin.ModelAdmin):
#     """Настройки для модели Article в админке"""
#
#     list_display = ('pk', 'title', 'category', 'publication_date', 'views', 'status', 'is_active', 'has_spiders')
#     list_display_links = ('pk', 'title')
#     list_filter = ('category', 'is_active', 'status', ArticleSpiderFilter)
#     ordering = ('category', '-is_active')
#     search_fields = ('title', 'content')
#     actions = ('make_inactive', 'make_active', 'set_checked', 'set_unchecked')
#     list_per_page = 20
#     date_hierarchy = 'publication_date'
#     save_on_top = True
#
#     fieldsets = (
#         ('Главная информация', {'fields': ('title', 'content')}),
#         ('Дополнительные параметры', {'fields': ('category', 'tags', 'is_active')}),
#         ('Доп. инфо', {'fields': ('views', 'slug')}),
#     )
#
#     inlines = [TagInline]
#
#     def get_queryset(self, request):
#         return Article.all_objects.get_queryset()
#
#     @admin.display(description='Пауки внутри')
#     def has_spiders(self, article):
#         return 'Да' if 'пауки' in article.content else 'Нет'
#
#     @admin.action(description='Сделать неактивными выбранные статьи')
#     def make_inactive(self, request, queryset):
#         queryset.update(is_active=False)
#
#     @admin.action(description='Сделать активными выбранные статьи')
#     def make_active(self, request, queryset):
#         queryset.update(is_active=True)
#
#     @admin.action(description='Отметить статьи как проверенные')
#     def set_checked(self, request, queryset):
#         update = queryset.update(status=Article.Status.CHECKED)
#         self.message_user(request, f'{update} статей было отмечено как проверенные')
#
#     @admin.action(description='Отметить статьи как не проверенные')
#     def set_unchecked(self, request, queryset):
#         update = queryset.update(status=Article.Status.UNCHECKED)
#         self.message_user(request, f'{update} статей было отмечено как не проверенные', 'warning')
#
#
# class CustomAdminSite(admin.AdminSite):
#     """Кастомный сайт администрирования с доп. маршрутами"""
#
#     site_header = "Админка Info to Go"
#     site_title = "Админка"
#     index_title = "Привет, админ!"
#
#     def get_urls(self):
#         urls = super().get_urls()
#         custom_urls = [
#             path('news/catalog/', self.admin_view(self.catalog_view), name='catalog_admin'),
#         ]
#         return custom_urls + urls
#
#     def catalog_view(self, request: HttpRequest):
#         """Перенаправляем /admin/news/catalog/ на клиентскую версию каталога"""
#         return redirect('/news/catalog/')
#
#
# admin_site = CustomAdminSite(name='custom_admin')
#
# admin_site.register(Article, ArticleAdmin)
# admin_site.register(Category)
# admin_site.register(Tag)
