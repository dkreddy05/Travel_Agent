"""
wanderai/ai/rag/ingestion.py
Document ingestion pipeline: read files → chunk → embed → upsert to Qdrant.
Run with: flask rag ingest
"""

import os
import uuid
from pathlib import Path
from typing import Iterator
from wanderai.observability.logger import get_logger

logger = get_logger(__name__)

KNOWLEDGE_BASE_DIR = Path(__file__).parent / "knowledge_base"
CHUNK_SIZE = 512  # chars per chunk
CHUNK_OVERLAP = 64  # overlap between chunks
COLLECTION_NAME = "wanderai_knowledge"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"


def chunk_text(
    text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP
) -> list[str]:
    """Split text into overlapping chunks."""
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        chunks.append(text[start:end].strip())
        start += size - overlap
    return [c for c in chunks if len(c) > 50]  # drop tiny chunks


def iter_documents() -> Iterator[dict]:
    """Walk the knowledge base directory and yield {text, source, category}."""
    for category_dir in KNOWLEDGE_BASE_DIR.iterdir():
        if not category_dir.is_dir():
            continue
        category = category_dir.name
        for doc_file in category_dir.glob("*.md"):
            try:
                text = doc_file.read_text(encoding="utf-8")
                yield {"text": text, "source": doc_file.name, "category": category}
            except Exception as exc:
                logger.warning("doc_read_failed", file=str(doc_file), error=str(exc))


def ingest_all(recreate_collection: bool = False) -> int:
    """
    Full ingestion pipeline. Returns number of chunks upserted.

    Args:
        recreate_collection: If True, drops and recreates the Qdrant collection.
    """
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct
    from sentence_transformers import SentenceTransformer

    client = QdrantClient(
        url=os.getenv("QDRANT_URL", "http://localhost:6333"),
        api_key=os.getenv("QDRANT_API_KEY") or None,
    )
    embedder = SentenceTransformer(EMBEDDING_MODEL)
    vector_size = embedder.get_sentence_embedding_dimension()

    # Create/recreate collection
    existing = [c.name for c in client.get_collections().collections]
    if recreate_collection and COLLECTION_NAME in existing:
        client.delete_collection(COLLECTION_NAME)
        existing.remove(COLLECTION_NAME)

    if COLLECTION_NAME not in existing:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )
        logger.info(
            "qdrant_collection_created",
            collection=COLLECTION_NAME,
            vector_size=vector_size,
        )

    total = 0
    batch: list[PointStruct] = []

    for doc in iter_documents():
        chunks = chunk_text(doc["text"])
        for chunk in chunks:
            vector = embedder.encode(chunk, show_progress_bar=False).tolist()
            batch.append(
                PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vector,
                    payload={
                        "text": chunk,
                        "source": doc["source"],
                        "category": doc["category"],
                    },
                )
            )

            if len(batch) >= 100:
                client.upsert(collection_name=COLLECTION_NAME, points=batch)
                total += len(batch)
                logger.info("rag_batch_upserted", count=total)
                batch = []

    if batch:
        client.upsert(collection_name=COLLECTION_NAME, points=batch)
        total += len(batch)

    logger.info("rag_ingestion_complete", total_chunks=total)
    return total
