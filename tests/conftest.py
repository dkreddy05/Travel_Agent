"""
tests/conftest.py
Shared pytest fixtures for all test scopes.
"""

import pytest


@pytest.fixture(scope="session")
def app():
    """Create app with testing config — one instance per test session."""
    from wanderai.app import create_app

    application = create_app("testing")

    with application.app_context():
        from wanderai.extensions import db

        db.create_all()
        yield application
        db.drop_all()


@pytest.fixture
def client(app):
    """Flask test client."""
    return app.test_client()


@pytest.fixture
def db(app):
    """Database session with rollback after each test."""
    from wanderai.extensions import db as _db

    connection = _db.engine.connect()
    transaction = connection.begin()

    yield _db

    _db.session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def test_user(db, app):
    """Create a test user in the database."""
    from wanderai.models.user import User, UserRole, AuthProvider

    user = User(
        email="test@wanderai.app",
        username="testuser",
        password_hash="$2b$12$test_hash_placeholder",
        email_verified=True,
        role=UserRole.USER,
        provider=AuthProvider.LOCAL,
    )
    db.session.add(user)
    db.session.flush()
    return user


@pytest.fixture
def auth_headers(client, test_user, app):
    """Return Authorization headers for an authenticated user."""
    with app.app_context():
        from flask_jwt_extended import create_access_token

        token = create_access_token(
            identity=test_user.id,
            additional_claims={"role": "user", "email_verified": True},
        )
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


@pytest.fixture
def mock_llm(monkeypatch):
    """Mock the AI client to avoid real LLM calls in tests."""
    mock_result = {
        "text": "**Paris, France** is a wonderful destination...\n\nWould you like more details?",
        "model": "meta-llama/llama-3-3-70b-instruct",
        "tokens_used": 150,
        "latency_ms": 50,
        "cached": False,
        "json_data": None,
    }

    def mock_run_single_prompt(prompt, task="general", **kwargs):
        return mock_result

    def mock_run_chat(user_message, conversation_id, **kwargs):
        return mock_result

    monkeypatch.setattr(
        "wanderai.ai.pipeline.run_single_prompt", mock_run_single_prompt
    )
    monkeypatch.setattr("wanderai.ai.pipeline.run_chat", mock_run_chat)
    return mock_result
