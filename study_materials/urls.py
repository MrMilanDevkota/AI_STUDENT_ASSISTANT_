"""URL patterns for the study_materials app."""

from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),

    # Upload & Delete
    path('upload/', views.upload_material, name='upload'),
    path('material/<int:material_id>/delete/', views.delete_material, name='delete_material'),

    # AI Features
    path('material/<int:material_id>/summary/', views.summary_view, name='summary'),
    path('material/<int:material_id>/quiz/', views.quiz_view, name='quiz'),
    path('material/<int:material_id>/flashcards/', views.flashcards_view, name='flashcards'),
    path('material/<int:material_id>/chat/', views.chat_view, name='chat'),

    # Chat AJAX endpoint
    path('material/<int:material_id>/chat/send/', views.chat_send_message, name='chat_send'),
    path('material/<int:material_id>/chat/clear/', views.clear_chat, name='clear_chat'),
]
