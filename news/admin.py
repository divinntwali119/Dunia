from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import News


@admin.register(News)
class NewsAdmin(ModelAdmin):
    list_display = ('title', 'category', 'published_date')
    search_fields = ('title', 'description')
    list_filter = ('category', 'published_date')
