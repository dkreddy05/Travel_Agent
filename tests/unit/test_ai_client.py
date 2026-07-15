"""Tests for AIClient with mocked external dependencies."""


class TestAIClient:
    def test_init_with_defaults(self):
        from wanderai.ai.client import AIClient

        client = AIClient({"AI_PRIMARY_MODEL": "test-model"})
        assert client.primary_model == "test-model"
        assert client.fallback_model == ""
        assert client.max_retries == 3
        assert client.timeout == 60
        assert client._cache is None

    def test_set_cache(self):
        from wanderai.ai.client import AIClient

        client = AIClient({})
        client.set_cache("fake-cache")
        assert client._cache == "fake-cache"

    def test_complete_with_cache_hit(self, monkeypatch):
        from wanderai.ai.client import AIClient

        cached_result = {
            "text": "Cached response",
            "model": "test-model",
            "tokens_used": 10,
            "latency_ms": 5,
            "cached": True,
        }

        class FakeCache:
            def get(self, key):
                return cached_result

            def set(self, key, value, timeout):
                pass

        client = AIClient({"AI_PRIMARY_MODEL": "test-model"})
        client.set_cache(FakeCache())

        result = client.complete(
            messages=[{"role": "user", "content": "Hello"}], use_cache=True
        )
        assert result["cached"] is True
        assert result["text"] == "Cached response"

    def test_complete_successful_call(self, monkeypatch):
        import wanderai.ai.client as client_mod

        def mock_watsonx(messages, model_id, **params):
            return "Hello, how can I help you?"

        monkeypatch.setattr(
            client_mod, "_get_watsonx_messages_completion", mock_watsonx
        )

        client = client_mod.AIClient({"AI_PRIMARY_MODEL": "test-model"})
        result = client.complete(
            messages=[{"role": "user", "content": "Hello"}],
            use_cache=False,
        )
        assert result["cached"] is False
        assert "Hello" in result["text"]
        assert result["model"] == "test-model"

    def test_complete_with_retry_and_fallback(self, monkeypatch):
        import wanderai.ai.client as client_mod

        call_count = [0]

        def mock_watsonx_primary_fails(messages, model_id, **params):
            call_count[0] += 1
            if model_id == "primary":
                raise ConnectionError("API unavailable")
            return "Fallback response"

        monkeypatch.setattr(
            client_mod, "_get_watsonx_messages_completion", mock_watsonx_primary_fails
        )

        client = client_mod.AIClient(
            {
                "AI_PRIMARY_MODEL": "primary",
                "AI_FALLBACK_MODEL": "fallback",
                "AI_MAX_RETRIES": 2,
            }
        )

        with monkeypatch.context() as m:
            m.setattr(client_mod.logger, "warning", lambda *a, **kw: None)
            m.setattr(client_mod.logger, "error", lambda *a, **kw: None)
            m.setattr(client_mod.logger, "info", lambda *a, **kw: None)
            result = client.complete(
                messages=[{"role": "user", "content": "Hello"}],
                use_cache=False,
            )

        assert "Fallback" in result["text"]
        assert result["model"] == "fallback"

    def test_complete_all_retries_exhausted_no_fallback(self, monkeypatch):
        import wanderai.ai.client as client_mod

        def always_fails(messages, model_id, **params):
            raise ConnectionError("Always fails")

        monkeypatch.setattr(
            client_mod, "_get_watsonx_messages_completion", always_fails
        )

        client = client_mod.AIClient(
            {
                "AI_PRIMARY_MODEL": "primary",
                "AI_FALLBACK_MODEL": "",
                "AI_MAX_RETRIES": 2,
            }
        )

        with monkeypatch.context() as m:
            m.setattr(client_mod.logger, "warning", lambda *a, **kw: None)
            m.setattr(client_mod.logger, "error", lambda *a, **kw: None)
            m.setattr(client_mod.logger, "info", lambda *a, **kw: None)
            result = client.complete(
                messages=[{"role": "user", "content": "Hello"}],
                use_cache=False,
            )

        assert result["is_error"] is True
        assert "error" in result["text"].lower()

    def test_complete_caches_successful_result(self, monkeypatch):
        import wanderai.ai.client as client_mod

        cache_store = {}

        class FakeCache:
            def get(self, key):
                return cache_store.get(key)

            def set(self, key, value, timeout):
                cache_store[key] = value

        def mock_watsonx(messages, model_id, **params):
            return "Success"

        monkeypatch.setattr(
            client_mod, "_get_watsonx_messages_completion", mock_watsonx
        )

        client = client_mod.AIClient({"AI_PRIMARY_MODEL": "test-model"})
        client.set_cache(FakeCache())

        result = client.complete(
            messages=[{"role": "user", "content": "Cache me"}],
            use_cache=True,
        )
        assert result["cached"] is False
        assert len(cache_store) > 0

    def test_complete_uses_model_param(self, monkeypatch):
        import wanderai.ai.client as client_mod

        used_model = [None]

        def mock_watsonx(messages, model_id, **params):
            used_model[0] = model_id
            return "OK"

        monkeypatch.setattr(
            client_mod, "_get_watsonx_messages_completion", mock_watsonx
        )

        client = client_mod.AIClient({"AI_PRIMARY_MODEL": "default-model"})
        client.complete(
            messages=[{"role": "user", "content": "Hi"}],
            model="custom-model",
            use_cache=False,
        )
        assert used_model[0] == "custom-model"
