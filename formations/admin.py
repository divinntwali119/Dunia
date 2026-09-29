from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import Formation


@admin.register(Formation)
class FormationAdmin(ModelAdmin):
    list_display = ('title', 'category', 'duration', 'level', 'created_at')
    list_filter = ('category', 'level', 'created_at')
    search_fields = ('title', 'description')
