"""
wanderai/utils/security.py
Cryptographic utilities — password hashing, token generation.
Never store plain-text passwords. bcrypt cost factor 12 is OWASP recommended.
"""
import secrets
import string
import bcrypt


def hash_password(plain_text: str) -> str:
    """Hash a password with bcrypt (cost=12). Returns str for DB storage."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(plain_text.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_text: str, hashed: str) -> bool:
    """Return True if plain_text matches the bcrypt hash."""
    try:
        return bcrypt.checkpw(plain_text.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def generate_token(length: int = 64) -> str:
    """Generate a cryptographically secure URL-safe token."""
    return secrets.token_urlsafe(length)


def generate_otp(length: int = 6) -> str:
    """Generate a numeric OTP code."""
    return "".join(secrets.choice(string.digits) for _ in range(length))


def mask_secret(value: str, visible: int = 4) -> str:
    """Mask a secret for logging: 'sk-abc...' → 'sk-a****'."""
    if not value or len(value) <= visible:
        return "****"
    return value[:visible] + "*" * (len(value) - visible)
