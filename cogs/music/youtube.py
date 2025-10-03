import asyncio
import os
import urllib.parse
from concurrent.futures import ProcessPoolExecutor

import aiohttp
import yt_dlp
import yt_dlp.utils

from . import errors

YTDLP_OPTIONS = {
    "format": "bestaudio/best",
    "quiet": True,
    "noplaylist": True,
    "no_warnings": True,
    "ignore_errors": True,
    "noprogress": True,
    "geo-country": "JP",
    "max_results": 1,
}

YOUTUBE_API_KEY = os.getenv("GOOGLE_API_KEY")
YOUTUBE_API_URL = "https://www.googleapis.com/youtube/v3/search"


def _download(url: str) -> dict:
    try:
        with yt_dlp.YoutubeDL(YTDLP_OPTIONS) as ydl:  # pyright: ignore[reportArgumentType]
            info = ydl.extract_info(url, download=False)
            info = ydl.sanitize_info(info)
    except yt_dlp.utils.DownloadError as e:
        raise errors.DownloadError(str(e)) from e
    except yt_dlp.utils.YoutubeDLError as e:
        raise errors.YouTubeDLPError(str(e)) from e
    return info  # pyright: ignore[reportReturnType]


async def download(url: str) -> dict:
    loop = asyncio.get_running_loop()
    with ProcessPoolExecutor() as executor:
        return await loop.run_in_executor(executor, _download, url)


async def search(word: str, *, results: int = 1, token: str = "") -> dict:
    query = {
        "part": "snippet",
        "type": "video",
        "maxResults": results,
        "q": word,
        "key": YOUTUBE_API_KEY,
        "pageToken": token,
    }
    parse = urllib.parse.urlparse(YOUTUBE_API_URL)
    parse = parse._replace(query=urllib.parse.urlencode(query))
    url = urllib.parse.urlunparse(parse)

    async with aiohttp.ClientSession() as session, session.get(url) as res:
        info: dict = await res.json()
    if "error" in info:
        error_info: dict = info["error"]
        raise errors.SearchError(error_info.get("message"))
    if "items" not in info or not isinstance(info["items"], list) or len(info["items"]) <= 0:
        raise errors.SearchError("No results found.")
    return info
