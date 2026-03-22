import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.auth.security import decode_token, hash_token
from src.backend.db.models import AuthSession, User
from src.backend.db.session import get_db

bearer = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        user_id = decode_token(credentials.credentials)
    except JWTError:
        raise exc

    # Check session is still active (not revoked)
    token_hash = hash_token(credentials.credentials)
    session_result = await db.execute(
        select(AuthSession).where(AuthSession.access_token_hash == token_hash)
    )
    session = session_result.scalar_one_or_none()
    if session is None or session.is_revoked:
        raise exc
    if session.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise exc

    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise exc

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentToken = Annotated[str, Depends(lambda c: c.credentials)]


async def get_current_token(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer)],
) -> str:
    return credentials.credentials
