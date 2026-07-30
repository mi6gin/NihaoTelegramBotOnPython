"""SQLAlchemy implementation of mailing audience queries."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.user import User
from domain.mailing import AudienceKind, MailingAudience


class MailingRepository:
    async def list_recipients(
        self,
        session: AsyncSession,
        audience: MailingAudience,
    ) -> list[User]:
        query = select(User).where(User.telegram_id > 0)

        if audience.kind is AudienceKind.LANGUAGE:
            query = query.where(User.language == audience.value)
        elif audience.kind is AudienceKind.THEME:
            query = query.where(User.selected_theme == audience.value)
        elif audience.kind is AudienceKind.LIST:
            if not audience.user_ids:
                return []
            query = select(User).where(
                User.telegram_id.in_(audience.user_ids),
            )

        result = await session.execute(query)
        return list(result.scalars().all())

    async def list_summaries(
        self,
        session: AsyncSession,
    ) -> list[dict[str, Any]]:
        query = (
            select(User.telegram_id, User.first_name, User.username)
            .where(User.telegram_id > 0)
            .order_by(User.registered_at.desc())
        )
        result = await session.execute(query)
        return [
            {
                "telegram_id": row[0],
                "first_name": row[1],
                "username": row[2],
            }
            for row in result.all()
        ]
