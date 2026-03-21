import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.db.models import AuthSession


async def create_session(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    access_token_hash: str,
    expires_at: datetime,
    user_agent: str | None,
    ip_address: str | None,
) -> AuthSession:
    session = AuthSession(
        user_id=user_id,
        access_token_hash=access_token_hash,
        expires_at=expires_at,
        user_agent=user_agent,
        ip_address=ip_address,
    )
    db.add(session)
    await db.flush()
    return session


async def get_by_token_hash(db: AsyncSession, token_hash: str) -> AuthSession | None:
    result = await db.execute(
        select(AuthSession).where(AuthSession.access_token_hash == token_hash)
    )
    return result.scalar_one_or_none()


async def get_by_id(db: AsyncSession, session_id: uuid.UUID) -> AuthSession | None:
    result = await db.execute(select(AuthSession).where(AuthSession.id == session_id))
    return result.scalar_one_or_none()


async def list_active_for_user(db: AsyncSession, user_id: uuid.UUID) -> list[AuthSession]:
    result = await db.execute(
        select(AuthSession).where(
            AuthSession.user_id == user_id,
            AuthSession.is_revoked.is_(False),
            AuthSession.expires_at > datetime.now(timezone.utc),
        )
    )
    return list(result.scalars().all())


async def revoke(db: AsyncSession, session: AuthSession) -> None:
    session.is_revoked = True
    await db.commit()
