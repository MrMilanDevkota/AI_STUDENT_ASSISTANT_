from django.contrib import admin
from .models import StudyMaterial, AIGeneratedContent, ChatMessage


@admin.register(StudyMaterial)
class StudyMaterialAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'file_type', 'status', 'word_count', 'created_at']
    list_filter = ['status', 'file_type']
    search_fields = ['title', 'user__username']
    readonly_fields = ['created_at', 'updated_at', 'word_count', 'vector_store_path']


@admin.register(AIGeneratedContent)
class AIGeneratedContentAdmin(admin.ModelAdmin):
    list_display = ['study_material', 'content_type', 'created_at']
    list_filter = ['content_type']


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['study_material', 'role', 'content', 'created_at']
    list_filter = ['role']
