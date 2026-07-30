"""Правила аудитории рассылок без зависимостей от фреймворков и базы данных."""

from dataclasses import dataclass
from enum import Enum
from typing import Iterable


class AudienceKind(str, Enum):
    ALL = "all"
    LANGUAGE = "language"
    THEME = "theme"
    LIST = "list"


@dataclass(frozen=True, slots=True)
class MailingAudience:
    kind: AudienceKind
    value: str | None = None
    user_ids: tuple[int, ...] = ()

    @classmethod
    def from_filter(
        cls,
        target_filter: str,
        selected_ids: Iterable[int] = (),
    ) -> "MailingAudience":
        if target_filter == "list":
            return cls(
                kind=AudienceKind.LIST,
                user_ids=tuple(dict.fromkeys(selected_ids)),
            )
        if target_filter.startswith("lang_"):
            return cls(
                kind=AudienceKind.LANGUAGE,
                value=target_filter.removeprefix("lang_"),
            )
        if target_filter.startswith("theme_"):
            return cls(
                kind=AudienceKind.THEME,
                value=target_filter.removeprefix("theme_"),
            )
        return cls(kind=AudienceKind.ALL)
