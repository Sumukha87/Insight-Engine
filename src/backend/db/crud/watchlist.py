import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.db.models import EntityWatchlist


async def add(
    db: AsyncSession,
    user_id: uuid.UUID,
    entity_name: str,
    entity_type: str,
    entity_domain: str,
) -> EntityWatchlist | None:
    """Returns None if entity is already on the watchlist."""
    item = EntityWatchlist(
        id=uuid.uuid4(),
        user_id=user_id,
        entity_name=entity_name,
        entity_type=entity_type,
        entity_domain=entity_domain,
    )
    db.add(item)
    try:
        await db.commit()
        await db.refresh(item)
        return item
    except IntegrityError:
        await db.rollback()
        return None


async def list_for_user(db: AsyncSession, user_id: uuid.UUID) -> list[EntityWatchlist]:
    result = await db.execute(
        select(EntityWatchlist)
        .where(EntityWatchlist.user_id == user_id)
        .order_by(EntityWatchlist.added_at.desc())
    )
    return list(result.scalars().all())


async def remove(db: AsyncSession, user_id: uuid.UUID, entity_name: str) -> bool:
    result = await db.execute(
        select(EntityWatchlist).where(
            EntityWatchlist.user_id == user_id,
            EntityWatchlist.entity_name == entity_name,
        )
    )
    item = result.scalar_one_or_none()
    if item is None:
        return False
    await db.delete(item)
    await db.commit()
    return True
