"""Backward-compatible import for the TikTok infrastructure adapter.

New code should import :class:`infrastructure.tiktok.TikTokParser`.
"""

from infrastructure.tiktok import TikTokParser

__all__ = ["TikTokParser"]
