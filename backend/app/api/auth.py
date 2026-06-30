"""
Authentication API router.

Routes:
  POST /auth/register – create a new account, returns JWT
  POST /auth/login    – OAuth2 form-data login, returns JWT
  GET  /auth/me       – return the currently authenticated user
"""
import logging

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.models import User
from app.schemas.user import (
    TokenResponse,
    UserCreate,
    UserResponse,
    ForgotPasswordRequest,
    ResetPasswordRequest,
)
from app.services.auth_service import (
    login_user,
    register_user,
    forgot_password_request,
    reset_user_password,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=201,
    summary="Register a new user account",
)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """
    Create a new FinSense account.

    - Validates input (unique email, password length ≥ 6).
    - Hashes the password with bcrypt.
    - Returns a 7-day JWT access token.
    """
    return register_user(user_data, db)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and receive a JWT token",
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> TokenResponse:
    """
    Authenticate with email and password.

    Accepts OAuth2 `application/x-www-form-urlencoded` format:
    - **username** field = your email address
    - **password** field = your password

    This format is required for Swagger UI's **Authorize** button to work.
    When using Postman or Insomnia, send `username` and `password` as form fields.
    """
    return login_user(email=form_data.username, password=form_data.password, db=db)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get the current authenticated user",
)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Return the profile of the currently authenticated user."""
    return UserResponse.model_validate(current_user)


@router.post(
    "/forgot-password",
    summary="Request a password reset email",
)
async def forgot_password(
    data: ForgotPasswordRequest,
    db: Session = Depends(get_db),
) -> dict:
    """
    Generate password reset token and send recovery email (or print/log it).
    """
    return forgot_password_request(data.email, db)


@router.post(
    "/reset-password",
    summary="Reset password using a token",
)
async def reset_password(
    data: ResetPasswordRequest,
    db: Session = Depends(get_db),
) -> dict:
    """
    Reset a user's password using the signed JWT token.
    """
    return reset_user_password(data.token, data.new_password, db)
