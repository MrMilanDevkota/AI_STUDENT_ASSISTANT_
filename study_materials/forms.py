"""
Study Materials Forms
Handles file upload validation and study material creation.
"""

import os
from django import forms
from django.conf import settings
from .models import StudyMaterial


class StudyMaterialUploadForm(forms.ModelForm):
    """
    Form for uploading study materials with validation.
    """

    class Meta:
        model = StudyMaterial
        fields = ['title', 'description', 'file']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Chapter 5 - Cell Biology'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Brief description of the material (optional)',
                'rows': 3
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.docx,.txt'
            }),
        }

    def clean_file(self):
        """
        Validate uploaded file:
        - Check file extension (PDF, DOCX, TXT only)
        - Check file size (max 10MB)
        """
        file = self.cleaned_data.get('file')

        if not file:
            raise forms.ValidationError("Please select a file to upload.")

        # Check file extension
        ext = os.path.splitext(file.name)[1].lower()
        allowed_extensions = getattr(settings, 'ALLOWED_UPLOAD_EXTENSIONS', ['.pdf', '.docx', '.txt'])

        if ext not in allowed_extensions:
            raise forms.ValidationError(
                f"File type '{ext}' is not supported. "
                f"Please upload a PDF, DOCX, or TXT file."
            )

        # Check file size (default: 10MB)
        max_size = getattr(settings, 'MAX_UPLOAD_SIZE', 10 * 1024 * 1024)
        if file.size > max_size:
            max_mb = max_size / (1024 * 1024)
            raise forms.ValidationError(
                f"File size ({file.size / 1024 / 1024:.1f}MB) exceeds "
                f"the maximum allowed size ({max_mb:.0f}MB)."
            )

        return file

    def save(self, commit=True):
        """
        Save the form and auto-detect file type from extension.
        """
        instance = super().save(commit=False)

        # Determine file type from extension
        ext = os.path.splitext(instance.file.name)[1].lower()
        file_type_map = {'.pdf': 'pdf', '.docx': 'docx', '.txt': 'txt'}
        instance.file_type = file_type_map.get(ext, 'txt')
        instance.file_size = instance.file.size

        if commit:
            instance.save()
        return instance


class ChatMessageForm(forms.Form):
    """
    Simple form for submitting chat messages.
    """
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Ask a question about your study material...',
            'rows': 2,
            'id': 'chat-input'
        }),
        max_length=1000,
        strip=True,
    )
