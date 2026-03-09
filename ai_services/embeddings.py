"""
Embeddings Service
Uses Google's generativeai SDK directly to avoid LangChain wrapper API version issues.
Falls back to HuggingFace sentence-transformers if Google API unavailable.
"""

import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class GoogleEmbeddingsWrapper:
    """
    Custom LangChain-compatible embeddings wrapper using google-generativeai SDK directly.
    This bypasses the v1beta API version issue in langchain-google-genai.
    """

    def __init__(self, api_key: str, model: str = "models/text-embedding-004"):
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        self.model = model
        self.genai = genai

    def embed_documents(self, texts: list) -> list:
        """Embed a list of document chunks."""
        embeddings = []
        for text in texts:
            result = self.genai.embed_content(
                model=self.model,
                content=text,
                task_type="retrieval_document",
            )
            embeddings.append(result['embedding'])
        return embeddings

    def embed_query(self, text: str) -> list:
        """Embed a single query string."""
        result = self.genai.embed_content(
            model=self.model,
            content=text,
            task_type="retrieval_query",
        )
        return result['embedding']


def get_embeddings():
    """Return an embeddings model compatible with FAISS."""
    google_api_key = getattr(settings, 'GOOGLE_API_KEY', '')
    if google_api_key:
        return _get_google_embeddings(google_api_key)
    else:
        logger.warning("GOOGLE_API_KEY not set. Using HuggingFace embeddings.")
        return _get_huggingface_embeddings()


def _get_google_embeddings(api_key: str):
    """Initialize Google embeddings using the SDK directly."""
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)

        # Quick connectivity test
        test = genai.embed_content(
            model="models/text-embedding-004",
            content="test",
            task_type="retrieval_query",
        )
        assert 'embedding' in test

        logger.info("Using Google Generative AI embeddings (direct SDK).")
        return GoogleEmbeddingsWrapper(api_key=api_key)

    except Exception as e:
        logger.error(f"Google embeddings failed: {e}")
        logger.warning("Falling back to HuggingFace embeddings...")
        return _get_huggingface_embeddings()


def _get_huggingface_embeddings():
    """Local HuggingFace embeddings fallback (~90MB download on first use)."""
    try:
        from langchain_community.embeddings import HuggingFaceEmbeddings
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True},
        )
        logger.info("Using HuggingFace local embeddings (all-MiniLM-L6-v2).")
        return embeddings
    except ImportError:
        raise ImportError("Run: pip install sentence-transformers")
    except Exception as e:
        logger.error(f"HuggingFace embeddings failed: {e}")
        raise