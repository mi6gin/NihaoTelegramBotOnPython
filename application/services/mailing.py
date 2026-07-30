"""Mailing use cases."""

from typing import Any, Protocol

from domain.mailing import MailingAudience


class MailingRepositoryProtocol(Protocol):
    async def list_recipients(
        self,
        session: Any,
        audience: MailingAudience,
    ) -> list[Any]: ...

    async def list_summaries(self, session: Any) -> list[dict[str, Any]]: ...


class MailingService:
    def __init__(self, repository: MailingRepositoryProtocol) -> None:
        self.repository = repository

    async def get_recipients(
        self,
        session: Any,
        target_filter: str,
        selected_ids: list[int] | None = None,
    ) -> list[Any]:
        audience = MailingAudience.from_filter(
            target_filter,
            selected_ids or (),
        )
        return await self.repository.list_recipients(session, audience)

    async def get_user_summaries(
        self,
        session: Any,
    ) -> list[dict[str, Any]]:
        return await self.repository.list_summaries(session)
