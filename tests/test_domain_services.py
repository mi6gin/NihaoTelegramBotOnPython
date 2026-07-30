from unittest.mock import AsyncMock

import pytest

from application.services.mailing import MailingService
from application.services.support import SupportService
from application.services.tiktok import TikTokService
from domain.mailing import AudienceKind, MailingAudience
from domain.support import InvalidTicketMessage, validate_ticket_message


class FakeTikTokGateway:
    @staticmethod
    def extract_video_id(url: str) -> str | None:
        marker = "/video/"
        return url.split(marker, 1)[1] if marker in url else None

    @staticmethod
    async def get_post_info(url: str) -> dict:
        return {
            "type": "photo",
            "resolved_url": f"{url}?resolved=1",
            "images": ["one.jpg", "two.jpg"],
        }

    @staticmethod
    async def fetch_comments(
        url: str,
        cursor: int = 0,
        count: int = 5,
    ) -> dict:
        return {"comments": [{"author": "A", "text": "B", "likes": 1}]}


def test_mailing_audience_parses_filters() -> None:
    assert MailingAudience.from_filter("lang_en") == MailingAudience(
        AudienceKind.LANGUAGE,
        value="en",
    )
    assert MailingAudience.from_filter(
        "list",
        [1, 1, 2],
    ).user_ids == (1, 2)


@pytest.mark.asyncio
async def test_mailing_service_passes_domain_audience_to_repository() -> None:
    repository = AsyncMock()
    repository.list_recipients.return_value = ["recipient"]
    service = MailingService(repository)

    result = await service.get_recipients(object(), "theme_theme_sakura")

    assert result == ["recipient"]
    audience = repository.list_recipients.await_args.args[1]
    assert audience == MailingAudience(
        AudienceKind.THEME,
        value="theme_sakura",
    )


def test_ticket_message_validation() -> None:
    assert validate_ticket_message("  valid message  ") == "valid message"
    with pytest.raises(InvalidTicketMessage):
        validate_ticket_message("short")


@pytest.mark.asyncio
async def test_support_service_validates_before_persistence() -> None:
    tickets = AsyncMock()
    users = AsyncMock()
    service = SupportService(tickets, users)

    with pytest.raises(InvalidTicketMessage):
        await service.create_ticket(object(), 123, "short")

    tickets.create.assert_not_awaited()
    users.get_admins.assert_not_awaited()


@pytest.mark.asyncio
async def test_tiktok_service_normalizes_and_restores_post_state() -> None:
    service = TikTokService(FakeTikTokGateway)
    url = "https://www.tiktok.com/@a/video/123456789012345"

    key = service.register_post_url(url)
    post = await service.get_post(url)
    comments = await service.load_comments(key)

    assert key == "v123456789012345"
    assert service.resolve_post_url(key) == url
    assert post.is_slideshow
    assert post.images == ("one.jpg", "two.jpg")
    assert comments == service.get_comments(key)
