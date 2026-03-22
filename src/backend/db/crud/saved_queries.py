import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.db.models import SavedQuery


async def create(
    db: AsyncSession,
    user_id: uuid.UUID,
    name: str,
    query_text: str,
    result_json: dict,
    notes: str | None,
) -> SavedQuery:
    sq = SavedQuery(
        id=uuid.uuid4(),
        user_id=user_id,
        name=name,
        query_text=query_text,
        result=result_json,
        notes=notes,
    )
    db.add(sq)
    await db.commit()
    await db.refresh(sq)
    return sq


async def list_for_user(db: AsyncSession, user_id: uuid.UUID) -> list[SavedQuery]:
    result = await db.execute(
        select(SavedQuery)
        .where(SavedQuery.user_id == user_id)
        .order_by(SavedQuery.created_at.desc())
        .limit(100)
    )
    return list(result.scalars().all())


async def get_by_id(db: AsyncSession, sq_id: uuid.UUID) -> SavedQuery | None:
    result = await db.execute(select(SavedQuery).where(SavedQuery.id == sq_id))
    return result.scalar_one_or_none()


async def delete(db: AsyncSession, sq: SavedQuery) -> None:
    await db.delete(sq)
    await db.commit()
