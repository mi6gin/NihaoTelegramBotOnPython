"""Support-ticket business rules."""


class InvalidTicketMessage(ValueError):
    """Raised when a support message violates the accepted length."""


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
