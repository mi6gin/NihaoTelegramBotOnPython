import re
import os
import json
import asyncio
import aiohttp
import yt_dlp
from typing import Dict, Any, List, Optional
from utils.logger import logger

TEMP_DIR = os.path.abspath("data/temp")
os.makedirs(TEMP_DIR, exist_ok=True)

# Регулярные выражения для поиска ссылок на TikTok
TIKTOK_URL_REGEX = re.compile(
    r"https?://(?:vm|vt|m|www)\.tiktok\.com/(?:@[\w.-]+/video/\d+|@[\w.-]+/photo/\d+|\w+/|\S+)",
    re.IGNORECASE
)


class TikTokParser:
    """
    Асинхронный гибридный загрузчик контента из TikTok.
    Поддерживает:
    - Видео без водяных знаков (MP4) через yt-dlp.
    - Фото-слайдшоу (карусели из HD-картинок) через прямой асинхронный парсинг официального HTML/JSON.
    - Извлечение фонового аудиотрека (MP3).
    """

    @staticmethod
    def extract_url_from_text(text: str) -> Optional[str]:
        """
        Ищет первую ссылку на TikTok в тексте сообщения.
        """
        match = TIKTOK_URL_REGEX.search(text)
        return match.group(0) if match else None

    @staticmethod
    async def resolve_url(url: str) -> str:
        """
        Раскрывает сокращенные ссылки вида vt.tiktok.com/... до канонического URL tiktok.com/@user/video/...
        """
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            )
        }
        try:
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(url, allow_redirects=True, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    return str(resp.url)
        except Exception as e:
            logger.warning(f"Error resolving TikTok URL {url}: {e}")
            return url

    @staticmethod
    async def get_post_info(url: str) -> Dict[str, Any]:
        """
        Анализирует пост TikTok (видео или фото-слайдшоу).
        Возвращает тип поста ('video' или 'photo') и метаданные.
        """
        resolved_url = await TikTokParser.resolve_url(url)
        
        # Запрашиваем официальную страницу для анализа типа поста и слайдшоу
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            )
        }
        
        try:
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(resolved_url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    html = await resp.text()

            # Ищем встроенный JSON в странице TikTok
            json_match = re.search(
                r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__" type="application/json">(.*?)</script>',
                html,
                re.DOTALL
            )
            if json_match:
                data = json.loads(json_match.group(1))
                default_scope = data.get("__DEFAULT_SCOPE__", {})
                detail = default_scope.get("webapp.video-detail", {})
                item_info = detail.get("itemInfo", {}).get("itemStruct", {})

                if item_info:
                    images = item_info.get("imagePost", {}).get("images", [])
                    music = item_info.get("music", {}).get("playUrl")
                    
                    if images:
                        image_urls = [img.get("imageURL", {}).get("urlList", [None])[0] for img in images if img.get("imageURL", {}).get("urlList")]
                        return {
                            "type": "photo",
                            "resolved_url": resolved_url,
                            "title": item_info.get("desc", "TikTok Slideshow"),
                            "images": image_urls,
                            "music_url": music,
                            "author": item_info.get("author", {}).get("nickname", "TikTok User"),
                            "author_username": item_info.get("author", {}).get("uniqueId", ""),
                        }

        except Exception as e:
            logger.debug(f"Direct JSON parse error: {e}")

        # По умолчанию обрабатываем как видео
        return {
            "type": "video",
            "resolved_url": resolved_url,
            "title": "TikTok Video",
            "images": [],
            "music_url": None,
        }

    @staticmethod
    def _download_video_sync(url: str, output_path: str) -> Optional[str]:
        """
        Синхронная функция скачивания MP4 видео без водяных знаков через yt-dlp.
        """
        ydl_opts = {
            "format": "bestvideo+bestaudio/best",
            "outtmpl": output_path,
            "quiet": True,
            "no_warnings": True,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            if os.path.exists(output_path):
                return output_path
            # Если yt-dlp изменил расширение файла
            base_dir = os.path.dirname(output_path)
            for fname in os.listdir(base_dir):
                if fname.startswith(os.path.basename(output_path).split('.')[0]):
                    return os.path.join(base_dir, fname)
        except Exception as e:
            logger.error(f"yt-dlp download error for {url}: {e}")
        return None

    @staticmethod
    async def download_video(url: str, filename_prefix: str = "tiktok_video") -> Optional[str]:
        """
        Асинхронно скачивает видео MP4 без водяного знака.
        """
        output_file = os.path.join(TEMP_DIR, f"{filename_prefix}_{int(asyncio.get_event_loop().time() * 1000)}.mp4")
        return await asyncio.to_thread(TikTokParser._download_video_sync, url, output_file)

    @staticmethod
    async def download_audio(url: str, filename_prefix: str = "tiktok_audio") -> Optional[str]:
        """
        Асинхронно извлекает или скачивает аудиофайл MP3.
        """
        output_file = os.path.join(TEMP_DIR, f"{filename_prefix}_{int(asyncio.get_event_loop().time() * 1000)}.mp3")
        
        info = await TikTokParser.get_post_info(url)
        if info.get("music_url"):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(info["music_url"]) as resp:
                        if resp.status == 200:
                            content = await resp.read()
                            with open(output_file, "wb") as f:
                                f.write(content)
                            return output_file
            except Exception as e:
                logger.warning(f"Error downloading direct music_url: {e}")

        # Фолбек на yt-dlp для извлечения аудио
        def _download_audio_sync(u: str, out: str) -> Optional[str]:
            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": out,
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],
                "quiet": True,
                "no_warnings": True,
            }
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([u])
                if os.path.exists(out):
                    return out
            except Exception as e:
                logger.error(f"yt-dlp audio extract error: {e}")
            return None

        return await asyncio.to_thread(_download_audio_sync, url, output_file)
