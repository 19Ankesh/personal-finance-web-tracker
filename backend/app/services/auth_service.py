"""
Authentication service layer.

Business logic for user registration and login lives here, not in the router.
"""
import logging
from datetime import timedelta

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, hash_password, verify_password, decode_token
from app.core.email import send_reset_password_email
from app.models.models import User
from app.schemas.user import TokenResponse, UserCreate, UserResponse

logger = logging.getLogger(__name__)


def register_user(user_data: UserCreate, db: Session) -> TokenResponse:
    """
    Register a new user account.

    Steps:
      1. Check email uniqueness.
      2. Hash the password with bcrypt.
      3. Persist the new User record.
      4. Issue a JWT access token.
      5. Return TokenResponse (token + public user data).

    Raises:
        HTTPException 400 – if the email is already registered.
    """
    existing = (
        db.query(User).filter(User.email == user_data.email.strip().lower()).first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists.",
        )

    user = User(
        name=user_data.name.strip(),
        email=user_data.email.strip().lower(),
        password_hash=hash_password(user_data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info("New user registered: %s (id=%s)", user.email, user.id)

    token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(days=settings.ACCESS_TOKEN_EXPIRE_DAYS),
    )
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


def login_user(email: str, password: str, db: Session) -> TokenResponse:
    """
    Authenticate an existing user.

    Steps:
      1. Look up the user by email.
      2. Verify the bcrypt password hash.
      3. Issue a JWT access token.
      4. Return TokenResponse.

    Raises:
        HTTPException 401 – if credentials are invalid.
    """
    user: User | None = (
        db.query(User).filter(User.email == email.strip().lower()).first()
    )
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(days=settings.ACCESS_TOKEN_EXPIRE_DAYS),
    )
    logger.info("User logged in: %s (id=%s)", user.email, user.id)
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


def forgot_password_request(email: str, db: Session) -> dict:
    """Generate password reset token and send recovery email (or print/log it)."""
    user = db.query(User).filter(User.email == email.strip().lower()).first()
    
    # Stateless security protection against email harvesting/enumeration
    if user:
        token = create_access_token(
            data={"sub": str(user.id), "action": "reset_password"},
            expires_delta=timedelta(minutes=15),
        )
        send_reset_password_email(user.email, token)
        logger.info("Password reset token generated and sent for user: %s", user.email)
    else:
        logger.info("Forgot password request for non-existent email: %s", email)
        
    return {"detail": "If the email is registered, a password reset link has been sent."}


def reset_user_password(token: str, new_password: str, db: Session) -> dict:
    """Validate token and reset the user's password."""
    payload = decode_token(token)
    if not payload or payload.get("action") != "reset_password":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The password reset link is invalid or has expired.",
        )

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    user.password_hash = hash_password(new_password)
    db.commit()
    logger.info("Password reset successfully completed for user: %s", user.email)
    return {"detail": "Your password has been successfully reset."}
