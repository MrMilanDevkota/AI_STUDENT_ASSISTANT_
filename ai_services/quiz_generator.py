"""
Quiz Generator Service
Generates MCQ and short-answer quizzes from study materials.

Output is structured JSON for easy rendering in templates.
"""

import json
import logging
import re
from typing import Dict, List

logger = logging.getLogger(__name__)


def _parse_json_response(response: str) -> dict:
    """
    Safely parse JSON from LLM response.
    Handles cases where the LLM wraps JSON in markdown code blocks.
    """
    # Remove markdown code blocks if present
    response = response.strip()
    response = re.sub(r'^```(?:json)?\s*', '', response)
    response = re.sub(r'\s*```$', '', response)

    try:
        return json.loads(response)
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error: {e}\nResponse: {response[:500]}")
        raise ValueError(f"Failed to parse AI response as JSON: {e}")


def generate_mcq_quiz(text: str, num_questions: int = 10) -> Dict:
    """
    Generate multiple choice questions from study material.

    Args:
        text: Study material text.
        num_questions: Number of MCQs to generate (default: 10).

    Returns:
        Dictionary with 'questions' list. Each question has:
        - question: str
        - options: dict (A, B, C, D)
        - correct_answer: str (A/B/C/D)
        - explanation: str
    """
    try:
        from langchain.prompts import PromptTemplate
        from langchain_core.output_parsers import StrOutputParser
        from .llm import get_llm

        llm = get_llm(temperature=0.3, max_tokens=3000)

        prompt = PromptTemplate(
            input_variables=["text", "num_questions"],
            template="""You are an expert educator creating a quiz to test student understanding.

Read the following study material and generate {num_questions} Multiple Choice Questions (MCQs).

IMPORTANT: Return ONLY valid JSON, no other text.

Required JSON format:
{{
  "questions": [
    {{
      "id": 1,
      "question": "Question text here?",
      "options": {{
        "A": "First option",
        "B": "Second option",
        "C": "Third option",
        "D": "Fourth option"
      }},
      "correct_answer": "A",
      "explanation": "Brief explanation of why A is correct"
    }}
  ]
}}

Guidelines:
- Questions should test understanding, not just memorization
- All 4 options should be plausible (avoid obvious wrong answers)
- Cover different parts of the material
- Vary difficulty (easy, medium, hard)
- correct_answer must be exactly "A", "B", "C", or "D"

Study Material:
{text}

JSON RESPONSE:"""
        )

        chain = prompt | llm | StrOutputParser()

        # Use a reasonable text sample
        text_sample = text[:10000] if len(text) > 10000 else text

        result = chain.invoke({
            "text": text_sample,
            "num_questions": num_questions
        })

        quiz_data = _parse_json_response(result)

        # Validate structure
        if 'questions' not in quiz_data:
            raise ValueError("AI response missing 'questions' field")

        logger.info(f"Generated {len(quiz_data['questions'])} MCQs")
        return quiz_data

    except Exception as e:
        logger.error(f"MCQ generation failed: {e}")
        raise


def generate_short_questions(text: str, num_questions: int = 5) -> Dict:
    """
    Generate short answer questions from study material.

    Args:
        text: Study material text.
        num_questions: Number of questions (default: 5).

    Returns:
        Dictionary with 'questions' list. Each question has:
        - question: str
        - answer: str (model answer)
        - key_points: list of strings
    """
    try:
        from langchain.prompts import PromptTemplate
        from langchain_core.output_parsers import StrOutputParser
        from .llm import get_llm

        llm = get_llm(temperature=0.3, max_tokens=2000)

        prompt = PromptTemplate(
            input_variables=["text", "num_questions"],
            template="""You are an expert educator creating a short-answer quiz to test deep understanding.

Read the following study material and generate {num_questions} short-answer questions.

IMPORTANT: Return ONLY valid JSON, no other text.

Required JSON format:
{{
  "questions": [
    {{
      "id": 1,
      "question": "Question requiring a short paragraph answer?",
      "model_answer": "A complete model answer (2-4 sentences)",
      "key_points": [
        "Key point 1 that must be mentioned",
        "Key point 2 that must be mentioned"
      ]
    }}
  ]
}}

Guidelines:
- Ask "why", "how", "explain", "describe" type questions
- Require critical thinking, not just recall
- Model answers should be 2-4 sentences
- Include 2-3 key points per question

Study Material:
{text}

JSON RESPONSE:"""
        )

        chain = prompt | llm | StrOutputParser()

        text_sample = text[:10000] if len(text) > 10000 else text

        result = chain.invoke({
            "text": text_sample,
            "num_questions": num_questions
        })

        quiz_data = _parse_json_response(result)

        if 'questions' not in quiz_data:
            raise ValueError("AI response missing 'questions' field")

        logger.info(f"Generated {len(quiz_data['questions'])} short questions")
        return quiz_data

    except Exception as e:
        logger.error(f"Short question generation failed: {e}")
        raise
