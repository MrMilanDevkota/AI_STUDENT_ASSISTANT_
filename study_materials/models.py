"""
Study Materials Models
Core data models for the AI Study Assistant.
"""

import os
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator


def study_material_upload_path(instance, filename):
    """Generate a user-specific upload path: media/study_materials/<user_id>/<filename>"""
    return f'study_materials/{instance.user.id}/{filename}'


class StudyMaterial(models.Model):
    """
    Represents an uploaded study document.
    Stores the file, metadata, and processing status.
    """

    STATUS_CHOICES = [
        ('pending', 'Pending Processing'),
        ('processing', 'Processing'),
        ('ready', 'Ready'),
        ('error', 'Error'),
    ]

    FILE_TYPE_CHOICES = [
        ('pdf', 'PDF'),
        ('docx', 'Word Document'),
        ('txt', 'Text File'),
    ]

    # Relationships
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='study_materials'
    )

    # File Information
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    file = models.FileField(
        upload_to=study_material_upload_path,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'docx', 'txt'])]
    )
    file_type = models.CharField(max_length=10, choices=FILE_TYPE_CHOICES)
    file_size = models.PositiveBigIntegerField(default=0)  # Size in bytes

    # Processing Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True, null=True)

    # Extracted Content
    extracted_text = models.TextField(blank=True, null=True)
    word_count = models.PositiveIntegerField(default=0)

    # Vector Store Path (FAISS index stored here)
    vector_store_path = models.CharField(max_length=500, blank=True, null=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Study Material'
        verbose_name_plural = 'Study Materials'

    def __str__(self):
        return f"{self.title} ({self.user.username})"

    @property
    def filename(self):
        """Return just the filename without the full path."""
        return os.path.basename(self.file.name)

    @property
    def file_size_display(self):
        """Return human-readable file size."""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    @property
    def is_ready(self):
        """Check if the document has been processed and is ready for AI features."""
        return self.status == 'ready'

    def delete(self, *args, **kwargs):
        """Override delete to also remove associated files."""
        # Delete the uploaded file
        if self.file and os.path.isfile(self.file.path):
            os.remove(self.file.path)
        # Delete vector store if it exists
        if self.vector_store_path and os.path.isdir(self.vector_store_path):
            import shutil
            shutil.rmtree(self.vector_store_path, ignore_errors=True)
        super().delete(*args, **kwargs)


class AIGeneratedContent(models.Model):
    """
    Stores AI-generated content for a study material.
    Caches results to avoid redundant API calls.
    """

    CONTENT_TYPE_CHOICES = [
        ('short_summary', 'Short Summary'),
        ('detailed_summary', 'Detailed Summary'),
        ('key_concepts', 'Key Concepts'),
        ('mcq_quiz', 'Multiple Choice Quiz'),
        ('short_questions', 'Short Answer Questions'),
        ('flashcards', 'Flashcards'),
    ]

    study_material = models.ForeignKey(
        StudyMaterial,
        on_delete=models.CASCADE,
        related_name='ai_content'
    )
    content_type = models.CharField(max_length=30, choices=CONTENT_TYPE_CHOICES)
    content = models.TextField()  # JSON or plain text
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['study_material', 'content_type']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_content_type_display()} for {self.study_material.title}"


class ChatMessage(models.Model):
    """
    Stores chat history for the 'Chat with Notes' feature.
    """

    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
    ]

    study_material = models.ForeignKey(
        StudyMaterial,
        on_delete=models.CASCADE,
        related_name='chat_messages'
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."
