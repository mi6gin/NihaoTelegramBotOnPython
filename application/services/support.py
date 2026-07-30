"""Support-ticket use cases."""

from typing import Any, Protocol

from domain.support import validate_ticket_message


class TicketRepositoryProtocol(Protocol):
    async def create(
        self,
        session: Any,
        user_id: int,
        message: str,
    ) -> Any: ...


class UserRepositoryProtocol(Protocol):
    async def get_admins(self, session: Any) -> list[Any]: ...


class SupportService:
    def __init__(
        self,
        tickets: TicketRepositoryProtocol,
        users: UserRepositoryProtocol,
    ) -> None:
        self.tickets = tickets
        self.users = users

    async def create_ticket(
        self,
        session: Any,
        user_id: int,
        message: str,
    ) -> tuple[Any, list[Any]]:
        normalized_message = validate_ticket_message(message)
        ticket = await self.tickets.create(
            session,
            user_id,
            normalized_message,
        )
        admins = await self.users.get_admins(session)
        return ticket, admins
