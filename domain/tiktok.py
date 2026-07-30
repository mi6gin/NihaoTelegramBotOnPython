"""Доменные значения TikTok, независимые от Telegram и слоя хранения."""

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class TikTokPost:
    """Нормализованные метаданные для одного поста TikTok."""

    source_url: str
    resolved_url: str
    media_type: str
    title: str
    author: str
    images: tuple[str, ...]
    music_url: str | None
    cover_url: str | None
    play_url: str | None

    @classmethod
    def from_mapping(
        cls,
        source_url: str,
        data: Mapping[str, Any],
    ) -> "TikTokPost":
        return cls(
            source_url=source_url,
            resolved_url=str(data.get("resolved_url") or source_url),
            media_type=str(data.get("type") or "video"),
            title=str(data.get("title") or "TikTok Video"),
            author=str(data.get("author") or ""),
            images=tuple(str(url) for url in data.get("images", ()) if url),
            music_url=data.get("music_url"),
            cover_url=data.get("cover"),
            play_url=data.get("play_url"),
        )

    @property
    def is_slideshow(self) -> bool:
        return self.media_type == "photo" and bool(self.images)
