"""Tests for weather and currency tools."""

class TestWeatherTool:
    def test_get_weather_no_api_key(self, monkeypatch):
        import os
        monkeypatch.setattr(os, "getenv", lambda k, d="": "" if k == "OPENWEATHER_API_KEY" else d)

        from wanderai.ai.tools.weather_tool import get_weather

        result = get_weather("Paris", "June")
        assert "error" in result
        assert "not configured" in result["error"]

    def test_get_weather_cache_hit(self, monkeypatch):
        class FakeCache:
            def get(self, key):
                return {"temperature_c": 25, "cached": True}

            def set(self, key, value, timeout):
                pass

        from wanderai.ai.tools.weather_tool import get_weather
        import os
        monkeypatch.setattr(os, "getenv", lambda k, d="": "fake-key" if k == "OPENWEATHER_API_KEY" else d)

        result = get_weather("London", "July", cache=FakeCache())
        assert result["cached"] is True
        assert result["temperature_c"] == 25

    def test_get_weather_api_error(self, monkeypatch):
        import os
        monkeypatch.setattr(os, "getenv", lambda k, d="": "fake-key" if k == "OPENWEATHER_API_KEY" else d)

        def mock_get(url, params, timeout):
            raise Exception("Connection error")

        monkeypatch.setattr("requests.get", mock_get)

        from wanderai.ai.tools.weather_tool import get_weather

        with monkeypatch.context() as m:
            m.setattr("wanderai.ai.tools.weather_tool.logger", type("FakeLogger", (), {"warning": lambda *a, **kw: None, "debug": lambda *a, **kw: None})())
            result = get_weather("Paris", "June")

        assert "error" in result
        assert result["fallback"] is True


class TestCurrencyTool:
    def test_get_exchange_rate_cache_hit(self, monkeypatch):
        class FakeCache:
            def get(self, key):
                return {"rate": 0.85, "cached": True}

            def set(self, key, value, timeout):
                pass

        from wanderai.ai.tools.currency_tool import get_exchange_rate

        result = get_exchange_rate("USD", "EUR", cache=FakeCache())
        assert result["cached"] is True
        assert result["rate"] == 0.85

    def test_get_exchange_rate_api_error(self, monkeypatch):
        def mock_get(url, params, timeout):
            raise Exception("API error")

        monkeypatch.setattr("requests.get", mock_get)

        from wanderai.ai.tools.currency_tool import get_exchange_rate

        with monkeypatch.context() as m:
            m.setattr("wanderai.ai.tools.currency_tool.logger", type("FakeLogger", (), {"warning": lambda *a, **kw: None, "debug": lambda *a, **kw: None})())
            result = get_exchange_rate("USD", "EUR")

        assert "error" in result

    def test_get_exchange_rate_success(self, monkeypatch):
        def mock_get(url, params, timeout):
            class FakeResponse:
                def raise_for_status(self):
                    pass

                def json(self):
                    return {"rates": {"EUR": 0.92}, "date": "2024-01-01"}

            return FakeResponse()

        monkeypatch.setattr("requests.get", mock_get)

        from wanderai.ai.tools.currency_tool import get_exchange_rate

        with monkeypatch.context() as m:
            m.setattr("wanderai.ai.tools.currency_tool.logger", type("FakeLogger", (), {"warning": lambda *a, **kw: None, "debug": lambda *a, **kw: None})())
            result = get_exchange_rate("USD", "EUR")

        assert result["rate"] == 0.92
        assert result["from"] == "USD"
        assert result["to"] == "EUR"
        assert result["cached"] is False

    def test_get_exchange_rate_no_cache(self, monkeypatch):
        from wanderai.ai.tools.currency_tool import get_exchange_rate

        def mock_get(url, params, timeout):
            class FakeResponse:
                def raise_for_status(self):
                    pass

                def json(self):
                    return {"rates": {"USD": 1.0}, "date": "2024-01-01"}

            return FakeResponse()

        monkeypatch.setattr("requests.get", mock_get)
        result = get_exchange_rate("USD", "USD", cache=None)
        assert result["rate"] == 1.0 or "error" in result
