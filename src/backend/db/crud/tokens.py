import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.db.models import AuthSession, RefreshToken


async def create_refresh_token(
    db: AsyncSession,
    *,
    session_id: uuid.UUID,
    user_id: uuid.UUID,
    token_hash: str,
    expires_at: datetime,
) -> RefreshToken:
    token = RefreshToken(
        session_id=session_id,
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at,
    )
    db.add(token)
    await db.flush()
    return token


async def get_by_hash(db: AsyncSession, token_hash: str) -> RefreshToken | None:
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    return result.scalar_one_or_none()


async def consume(db: AsyncSession, token: RefreshToken) -> None:
    """Mark token as used. Call before issuing new token pair."""
    token.used_at = datetime.now(timezone.utc)
    await db.flush()


async def revoke_by_session(db: AsyncSession, session: AuthSession) -> None:
    """Revoke the refresh token tied to a session (used on replay detection)."""
    if session.refresh_token:
        session.refresh_token.is_revoked = True
    session.is_revoked = True
    await db.commit()
