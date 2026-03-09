"""
LLM Configuration Service
Central place to initialize and configure the Google Gemini LLM.
All AI services import the LLM from here to ensure consistency.
"""

import logging
from django.conf import settings

logger = logging.getLogger(__name__)

# Default model settings
DEFAULT_MODEL = "gemini-2.5-flash-lite"   # Fast, free-tier friendly
FALLBACK_MODEL = "gemini-1.5-flash"    # Higher quality, lower rate limits


def get_llm(temperature: float = 0.3, max_tokens: int = 2048):
    """
    Initialize and return a Google Gemini LLM instance.

    Args:
        temperature: Controls randomness (0=deterministic, 1=creative).
                    Lower for factual tasks, higher for creative ones.
        max_tokens: Maximum tokens in the response.

    Returns:
        A LangChain-compatible LLM object.

    Raises:
        ValueError: If GOOGLE_API_KEY is not configured.
        ImportError: If required packages are not installed.
    """
    api_key = getattr(settings, 'GOOGLE_API_KEY', '')

    if not api_key:
        raise ValueError(
            "GOOGLE_API_KEY is not set. "
            "Get your free key at: https://aistudio.google.com/app/apikey "
            "and add it to your .env file."
        )

    try:
        from langchain_google_genai import ChatGoogleGenerativeAI

        llm = ChatGoogleGenerativeAI(
            model=DEFAULT_MODEL,
            google_api_key=api_key,
            temperature=temperature,
            max_output_tokens=max_tokens,
            # Safety settings - less restrictive for educational content
            convert_system_message_to_human=True,
        )

        logger.info(f"LLM initialized: {DEFAULT_MODEL} (temp={temperature})")
        return llm

    except ImportError:
        raise ImportError(
            "langchain-google-genai not installed. "
            "Run: pip install langchain-google-genai"
        )
    except Exception as e:
        logger.error(f"LLM initialization failed: {e}")
        raise
