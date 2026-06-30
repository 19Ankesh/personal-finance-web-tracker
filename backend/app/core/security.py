"""
Security utilities: password hashing and JWT token operations.
Uses native bcrypt for hashing (bypasses passlib compatibility issues in Python 3.12+) and python-jose for JWT.
"""
from datetime import datetime, timedelta
from typing import Optional
import bcrypt

from jose import JWTError, jwt

from app.core.config import settings

# ── Password hashing ──────────────────────────────────────────────────────────


def hash_password(plain_password: str) -> str:
    """Hash a plain-text password using bcrypt."""
    pwd_bytes = plain_password.encode("utf-8")
    # Limit to 72 bytes (bcrypt maximum length spec) to avoid truncation warnings
    pwd_bytes = pwd_bytes[:72]
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Return True if plain_password matches the stored hash."""
    try:
        pwd_bytes = plain_password.encode("utf-8")
        pwd_bytes = pwd_bytes[:72]
        hashed_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(pwd_bytes, hashed_bytes)
    except Exception:
        return False


# ── JWT tokens ────────────────────────────────────────────────────────────────

def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a signed JWT access token.

    Args:
        data:          Payload to encode (must include ``sub`` = user UUID string).
        expires_delta: Custom expiry window; defaults to ACCESS_TOKEN_EXPIRE_DAYS.

    Returns:
        Encoded JWT string.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta
        if expires_delta is not None
        else timedelta(days=settings.ACCESS_TOKEN_EXPIRE_DAYS)
    )
    to_encode["exp"] = expire
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    """
    Decode and validate a JWT token.

    Returns:
        Payload dict if the token is valid and not expired; None otherwise.
    """
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None
