"""
Text Splitter Service
Splits extracted document text into overlapping chunks for vector embedding.
Uses LangChain's RecursiveCharacterTextSplitter for intelligent splitting.
"""

import logging
from typing import List

logger = logging.getLogger(__name__)

# Optimal chunk settings for study materials
DEFAULT_CHUNK_SIZE = 1000       # Characters per chunk
DEFAULT_CHUNK_OVERLAP = 200     # Overlap to preserve context at boundaries


def split_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP
) -> List[str]:
    """
    Split a large text into overlapping chunks.

    Uses RecursiveCharacterTextSplitter which tries to split on:
    1. Paragraph breaks (\\n\\n)
    2. Line breaks (\\n)
    3. Sentences (. ? !)
    4. Words (spaces)
    5. Characters (last resort)

    Args:
        text: The full extracted document text.
        chunk_size: Maximum characters per chunk.
        chunk_overlap: How many characters overlap between consecutive chunks.

    Returns:
        List of text chunk strings.
    """
    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            # Try these separators in order
            separators=["\n\n", "\n", ". ", "? ", "! ", " ", ""],
        )

        chunks = splitter.split_text(text)

        # Filter out empty or whitespace-only chunks
        chunks = [chunk.strip() for chunk in chunks if chunk.strip()]

        logger.info(f"Split text into {len(chunks)} chunks "
                    f"(chunk_size={chunk_size}, overlap={chunk_overlap})")

        return chunks

    except ImportError:
        raise ImportError("langchain-text-splitters not installed. Run: pip install langchain-text-splitters")
    except Exception as e:
        logger.error(f"Text splitting error: {e}")
        raise
