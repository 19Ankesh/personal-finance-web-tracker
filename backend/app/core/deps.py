"""
FastAPI dependency: get_current_user.

Extracts the Bearer token from the Authorization header, decodes it,
and returns the authenticated User ORM object.

Import this dependency into any protected router::

    from app.core.deps import get_current_user

    @router.get("/protected")
    async def protected(current_user: User = Depends(get_current_user)):
        ...
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.session import get_db
from app.models.models import User

# tokenUrl must match the login route so Swagger's "Authorize" button works
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Validate the Bearer JWT and return the authenticated User.

    Raises:
        HTTPException 401 – if the token is missing, invalid, or expired.
        HTTPException 401 – if the user in the token no longer exists.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_token(token)
    if payload is None:
        raise credentials_exception

    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    user: User | None = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception

    return user
