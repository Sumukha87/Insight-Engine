import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.auth.security import (ACCESS_TOKEN_EXPIRE_MINUTES,
                                       create_access_token)
from src.backend.db.crud import sessions as sessions_crud
from src.backend.db.crud import tokens as tokens_crud
from src.backend.db.models import AuthSession, RefreshToken, User

REFRESH_TOKEN_EXPIRE_DAYS = int(os.environ.get("REFRESH_TOKEN_EXPIRE_DAYS", "30"))


def _hash(value: str) -> str:
    """SHA-256 hex digest — used for storing tokens without reversibility."""
    return hashlib.sha256(value.encode()).hexdigest()


async def issue_tokens(
    db: AsyncSession,
    user: User,
    *,
    user_agent: str | None = None,
    ip_address: str | None = None,
) -> tuple[str, str]:
    """
    Create a new session + refresh token pair.
    Returns (access_token, refresh_token) — raw values for sending to client.
    Only hashes are persisted in DB.
    """
    now = datetime.now(timezone.utc)
    access_token = create_access_token(str(user.id))
    access_expires = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    session = await sessions_crud.create_session(
        db,
        user_id=user.id,
        access_token_hash=_hash(access_token),
        expires_at=access_expires,
        user_agent=user_agent,
        ip_address=ip_address,
    )

    refresh_raw = secrets.token_hex(32)
    refresh_expires = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    await tokens_crud.create_refresh_token(
        db,
        session_id=session.id,
        user_id=user.id,
        token_hash=_hash(refresh_raw),
        expires_at=refresh_expires,
    )

    await db.commit()
    return access_token, refresh_raw


async def refresh_tokens(
    db: AsyncSession,
    refresh_raw: str,
    *,
    user_agent: str | None = None,
    ip_address: str | None = None,
) -> tuple[str, str] | None:
    """
    Validate and rotate a refresh token.
    Returns new (access_token, refresh_token) or None if invalid/expired.
    If replay detected (token already used), revokes entire session.
    """
    token = await tokens_crud.get_by_hash(db, _hash(refresh_raw))

    if token is None or token.is_revoked:
        return None

    now = datetime.now(timezone.utc)
    if token.expires_at.replace(tzinfo=timezone.utc) < now:
        return None

    # Replay attack — token already used
    if token.used_at is not None:
        await tokens_crud.revoke_by_session(db, token.session)
        return None

    # Mark old token consumed, revoke old session
    await tokens_crud.consume(db, token)
    await sessions_crud.revoke(db, token.session)

    # Issue fresh pair
    from src.backend.db.crud import users as users_crud

    user = await users_crud.get_by_id(db, token.user_id)
    if user is None or not user.is_active:
        return None

    return await issue_tokens(db, user, user_agent=user_agent, ip_address=ip_address)


async def revoke_session_by_token_hash(
    db: AsyncSession, access_token_hash: str
) -> None:
    session = await sessions_crud.get_by_token_hash(db, access_token_hash)
    if session and not session.is_revoked:
        await tokens_crud.revoke_by_session(db, session)
