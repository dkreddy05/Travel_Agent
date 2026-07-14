"""
wanderai/ai/rag/retriever.py
Qdrant-based semantic retrieval for the RAG pipeline.
"""

from wanderai.observability.logger import get_logger

logger = get_logger(__name__)

_client = None
_embedder = None
COLLECTION_NAME = "wanderai_knowledge"


def _get_client():
    global _client
    if _client is None:
        from qdrant_client import QdrantClient
        import os

        _client = QdrantClient(
            url=os.getenv("QDRANT_URL", "http://localhost:6333"),
            api_key=os.getenv("QDRANT_API_KEY") or None,
        )
    return _client


def _get_embedder():
    global _embedder
    if _embedder is None:
        from sentence_transformers import SentenceTransformer

        _embedder = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedder


def retrieve(query: str, top_k: int = 5, score_threshold: float = 0.4) -> list[dict]:
    """
    Embed the query and retrieve the top-k most similar knowledge chunks.

    Args:
        query: The search query (user message + destination)
        top_k: Number of results to return
        score_threshold: Minimum similarity score (0–1)

    Returns:
        List of {text, score, metadata} dicts
    """
    try:
        embedder = _get_embedder()
        client = _get_client()

        # Generate query embedding
        query_vector = embedder.encode(query, show_progress_bar=False).tolist()

        # Search Qdrant
        results = client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_vector,
            limit=top_k,
            score_threshold=score_threshold,
        )

        chunks = [
            {
                "text": r.payload.get("text", ""),
                "source": r.payload.get("source", ""),
                "category": r.payload.get("category", ""),
                "score": r.score,
            }
            for r in results
        ]

        logger.debug("rag_retrieved", query_preview=query[:60], count=len(chunks))
        return chunks

    except Exception as exc:
        logger.debug("rag_retrieval_failed", reason=str(exc))
        return []
