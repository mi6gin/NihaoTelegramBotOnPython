"""Shared state and presentation helpers for TikTok handlers."""

from typing import Any, Optional

from aiogram_i18n import I18nContext

from application.services.tiktok import TikTokService
from database.models.user import User
from infrastructure.tiktok import TikTokParser


_post_urls_cache: dict[str, str] = {}
_comments_cache: dict[str, list[dict[str, Any]]] = {}
tiktok_service = TikTokService(
    TikTokParser,
    post_cache=_post_urls_cache,
    comments_cache=_comments_cache,
)


def register_post_url(url: str, resolved_url: Optional[str] = None) -> str:
    """Register a post URL for callback data."""
    return tiktok_service.register_post_url(url, resolved_url)


def format_user_caption(
    user: User,
    url: str,
    i18n: Optional[I18nContext] = None,
) -> str:
    """Build the required user and source caption for sent media."""
    username = user.username or user.first_name
    link_text = (
        i18n.get("tiktok-caption-link-text")
        if i18n
        else "Ссылка на TikTok"
    )
    return f'<b>@{username}</b> | <a href="{url}">{link_text}</a>'
