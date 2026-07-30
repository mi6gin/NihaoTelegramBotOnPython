"""Application orchestration for TikTok posts.

This module deliberately has no dependency on Aiogram, SQLAlchemy, or a concrete
HTTP client. Presentation and infrastructure are connected at the composition
edge.
"""

from collections.abc import MutableMapping
from typing import Any, Protocol

from domain.tiktok import TikTokPost


class TikTokGateway(Protocol):
    """Operations required from a TikTok infrastructure adapter."""

    @staticmethod
    def extract_video_id(url: str) -> str | None: ...

    @staticmethod
    async def get_post_info(url: str) -> dict[str, Any]: ...

    @staticmethod
    async def fetch_comments(
        url: str,
        cursor: int = 0,
        count: int = 5,
    ) -> dict[str, Any]: ...


class TikTokService:
    """Coordinate post metadata and short-lived interaction state."""

    def __init__(
        self,
        gateway: type[TikTokGateway],
        *,
        post_cache: MutableMapping[str, str] | None = None,
        comments_cache: MutableMapping[str, list[dict[str, Any]]] | None = None,
    ) -> None:
        self.gateway = gateway
        self.post_cache = post_cache if post_cache is not None else {}
        self.comments_cache = (
            comments_cache if comments_cache is not None else {}
        )

    def register_post_url(
        self,
        url: str,
        resolved_url: str | None = None,
    ) -> str:
        video_id = self.gateway.extract_video_id(url)
        if video_id is None and resolved_url:
            video_id = self.gateway.extract_video_id(resolved_url)

        if video_id:
            key = f"v{video_id}"
            self.post_cache[key] = (
                f"https://www.tiktok.com/@a/video/{video_id}"
            )
            return key

        # Keep callback data short. This fallback is process-local by design.
        key = str(abs(hash(url)) % 10_000_000)
        self.post_cache[key] = url
        return key

    def resolve_post_url(self, key: str) -> str | None:
        cached_url = self.post_cache.get(key)
        if cached_url:
            return cached_url

        if key.startswith("v") and key[1:].isdigit():
            video_id = key[1:]
        elif key.isdigit() and len(key) > 10:
            video_id = key
        else:
            return None

        url = f"https://www.tiktok.com/@a/video/{video_id}"
        self.post_cache[key] = url
        return url

    def remember_post_metadata(
        self,
        key: str,
        *,
        title: str | None = None,
        file_id: str | None = None,
    ) -> None:
        if title:
            self.post_cache[f"title_{key}"] = title
        if file_id:
            self.post_cache[f"file_id_{key}"] = file_id

    async def get_post(self, url: str) -> TikTokPost:
        data = await self.gateway.get_post_info(url)
        return TikTokPost.from_mapping(url, data)

    async def load_comments(
        self,
        key: str,
        *,
        count: int = 15,
    ) -> list[dict[str, Any]]:
        url = self.resolve_post_url(key)
        if url is None:
            return []

        result = await self.gateway.fetch_comments(url, cursor=0, count=count)
        comments = list(result.get("comments", ()))
        if comments:
            self.comments_cache[key] = comments
        return comments

    def get_comments(self, key: str) -> list[dict[str, Any]]:
        return self.comments_cache.get(key, [])
