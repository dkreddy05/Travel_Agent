"""Tests for RAG modules — retriever and ingestion."""

class TestRetriever:
    def test_retrieve_returns_empty_on_error(self, monkeypatch):
        from wanderai.ai.rag.retriever import retrieve

        def failing_embedder():
            raise Exception("Model not loaded")

        monkeypatch.setattr("wanderai.ai.rag.retriever._get_embedder", failing_embedder)

        result = retrieve("Paris")
        assert result == []

    def test_retrieve_empty_query(self, monkeypatch):
        from wanderai.ai.rag.retriever import retrieve

        result = retrieve("")
        assert result == []


class TestIngestion:
    def test_chunk_text(self):
        from wanderai.ai.rag.ingestion import chunk_text

        text = "A" * 1000
        chunks = chunk_text(text, size=200, overlap=20)
        assert len(chunks) > 0
        assert all(len(c) > 50 for c in chunks)

    def test_chunk_text_small(self):
        from wanderai.ai.rag.ingestion import chunk_text

        text = "Short text."
        chunks = chunk_text(text, size=512, overlap=64)
        assert len(chunks) == 0  # < 50 chars dropped

    def test_chunk_text_exact_size(self):
        from wanderai.ai.rag.ingestion import chunk_text

        text = "A" * 512
        chunks = chunk_text(text, size=512, overlap=64)
        # With size=512 and overlap=64, start goes 0, 448. Both produce chunks >= 50 chars
        assert len(chunks) >= 1
