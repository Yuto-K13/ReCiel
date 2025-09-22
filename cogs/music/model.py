import asyncio
import collections
import datetime
from collections.abc import Generator, Iterable
from concurrent.futures import ProcessPoolExecutor
from typing import Self

import yt_dlp
import yt_dlp.utils
from discord import AudioSource, FFmpegPCMAudio, Interaction, Member, Message, User, VoiceChannel, VoiceClient
from discord.channel import VocalGuildChannel
from discord.ext import tasks

import utils
from utils.types import CielType

from . import error

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
FFMPEG_BEFORE_OPTIONS = [
    "-reconnect 1",
    "-reconnect_streamed 1",
    "-reconnect_delay_max 10",
    "-fflags nobuffer",
    "-fflags discardcorrupt",
    "-flags low_delay",
    "-avioflags direct",
    "-probesize 500M",
    "-analyzeduration 0",
]
FFMPEG_OPTIONS = ["-vn", "-af dynaudnorm"]

TIMEOUT = 300


class Track:
    def __init__(
        self,
        user: User | Member,
        *,
        title: str | None = None,
        url: str | None = None,
        channel: str | None = None,
        channel_url: str | None = None,
        thumbnail: str | None = None,
        duration: datetime.timedelta | None = None,
        source: str | None = None,
    ) -> None:
        self.user = user
        self.title = title
        self.url = url
        self.channel = channel
        self.channel_url = channel_url
        self.thumbnail = thumbnail
        self.duration = duration

        self.source = source

    def __hash__(self) -> int:
        return hash((self.user, self.source))

    @property
    def title_markdown(self) -> str:
        title = self.title or "Unknown"
        if self.url is None:
            return title
        return f"[{title}]({self.url})"

    @property
    def channel_markdown(self) -> str:
        channel = self.channel or "Unknown"
        if self.channel_url is None:
            return channel
        return f"[{channel}]({self.channel_url})"

    def get_audio_source(
        self,
        *,
        before_options: Iterable[str] | str | None = None,
        options: Iterable[str] | str | None = None,
    ) -> AudioSource:
        if self.source is None:
            raise utils.InvalidAttributeError(f"{self.__class__.__name__}.source")
        if isinstance(before_options, Iterable) and not isinstance(before_options, str):
            before_options = " ".join(before_options)
        if isinstance(options, Iterable) and not isinstance(options, str):
            options = " ".join(options)

        return FFmpegPCMAudio(self.source, before_options=before_options, options=options)


class YouTubeDLPTrack(Track):
    @staticmethod
    def _download(url: str) -> dict:
        try:
            with yt_dlp.YoutubeDL(YTDLP_OPTIONS) as ydl:  # pyright: ignore[reportArgumentType]
                info = ydl.extract_info(url, download=False)
                info = ydl.sanitize_info(info)
        except yt_dlp.utils.DownloadError as e:
            raise error.DownloadError(str(e)) from e
        except yt_dlp.utils.YoutubeDLError as e:
            raise error.YouTubeDLPError(str(e)) from e
        return info  # pyright: ignore[reportReturnType]

    @classmethod
    async def download(cls, user: User | Member, url: str) -> Self:
        loop = asyncio.get_running_loop()
        with ProcessPoolExecutor() as executor:
            info = await loop.run_in_executor(executor, cls._download, url)

        return cls.from_info(user, info)

    @classmethod
    def from_info(cls, user: User | Member, info: dict) -> Self:
        title = info.get("title")
        url = info.get("webpage_url")
        channel = info.get("uploader")
        channel_url = info.get("uploader_url")
        thumbnail = info.get("thumbnail")
        if duration := info.get("duration"):
            duration = datetime.timedelta(seconds=duration)

        source = info.get("url")
        headers = []
        if http_headers := info.get("http_headers"):
            headers.extend([f"{key}: {value}" for key, value in http_headers.items()])
        if cookies := info.get("cookies"):
            headers.append(f"Cookie: {cookies}")

        return cls(
            user=user,
            title=title,
            url=url,
            channel=channel,
            channel_url=channel_url,
            source=source,
            headers=headers,
            thumbnail=thumbnail,
            duration=duration,
        )

    def __init__(
        self,
        user: User | Member,
        *,
        title: str | None = None,
        url: str | None = None,
        channel: str | None = None,
        channel_url: str | None = None,
        thumbnail: str | None = None,
        duration: datetime.timedelta | None = None,
        source: str | None = None,
        headers: list[str] | None = None,
    ) -> None:
        super().__init__(
            user=user,
            title=title,
            url=url,
            channel=channel,
            channel_url=channel_url,
            thumbnail=thumbnail,
            duration=duration,
            source=source,
        )
        if headers is None:
            headers = []
        self.headers = headers

    def get_audio_source(
        self,
        *,
        before_options: Iterable[str] | str | None = None,
        options: Iterable[str] | str | None = None,
    ) -> AudioSource:
        if before_options is None:
            before_options = FFMPEG_BEFORE_OPTIONS.copy()
            if self.headers:
                before_options.append(f'-headers "{"\r\n".join(self.headers)}"')
        if options is None:
            options = FFMPEG_OPTIONS.copy()

        return super().get_audio_source(before_options=before_options, options=options)


class MusicQueue(asyncio.Queue):
    def __init__(self) -> None:
        super().__init__()
        self._current: Track | None = None
        self._queue_loop = False
        self._playing = asyncio.Event()

    def _init(self, maxsize) -> None:  # noqa: ANN001, ARG002
        self._queue: collections.deque[Track] = collections.deque()

    def _get(self) -> Track:
        return self._queue.popleft()

    def _put(self, item: Track) -> None:
        self._queue.append(item)

    def get_nowait(self) -> Track:
        track: Track = super().get_nowait()
        self._current = track
        self._playing.clear()
        return track

    def __getitem__(self, idx: int) -> Track:
        return self._queue[idx]

    def __setitem__(self, idx: int, value: Track) -> None:
        self._queue[idx] = value

    def __delitem__(self, idx: int) -> None:
        del self._queue[idx]

    def __hash__(self) -> int:
        return hash((self._queue_loop, self._current, *self._queue))

    @property
    def current(self) -> Track | None:
        return self._current

    @property
    def queue_loop(self) -> bool:
        return self._queue_loop

    @property
    def playing(self) -> bool:
        return not self._playing.is_set()

    def all(self, current: bool = True) -> Generator[Track]:
        if current and self._current is not None:
            yield self._current
        for track in self._queue:
            if track is not None:
                yield track

    def toggle(self) -> bool:
        self._queue_loop = not self._queue_loop
        return self._queue_loop

    def finish(self) -> None:
        self._current = None
        self._playing.set()

    def clear(self) -> None:
        self._queue.clear()
        self.finish()

    async def wait(self) -> None:
        await self._playing.wait()


class MusicState:
    @staticmethod
    def get_voice_channel(interaction: Interaction) -> VocalGuildChannel | None:
        user = interaction.user
        if isinstance(user, User):
            return None
        if user.voice is None or user.voice.channel is None:
            return None
        if user.voice.channel.guild != interaction.guild:
            return None
        return user.voice.channel

    def __init__(self, bot: CielType) -> None:
        self._bot = bot
        self._message: Message | None = None
        self._interaction: Interaction | None = None
        self._voice: VoiceClient | None = None
        self.queue = MusicQueue()

    def __del__(self) -> None:
        self.cancel()

    @property
    def message(self) -> Message:
        if self._message is None:
            raise utils.InvalidAttributeError(f"{self.__class__.__name__}.message") from error.NotConnectedError
        return self._message

    @message.setter
    def message(self, message: Message) -> None:
        self._message = message

    @property
    def voice(self) -> VoiceClient:
        if not self.is_connected():
            raise utils.InvalidAttributeError(f"{self.__class__.__name__}.voice") from error.NotConnectedError
        return self._voice  # pyright: ignore[reportReturnType]

    def is_connected(self) -> bool:
        return self._voice is not None and self._voice.is_connected()

    async def connect(self, interaction: Interaction) -> None:
        channel = self.get_voice_channel(interaction)
        if channel is None:
            raise error.UserNotInVoiceChannelError
        if channel.guild != interaction.guild:
            raise error.UserNotInSameGuildError

        if self.is_connected():
            raise error.AlreadyConnectedError

        self._interaction = interaction
        self._voice = await channel.connect(self_deaf=True)
        self.audio_loop.start()

    async def move(self, interaction: Interaction) -> None:
        channel = self.get_voice_channel(interaction)
        if channel is None:
            raise error.UserNotInVoiceChannelError
        if channel.guild != interaction.guild:
            raise error.UserNotInSameGuildError

        if not self.is_connected():
            raise error.NotConnectedError
        if self.voice.channel == channel:
            raise error.AlreadyConnectedError

        self._interaction = interaction
        await self.voice.move_to(channel)
        if self.audio_loop.is_running():
            self.audio_loop.restart()
        else:
            self.audio_loop.start()

    async def disconnect(self) -> None:
        if not self.is_connected():
            raise error.NotConnectedError

        self.cancel()
        await self.voice.disconnect()

    def cancel(self) -> None:
        if self.audio_loop.is_running():
            self.audio_loop.cancel()

    def skip(self) -> Track:
        if not self.is_connected():
            raise error.NotConnectedError
        track = self.queue.current
        if track is None:
            raise error.NoTrackPlayingError

        self.voice.stop()
        return track

    def next(self, error: Exception | None) -> None:
        if error is not None:
            track = self.queue.current
            utils.logger.exception(f"Error: {track.title if track is not None else 'Unknown Track'}", exc_info=error)
        self.queue.finish()

    async def reset_timer(self) -> None:
        if self.queue.empty() and not self.queue.playing:
            await self.queue.put(None)

    async def set_status(self, status: str | None) -> None:
        if isinstance(self.voice.channel, VoiceChannel):
            await self.voice.channel.edit(status=status)

    @tasks.loop()
    async def audio_loop(self) -> None:
        try:
            track: Track | None = await asyncio.wait_for(self.queue.get(), timeout=TIMEOUT)
        except TimeoutError:
            self._bot.dispatch("music_timeout", self)
            self.audio_loop.stop()
            return

        if track is None:
            self.queue.finish()
            return
        await self.set_status(f"🎵 Now Playing {track.title or 'Unknown Track'}")
        self.voice.play(track.get_audio_source(), after=self.next)
        await self.queue.wait()
        await self.set_status(None)

        if self.queue.queue_loop:
            await self.queue.put(track)

    @audio_loop.before_loop
    async def before_audio_loop(self) -> None:
        await self._bot.wait_until_ready()

    @audio_loop.after_loop
    async def after_audio_loop(self) -> None:
        if self.audio_loop.is_being_cancelled():
            self.queue.clear()
            if self.is_connected() and self.voice.is_playing():
                self.voice.stop()
