"""
Document Processor Service
Orchestrates the full document ingestion pipeline:
load → split → embed → store in vector DB

This is called when a user uploads a new study material.
"""

import logging
from typing import Tuple

logger = logging.getLogger(__name__)


def process_document(file_path: str, material_id: int) -> Tuple[str, int, str]:
    """
    Full document processing pipeline.

    Steps:
    1. Load and extract text from file (PDF/DOCX/TXT)
    2. Split text into overlapping chunks
    3. Create embeddings and store in FAISS vector database

    Args:
        file_path: Absolute path to the uploaded file.
        material_id: Database ID of the StudyMaterial record.

    Returns:
        Tuple of (extracted_text, word_count, vector_store_path)

    Raises:
        Exception: If any step in the pipeline fails.
    """
    from .document_loader import load_document
    from .text_splitter import split_text
    from .vector_store import create_vector_store

    # Step 1: Extract text
    logger.info(f"[Processing] Step 1/3: Extracting text from {file_path}")
    extracted_text = load_document(file_path)

    word_count = len(extracted_text.split())
    logger.info(f"[Processing] Extracted {word_count} words")

    # Step 2: Split into chunks
    logger.info(f"[Processing] Step 2/3: Splitting into chunks")
    chunks = split_text(extracted_text)
    logger.info(f"[Processing] Created {len(chunks)} chunks")

    # Step 3: Create vector store
    logger.info(f"[Processing] Step 3/3: Building vector store")
    vector_store_path = create_vector_store(chunks, material_id)

    logger.info(f"[Processing] ✓ Complete for material {material_id}")
    return extracted_text, word_count, vector_store_path
