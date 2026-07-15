"""Tests for AI prompts registry and templates."""


class TestPromptRegistry:
    def test_register_and_get(self):
        from wanderai.ai.prompts.registry import register, get, PromptTemplate

        tpl = PromptTemplate(
            name="test_prompt",
            version="1.0.0",
            description="Test",
            system="You are a test assistant",
            user_template="{{ message }}",
        )
        register(tpl)

        retrieved = get("test_prompt", "1.0.0")
        assert retrieved is not None
        assert retrieved.name == "test_prompt"
        assert retrieved.system == "You are a test assistant"

    def test_get_latest(self):
        from wanderai.ai.prompts.registry import register, get, PromptTemplate

        tpl = PromptTemplate(
            name="latest_test",
            version="2.0.0",
            description="Test latest",
            system="Latest version",
            user_template="{{ msg }}",
        )
        register(tpl)

        latest = get("latest_test")
        assert latest is not None
        assert latest.version == "2.0.0"

    def test_get_nonexistent(self):
        from wanderai.ai.prompts.registry import get

        assert get("nonexistent") is None

    def test_list_all(self):
        from wanderai.ai.prompts.registry import list_all, register, PromptTemplate

        # Register a new unique one for this test
        tpl = PromptTemplate(
            name="list_test_unique",
            version="1.0.0",
            description="For listing",
            system="system",
            user_template="{{ q }}",
        )
        register(tpl)

        all_templates = list_all()
        names = [t.name for t in all_templates]
        assert "list_test_unique" in names


class TestBudgetPrompt:
    def test_budget_template_registered(self):
        # Import triggers module-level registration
        import wanderai.ai.prompts.budget  # noqa: F401
        from wanderai.ai.prompts.registry import get

        tpl = get("budget", "2.0.0")
        assert tpl is not None
        assert tpl.name == "budget"
        assert "Daily Budget Breakdown" in tpl.user_template


class TestItineraryPrompt:
    def test_itinerary_template_registered(self):
        # Import triggers module-level registration
        import wanderai.ai.prompts.itinerary  # noqa: F401
        from wanderai.ai.prompts.registry import get

        tpl = get("itinerary", "2.0.0")
        assert tpl is not None
        assert tpl.name == "itinerary"
        assert "Day-by-Day Itinerary" in tpl.user_template
