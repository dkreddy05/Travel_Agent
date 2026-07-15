"""Integration tests for AuthService business logic."""


class TestAuthServiceRegister:
    def test_register_success(self, db, app, monkeypatch):
        from wanderai.services.auth_service import AuthService

        service = AuthService()
        with app.app_context():
            result = service.register(
                email="newuser@example.com",
                password="SecurePass1",
                username="newuser",
            )
        assert result["success"] is True
        assert result["user"].email == "newuser@example.com"

    def test_register_invalid_email(self, db, app):
        from wanderai.services.auth_service import AuthService

        service = AuthService()
        with app.app_context():
            result = service.register(email="not-an-email", password="SecurePass1")
        assert result["success"] is False
        assert "Invalid email" in result["error"]

    def test_register_weak_password(self, db, app):
        from wanderai.services.auth_service import AuthService

        service = AuthService()
        with app.app_context():
            result = service.register(email="weakpw@example.com", password="123")
        assert result["success"] is False
        assert "8 characters" in result["error"]

    def test_register_duplicate_email(self, db, app, monkeypatch):
        from wanderai.services.auth_service import AuthService

        service = AuthService()
        with app.app_context():
            service.register(email="dupe@example.com", password="SecurePass1")
            result = service.register(email="dupe@example.com", password="SecurePass2")
        assert result["success"] is False
        assert "already registered" in result["error"].lower()

    def test_register_creates_preferences(self, db, app):
        from wanderai.services.auth_service import AuthService
        from wanderai.models.preference import UserPreference

        service = AuthService()
        with app.app_context():
            result = service.register(email="prefs@example.com", password="SecurePass1")
            user = result["user"]
            pref = UserPreference.query.filter_by(user_id=user.id).first()
            assert pref is not None


class TestAuthServiceLogin:
    def test_login_success(self, db, app):
        from wanderai.services.auth_service import AuthService

        service = AuthService()
        with app.app_context():
            service.register(email="login@example.com", password="SecurePass1")
            # Manually verify email
            from wanderai.models.user import User

            user = User.query.filter_by(email="login@example.com").first()
            user.email_verified = True
            from wanderai.extensions import db

            db.session.commit()

            result = service.login(email="login@example.com", password="SecurePass1")
        assert result["success"] is True
        assert "access_token" in result
        assert "refresh_token" in result

    def test_login_invalid_credentials(self, db, app):
        from wanderai.services.auth_service import AuthService

        service = AuthService()
        with app.app_context():
            result = service.login(email="nonexistent@test.com", password="pass")
        assert result["success"] is False
        assert "Invalid credentials" in result["error"]

    def test_login_wrong_password(self, db, app):
        from wanderai.services.auth_service import AuthService

        service = AuthService()
        with app.app_context():
            service.register(email="wrongpw@test.com", password="SecurePass1")
            from wanderai.models.user import User

            user = User.query.filter_by(email="wrongpw@test.com").first()
            user.email_verified = True
            from wanderai.extensions import db

            db.session.commit()

            result = service.login(email="wrongpw@test.com", password="WrongPass1")
        assert result["success"] is False
        assert "Invalid credentials" in result["error"]

    def test_login_account_disabled(self, db, app):
        from wanderai.services.auth_service import AuthService

        service = AuthService()
        with app.app_context():
            service.register(email="disabled@test.com", password="SecurePass1")
            from wanderai.models.user import User

            user = User.query.filter_by(email="disabled@test.com").first()
            user.is_active = False
            user.email_verified = True
            from wanderai.extensions import db

            db.session.commit()

            result = service.login(email="disabled@test.com", password="SecurePass1")
        assert result["success"] is False
        assert "disabled" in result["error"].lower()

    def test_login_email_not_verified(self, db, app):
        from wanderai.services.auth_service import AuthService

        service = AuthService()
        with app.app_context():
            service.register(email="unverified@test.com", password="SecurePass1")
            result = service.login(email="unverified@test.com", password="SecurePass1")
        assert result["success"] is False
        assert "verify your email" in result["error"].lower()


class TestAuthServiceOAuth:
    def test_login_oauth_creates_new_user(self, db, app):
        from wanderai.services.auth_service import AuthService
        from wanderai.models.user import AuthProvider

        service = AuthService()
        with app.app_context():
            result = service.login_oauth(
                provider=AuthProvider.GOOGLE,
                provider_id="google-123",
                email="oauth@example.com",
                username="oauthuser",
            )
        assert result["success"] is True

    def test_login_oauth_links_existing_account(self, db, app):
        from wanderai.services.auth_service import AuthService
        from wanderai.models.user import AuthProvider

        service = AuthService()
        with app.app_context():
            service.register(email="existing@test.com", password="SecurePass1")
            result = service.login_oauth(
                provider=AuthProvider.GITHUB,
                provider_id="github-456",
                email="existing@test.com",
            )
        assert result["success"] is True

    def test_login_oauth_reuses_existing_provider(self, db, app):
        from wanderai.services.auth_service import AuthService
        from wanderai.models.user import AuthProvider

        service = AuthService()
        with app.app_context():
            service.login_oauth(
                provider=AuthProvider.GOOGLE,
                provider_id="same-user",
                email="same@test.com",
            )
            result = service.login_oauth(
                provider=AuthProvider.GOOGLE,
                provider_id="same-user",
                email="same@test.com",
            )
        assert result["success"] is True


class TestAuthServiceEmailVerification:
    def test_verify_email_success(self, db, app):
        from wanderai.services.auth_service import AuthService
        from wanderai.models.user import User

        service = AuthService()
        with app.app_context():
            service.register(email="verify@test.com", password="SecurePass1")
            user = User.query.filter_by(email="verify@test.com").first()
            token = user.email_verify_token
            assert token is not None

            verify_result = service.verify_email(token)
        assert verify_result["success"] is True

    def test_verify_email_invalid_token(self, db, app):
        from wanderai.services.auth_service import AuthService

        service = AuthService()
        with app.app_context():
            result = service.verify_email("invalid-token-123")
        assert result["success"] is False
        assert "Invalid" in result["error"]


class TestAuthServiceLogout:
    def test_logout(self, db, app, monkeypatch):
        from wanderai.services.auth_service import AuthService

        class FakeCache:
            def __init__(self):
                self.store = {}

            def set(self, key, value, timeout):
                self.store[key] = value

            def get(self, key):
                return self.store.get(key)

        fake_cache = FakeCache()
        monkeypatch.setattr("wanderai.extensions.cache", fake_cache)

        service = AuthService()
        with app.app_context():
            service.register(email="logout@test.com", password="SecurePass1")
            from wanderai.models.user import User

            user = User.query.filter_by(email="logout@test.com").first()
            user.email_verified = True
            from wanderai.extensions import db

            db.session.commit()

            login_result = service.login(
                email="logout@test.com", password="SecurePass1"
            )
            from flask_jwt_extended import get_jti

            jti = get_jti(login_result["access_token"])

            service.logout(jti)
