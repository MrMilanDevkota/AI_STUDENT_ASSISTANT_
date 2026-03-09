"""
Vector Store Service
Creates, saves, and loads FAISS vector stores for document retrieval.

FAISS (Facebook AI Similarity Search) allows us to:
1. Store text chunk embeddings
2. Quickly find the most relevant chunks for any query

Each StudyMaterial gets its own FAISS index stored on disk.
"""

import os
import logging
from typing import List, Optional
from pathlib import Path

from django.conf import settings

logger = logging.getLogger(__name__)


def get_vector_store_path(material_id: int) -> str:
    """
    Return the filesystem path where a material's FAISS index is stored.
    Creates the directory if it doesn't exist.
    """
    base_dir = getattr(settings, 'VECTOR_STORE_BASE_DIR', Path(settings.MEDIA_ROOT) / 'vector_stores')
    store_path = os.path.join(str(base_dir), f'material_{material_id}')
    os.makedirs(store_path, exist_ok=True)
    return store_path


def create_vector_store(chunks: List[str], material_id: int) -> str:
    """
    Create a FAISS vector store from text chunks and save it to disk.

    Steps:
    1. Get embeddings model
    2. Embed all chunks into vectors
    3. Build FAISS index
    4. Save index to disk for later retrieval

    Args:
        chunks: List of text chunks from the document.
        material_id: Database ID of the StudyMaterial (used for save path).

    Returns:
        Path to the saved FAISS index directory.
    """
    try:
        from langchain_community.vectorstores import FAISS
        from .embeddings import get_embeddings

        if not chunks:
            raise ValueError("No text chunks provided to create vector store.")

        # Get embedding model
        embeddings = get_embeddings()

        logger.info(f"Creating vector store for material {material_id} "
                    f"with {len(chunks)} chunks...")

        # Create FAISS index from chunks
        # This embeds all chunks and builds the search index
        vector_store = FAISS.from_texts(
            texts=chunks,
            embedding=embeddings,
        )

        # Save to disk
        save_path = get_vector_store_path(material_id)
        vector_store.save_local(save_path)

        logger.info(f"Vector store saved to: {save_path}")
        return save_path

    except ImportError as e:
        raise ImportError(f"Required package not installed: {e}")
    except Exception as e:
        logger.error(f"Vector store creation failed for material {material_id}: {e}")
        raise


def load_vector_store(vector_store_path: str):
    """
    Load a saved FAISS vector store from disk.

    Args:
        vector_store_path: Path to the saved FAISS index directory.

    Returns:
        Loaded FAISS vector store object.

    Raises:
        FileNotFoundError: If the index doesn't exist at the path.
    """
    try:
        from langchain_community.vectorstores import FAISS
        from .embeddings import get_embeddings

        if not os.path.exists(vector_store_path):
            raise FileNotFoundError(
                f"Vector store not found at: {vector_store_path}. "
                "Please reprocess the document."
            )

        embeddings = get_embeddings()

        # allow_dangerous_deserialization=True required for FAISS pickle loading
        vector_store = FAISS.load_local(
            vector_store_path,
            embeddings,
            allow_dangerous_deserialization=True,
        )

        logger.info(f"Vector store loaded from: {vector_store_path}")
        return vector_store

    except Exception as e:
        logger.error(f"Failed to load vector store from {vector_store_path}: {e}")
        raise


def retrieve_relevant_chunks(
    vector_store_path: str,
    query: str,
    k: int = 5
) -> List[str]:
    """
    Retrieve the k most relevant text chunks for a given query.

    Uses cosine similarity between query embedding and chunk embeddings.

    Args:
        vector_store_path: Path to FAISS index.
        query: The user's question or topic.
        k: Number of chunks to retrieve.

    Returns:
        List of relevant text chunks (strings).
    """
    try:
        vector_store = load_vector_store(vector_store_path)

        # Similarity search returns Document objects
        docs = vector_store.similarity_search(query, k=k)

        # Extract just the text content
        chunks = [doc.page_content for doc in docs]

        logger.info(f"Retrieved {len(chunks)} chunks for query: '{query[:50]}...'")
        return chunks

    except Exception as e:
        logger.error(f"Chunk retrieval failed: {e}")
        raise
