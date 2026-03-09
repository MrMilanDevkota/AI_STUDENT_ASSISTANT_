"""
Study Materials Views
All views for the AI Study Assistant features.
Views are kept thin — all AI logic is in ai_services/.
"""

import json
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .models import StudyMaterial, AIGeneratedContent, ChatMessage
from .forms import StudyMaterialUploadForm, ChatMessageForm

logger = logging.getLogger(__name__)


# ============================================================
# Dashboard
# ============================================================

@login_required
def dashboard(request):
    """
    User dashboard showing all uploaded study materials.
    """
    materials = StudyMaterial.objects.filter(user=request.user)

    # Stats for dashboard cards
    stats = {
        'total': materials.count(),
        'ready': materials.filter(status='ready').count(),
        'processing': materials.filter(status='processing').count(),
        'error': materials.filter(status='error').count(),
    }

    return render(request, 'study_materials/dashboard.html', {
        'materials': materials,
        'stats': stats,
    })


# ============================================================
# Upload & Delete
# ============================================================

@login_required
def upload_material(request):
    """
    Handle study material file upload and trigger processing pipeline.
    """
    if request.method == 'POST':
        form = StudyMaterialUploadForm(request.POST, request.FILES)

        if form.is_valid():
            # Save the material (sets file_type, file_size)
            material = form.save(commit=False)
            material.user = request.user
            material.status = 'processing'
            material.save()

            # Run the AI processing pipeline
            try:
                from ai_services.document_processor import process_document

                extracted_text, word_count, vector_store_path = process_document(
                    file_path=material.file.path,
                    material_id=material.id,
                )

                # Update material with processing results
                material.extracted_text = extracted_text
                material.word_count = word_count
                material.vector_store_path = vector_store_path
                material.status = 'ready'
                material.save()

                messages.success(
                    request,
                    f'"{material.title}" uploaded and processed successfully! '
                    f'({word_count:,} words extracted)'
                )

            except Exception as e:
                logger.error(f"Document processing failed for material {material.id}: {e}")
                material.status = 'error'
                material.error_message = str(e)
                material.save()
                messages.error(
                    request,
                    f'File uploaded but processing failed: {str(e)}. '
                    'Please check your API key and try again.'
                )

            return redirect('dashboard')
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form = StudyMaterialUploadForm()

    return render(request, 'study_materials/upload.html', {'form': form})


@login_required
def delete_material(request, material_id):
    """
    Delete a study material and all associated files/vectors.
    """
    material = get_object_or_404(StudyMaterial, id=material_id, user=request.user)

    if request.method == 'POST':
        title = material.title
        material.delete()  # Also deletes file and vector store (see model)
        messages.success(request, f'"{title}" has been deleted.')

    return redirect('dashboard')


# ============================================================
# Summaries
# ============================================================

@login_required
def summary_view(request, material_id):
    """
    Generate and display summaries for a study material.
    Uses caching: if already generated, returns cached version.
    """
    material = get_object_or_404(StudyMaterial, id=material_id, user=request.user)

    if not material.is_ready:
        messages.warning(request, 'This material is not ready yet. Please wait for processing.')
        return redirect('dashboard')

    # Check cache first
    summaries = {}
    content_types = ['short_summary', 'detailed_summary', 'key_concepts']

    for ct in content_types:
        cached = AIGeneratedContent.objects.filter(
            study_material=material,
            content_type=ct
        ).first()
        if cached:
            summaries[ct] = cached.content

    # If we have all cached, just display
    if len(summaries) == 3 and request.method != 'POST':
        return render(request, 'study_materials/summary.html', {
            'material': material,
            'summaries': summaries,
        })

    # Generate (or regenerate on POST)
    if request.method == 'POST' or not summaries:
        try:
            from ai_services.summarizer import generate_all_summaries

            messages.info(request, 'Generating summaries... This may take a moment.')
            new_summaries = generate_all_summaries(material.extracted_text)

            # Cache results
            for ct, content in new_summaries.items():
                AIGeneratedContent.objects.update_or_create(
                    study_material=material,
                    content_type=ct,
                    defaults={'content': content}
                )

            summaries = new_summaries
            messages.success(request, 'Summaries generated successfully!')

        except Exception as e:
            logger.error(f"Summary generation error: {e}")
            messages.error(request, f'Error generating summaries: {str(e)}')

    return render(request, 'study_materials/summary.html', {
        'material': material,
        'summaries': summaries,
    })


# ============================================================
# Quiz
# ============================================================

@login_required
def quiz_view(request, material_id):
    """
    Generate and display quiz questions for a study material.
    """
    material = get_object_or_404(StudyMaterial, id=material_id, user=request.user)

    if not material.is_ready:
        messages.warning(request, 'This material is not ready yet.')
        return redirect('dashboard')

    mcq_data = None
    short_data = None

    # Check cache
    cached_mcq = AIGeneratedContent.objects.filter(
        study_material=material, content_type='mcq_quiz'
    ).first()
    cached_short = AIGeneratedContent.objects.filter(
        study_material=material, content_type='short_questions'
    ).first()

    if cached_mcq:
        mcq_data = json.loads(cached_mcq.content)
    if cached_short:
        short_data = json.loads(cached_short.content)

    if request.method == 'POST' or (not mcq_data and not short_data):
        try:
            from ai_services.quiz_generator import generate_mcq_quiz, generate_short_questions

            # Generate MCQs
            mcq_data = generate_mcq_quiz(material.extracted_text, num_questions=10)
            AIGeneratedContent.objects.update_or_create(
                study_material=material,
                content_type='mcq_quiz',
                defaults={'content': json.dumps(mcq_data)}
            )

            # Generate short questions
            short_data = generate_short_questions(material.extracted_text, num_questions=5)
            AIGeneratedContent.objects.update_or_create(
                study_material=material,
                content_type='short_questions',
                defaults={'content': json.dumps(short_data)}
            )

            messages.success(request, 'Quiz generated successfully!')

        except Exception as e:
            logger.error(f"Quiz generation error: {e}")
            messages.error(request, f'Error generating quiz: {str(e)}')

    return render(request, 'study_materials/quiz.html', {
        'material': material,
        'mcq_data': mcq_data,
        'short_data': short_data,
    })


# ============================================================
# Flashcards
# ============================================================

@login_required
def flashcards_view(request, material_id):
    """
    Generate and display flashcards for a study material.
    """
    material = get_object_or_404(StudyMaterial, id=material_id, user=request.user)

    if not material.is_ready:
        messages.warning(request, 'This material is not ready yet.')
        return redirect('dashboard')

    flashcard_data = None

    # Check cache
    cached = AIGeneratedContent.objects.filter(
        study_material=material, content_type='flashcards'
    ).first()

    if cached:
        flashcard_data = json.loads(cached.content)

    if request.method == 'POST' or not flashcard_data:
        try:
            from ai_services.flashcard_generator import generate_flashcards

            flashcard_data = generate_flashcards(material.extracted_text, num_cards=15)
            AIGeneratedContent.objects.update_or_create(
                study_material=material,
                content_type='flashcards',
                defaults={'content': json.dumps(flashcard_data)}
            )

            messages.success(request, 'Flashcards generated successfully!')

        except Exception as e:
            logger.error(f"Flashcard generation error: {e}")
            messages.error(request, f'Error generating flashcards: {str(e)}')

    return render(request, 'study_materials/flashcards.html', {
        'material': material,
        'flashcard_data': flashcard_data,
    })


# ============================================================
# Chat with Notes
# ============================================================

@login_required
def chat_view(request, material_id):
    """
    Chat interface for asking questions about study material.
    Displays chat history and form for new messages.
    """
    material = get_object_or_404(StudyMaterial, id=material_id, user=request.user)

    if not material.is_ready:
        messages.warning(request, 'This material is not ready yet.')
        return redirect('dashboard')

    chat_history = ChatMessage.objects.filter(study_material=material)
    form = ChatMessageForm()

    return render(request, 'study_materials/chat.html', {
        'material': material,
        'chat_history': chat_history,
        'form': form,
    })


@login_required
@require_POST
def chat_send_message(request, material_id):
    """
    AJAX endpoint for sending chat messages.
    Returns JSON with the AI's response.
    """
    material = get_object_or_404(StudyMaterial, id=material_id, user=request.user)

    if not material.is_ready or not material.vector_store_path:
        return JsonResponse({'error': 'Document not ready for chat.'}, status=400)

    form = ChatMessageForm(request.POST)

    if not form.is_valid():
        return JsonResponse({'error': 'Invalid message.'}, status=400)

    user_message = form.cleaned_data['message']

    # Save user message
    ChatMessage.objects.create(
        study_material=material,
        role='user',
        content=user_message
    )

    # Get chat history for context
    history = list(
        ChatMessage.objects.filter(study_material=material)
        .order_by('-created_at')[:10]
        .values('role', 'content')
    )
    history.reverse()

    try:
        from ai_services.chat_engine import answer_question

        answer = answer_question(
            question=user_message,
            vector_store_path=material.vector_store_path,
            chat_history=history,
        )

        # Save AI response
        ai_message = ChatMessage.objects.create(
            study_material=material,
            role='assistant',
            content=answer
        )

        return JsonResponse({
            'success': True,
            'answer': answer,
            'message_id': ai_message.id,
        })

    except Exception as e:
        logger.error(f"Chat error: {e}")
        error_msg = f"Sorry, I encountered an error: {str(e)}"

        ChatMessage.objects.create(
            study_material=material,
            role='assistant',
            content=error_msg
        )

        return JsonResponse({'success': True, 'answer': error_msg})


@login_required
def clear_chat(request, material_id):
    """Clear all chat history for a material."""
    material = get_object_or_404(StudyMaterial, id=material_id, user=request.user)
    ChatMessage.objects.filter(study_material=material).delete()
    messages.success(request, 'Chat history cleared.')
    return redirect('chat', material_id=material_id)
