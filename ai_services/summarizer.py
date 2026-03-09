"""
Summarizer Service
Generates different types of summaries from study material text.

Features:
- Short summary (2-3 paragraphs, key points)
- Detailed summary (comprehensive, well-structured)
- Key concepts extraction (glossary-style definitions)
"""

import logging
from typing import Dict

logger = logging.getLogger(__name__)


def _get_text_sample(text: str, max_chars: int = 12000) -> str:
    """
    Return a text sample within the token limit.
    For very long documents, uses beginning + middle + end for better coverage.
    """
    if len(text) <= max_chars:
        return text

    # Take beginning, middle, and end sections
    third = max_chars // 3
    beginning = text[:third]
    middle_start = len(text) // 2 - third // 2
    middle = text[middle_start:middle_start + third]
    end = text[-third:]

    return f"{beginning}\n\n[...middle section...]\n\n{middle}\n\n[...later section...]\n\n{end}"


def generate_short_summary(text: str) -> str:
    """
    Generate a concise summary (2-3 paragraphs).

    Args:
        text: Full extracted document text.

    Returns:
        Short summary string.
    """
    try:
        from langchain.prompts import PromptTemplate
        from langchain_core.output_parsers import StrOutputParser
        from .llm import get_llm

        llm = get_llm(temperature=0.2)

        prompt = PromptTemplate(
            input_variables=["text"],
            template="""You are an expert academic summarizer helping students understand study materials.

Read the following study material and create a CONCISE SUMMARY in 2-3 paragraphs.

Requirements:
- Cover the main topic and core ideas
- Use clear, student-friendly language
- Highlight the most important points
- Keep it under 300 words

Study Material:
{text}

CONCISE SUMMARY:"""
        )

        chain = prompt | llm | StrOutputParser()
        result = chain.invoke({"text": _get_text_sample(text)})

        return result.strip()

    except Exception as e:
        logger.error(f"Short summary generation failed: {e}")
        raise


def generate_detailed_summary(text: str) -> str:
    """
    Generate a comprehensive, well-structured detailed summary.

    Args:
        text: Full extracted document text.

    Returns:
        Detailed summary string with sections.
    """
    try:
        from langchain.prompts import PromptTemplate
        from langchain_core.output_parsers import StrOutputParser
        from .llm import get_llm

        llm = get_llm(temperature=0.2, max_tokens=3000)

        prompt = PromptTemplate(
            input_variables=["text"],
            template="""You are an expert academic summarizer helping students master their study materials.

Read the following study material and create a DETAILED, STRUCTURED SUMMARY.

Requirements:
- Use clear headings and subheadings
- Cover all major topics and subtopics
- Explain key terms and concepts
- Include important facts, dates, names if present
- Use bullet points where appropriate
- Target length: 500-800 words

Study Material:
{text}

DETAILED SUMMARY:"""
        )

        chain = prompt | llm | StrOutputParser()
        result = chain.invoke({"text": _get_text_sample(text, max_chars=14000)})

        return result.strip()

    except Exception as e:
        logger.error(f"Detailed summary generation failed: {e}")
        raise


def generate_key_concepts(text: str) -> str:
    """
    Extract and define key concepts from the document.

    Args:
        text: Full extracted document text.

    Returns:
        Formatted list of key concepts with definitions.
    """
    try:
        from langchain.prompts import PromptTemplate
        from langchain_core.output_parsers import StrOutputParser
        from .llm import get_llm

        llm = get_llm(temperature=0.1)

        prompt = PromptTemplate(
            input_variables=["text"],
            template="""You are an expert educator helping students identify the most important concepts.

Read the following study material and extract the KEY CONCEPTS.

Requirements:
- List 10-15 most important terms, concepts, or ideas
- For each concept: provide a clear, concise definition (1-2 sentences)
- Format: **Concept Name**: Definition
- Order from most fundamental to most advanced
- Use simple language appropriate for students

Study Material:
{text}

KEY CONCEPTS:"""
        )

        chain = prompt | llm | StrOutputParser()
        result = chain.invoke({"text": _get_text_sample(text)})

        return result.strip()

    except Exception as e:
        logger.error(f"Key concepts generation failed: {e}")
        raise


def generate_all_summaries(text: str) -> Dict[str, str]:
    """
    Generate all summary types for a document.

    Args:
        text: Full extracted document text.

    Returns:
        Dictionary with 'short', 'detailed', 'key_concepts' keys.
    """
    results = {}

    try:
        results['short_summary'] = generate_short_summary(text)
    except Exception as e:
        results['short_summary'] = f"Error generating short summary: {str(e)}"

    try:
        results['detailed_summary'] = generate_detailed_summary(text)
    except Exception as e:
        results['detailed_summary'] = f"Error generating detailed summary: {str(e)}"

    try:
        results['key_concepts'] = generate_key_concepts(text)
    except Exception as e:
        results['key_concepts'] = f"Error generating key concepts: {str(e)}"

    return results
