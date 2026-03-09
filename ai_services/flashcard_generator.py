"""
Flashcard Generator Service
Creates question/answer flashcards from study materials.
Ideal for spaced repetition and active recall practice.
"""

import json
import logging
import re
from typing import Dict, List

logger = logging.getLogger(__name__)


def generate_flashcards(text: str, num_cards: int = 15) -> Dict:
    """
    Generate question/answer flashcards from study material.

    Args:
        text: Study material text.
        num_cards: Number of flashcards to generate (default: 15).

    Returns:
        Dictionary with 'flashcards' list. Each card has:
        - id: int
        - front: str (question/term)
        - back: str (answer/definition)
        - category: str (optional topic tag)
    """
    try:
        from langchain.prompts import PromptTemplate
        from langchain_core.output_parsers import StrOutputParser
        from .llm import get_llm

        llm = get_llm(temperature=0.2, max_tokens=3000)

        prompt = PromptTemplate(
            input_variables=["text", "num_cards"],
            template="""You are an expert educator creating flashcards for student review.

Read the following study material and create {num_cards} flashcards.

Flashcards should cover:
- Key terms and their definitions
- Important concepts and explanations  
- Cause and effect relationships
- Important facts, dates, or names
- Process steps or procedures

IMPORTANT: Return ONLY valid JSON, no other text.

Required JSON format:
{{
  "flashcards": [
    {{
      "id": 1,
      "front": "Question or term on front of card",
      "back": "Answer or definition on back of card (2-3 sentences max)",
      "category": "Topic category"
    }}
  ]
}}

Guidelines:
- Front side: concise question or key term (under 20 words)
- Back side: clear, complete answer (2-3 sentences)
- Category: group related cards (e.g., "Definitions", "Concepts", "Facts")
- Mix different types: definitions, questions, fill-in-the-blank style
- Make cards specific and testable

Study Material:
{text}

JSON RESPONSE:"""
        )

        chain = prompt | llm | StrOutputParser()

        text_sample = text[:12000] if len(text) > 12000 else text

        result = chain.invoke({
            "text": text_sample,
            "num_cards": num_cards
        })

        # Clean and parse JSON
        result = result.strip()
        result = re.sub(r'^```(?:json)?\s*', '', result)
        result = re.sub(r'\s*```$', '', result)

        flashcard_data = json.loads(result)

        if 'flashcards' not in flashcard_data:
            raise ValueError("AI response missing 'flashcards' field")

        logger.info(f"Generated {len(flashcard_data['flashcards'])} flashcards")
        return flashcard_data

    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error in flashcard generation: {e}")
        raise ValueError(f"Failed to parse flashcard response: {e}")
    except Exception as e:
        logger.error(f"Flashcard generation failed: {e}")
        raise
