import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.db.models import (MemberRole, Membership, Organization,
                                   UsageQuota, User)


async def get_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_by_id(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def create_user_with_org(
    db: AsyncSession,
    *,
    email: str,
    hashed_password: str,
    full_name: str,
    org_name: str,
    job_title: str | None = None,
) -> User:
    user = User(
        email=email,
        hashed_password=hashed_password,
        full_name=full_name,
        job_title=job_title,
    )
    db.add(user)
    await db.flush()

    org = Organization(name=org_name)
    db.add(org)
    await db.flush()

    db.add(Membership(user_id=user.id, org_id=org.id, role=MemberRole.owner))
    db.add(
        UsageQuota(
            org_id=org.id,
            period_start=datetime.now(timezone.utc),
            queries_used=0,
            queries_limit=100,
        )
    )

    await db.commit()
    await db.refresh(user)
    return user


async def update_last_login(db: AsyncSession, user: User) -> None:
    user.last_login_at = datetime.now(timezone.utc)
    await db.commit()
