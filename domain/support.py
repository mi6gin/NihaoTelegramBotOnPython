"""Бизнес-правила тикетов техподдержки."""


class InvalidTicketMessage(ValueError):
    """Исключение, вызываемое при нарушении допустимой длины сообщения тикета."""


def validate_ticket_message(
    message: str,
    *,
    minimum: int = 10,
    maximum: int = 1000,
) -> str:
    normalized = message.strip()
    if not minimum <= len(normalized) <= maximum:
        raise InvalidTicketMessage
    return normalized
