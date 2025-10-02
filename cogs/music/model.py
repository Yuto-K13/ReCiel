import asyncio
import collections
import json
from collections.abc import Generator, Iterable
from datetime import timedelta
from typing import Self

from discord import ClientUser, Guild, Interaction, Member, Message, User, VoiceClient
from discord.channel import VocalGuildChannel, VoiceChannel
from discord.ext import tasks
from discord.player import AudioSource, FFmpegPCMAudio

import utils
from utils.types import CielType

from . import errors, youtube
from .agent import APP_NAME, RUNNER, SESSION_SERVICE

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
        user: User | Member | ClientUser | None,
        *,
        title: str | None = None,
        url: str | None = None,
        channel: str | None = None,
        channel_url: str | None = None,
        thumbnail: str | None = None,
        duration: timedelta | None = None,
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
    def user_name(self) -> str:
        if self.user is None:
            return "Unknown"
        return self.user.display_name

    @property
    def user_icon(self) -> str | None:
        if self.user is None:
            return None
        return self.user.display_avatar.url

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
    @classmethod
    async def download(cls, user: User | Member | ClientUser | None, url: str) -> Self:
        user_name = user.display_name if user is not None else "Unknown"
        utils.logger.debug(f"Downloading Track (User: {user_name}, URL: {url})")
        info = await youtube.download(url)
        return cls.from_info(user, info)

    @classmethod
    def from_info(cls, user: User | Member | ClientUser | None, info: dict) -> Self:
        title = info.get("title")
        url = info.get("webpage_url")
        channel = info.get("uploader")
        channel_url = info.get("uploader_url")
        thumbnail = info.get("thumbnail")
        duration = info.get("duration")
        if duration is not None:
            duration = timedelta(seconds=duration)

        source = info.get("url")
        headers = []
        http_headers = info.get("http_headers")
        if http_headers is not None:
            headers.extend([f"{key}: {value}" for key, value in http_headers.items()])
        cookies = info.get("cookies")
        if cookies is not None:
            headers.append(f"Cookie: {cookies}")

        extractor = info.get("extractor")
        if extractor == "niconico":
            uploader_id = info.get("uploader_id")
            if uploader_id is not None and channel_url is None:
                channel_url = f"https://www.nicovideo.jp/user/{uploader_id}"

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
        user: User | Member | ClientUser | None,
        *,
        title: str | None = None,
        url: str | None = None,
        channel: str | None = None,
        channel_url: str | None = None,
        thumbnail: str | None = None,
        duration: timedelta | None = None,
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

    def set_default_info(self, track: Track) -> Self:
        self.title = self.title or track.title
        self.url = self.url or track.url
        self.channel = self.channel or track.channel
        self.channel_url = self.channel_url or track.channel_url
        self.thumbnail = self.thumbnail or track.thumbnail
        self.duration = self.duration or track.duration

        return self


class GoogleSearchTrack(Track):
    @classmethod
    async def search_top(cls, user: User | Member | ClientUser, word: str) -> Self:
        tracks, _ = await cls.search(user, word, results=1)
        return tracks[0]

    @classmethod
    async def search(
        cls,
        user: User | Member | ClientUser | None,
        word: str,
        *,
        results: int,
        token: str = "",
    ) -> tuple[list[Self], str]:
        user_name = user.display_name if user is not None else "Unknown"
        utils.logger.debug(f"Searching Tracks (User: {user_name}, Query: {word})")
        info = await youtube.search(word, results=results, token=token)
        token = info.get("nextPageToken", "")
        tracks = [cls.from_info(user, i) for i in info.get("items", [])]

        return tracks, token

    @classmethod
    def from_info(cls, user: User | Member | ClientUser | None, info: dict[str, dict]) -> Self:
        snippet = info.get("snippet", {})

        title = snippet.get("title")
        video_id = info.get("id", {}).get("videoId")
        url = f"https://www.youtube.com/watch?v={video_id}" if video_id is not None else None

        channel = snippet.get("channelTitle")
        channel_id = snippet.get("channelId")
        channel_url = f"https://www.youtube.com/channel/{channel_id}" if channel_id is not None else None

        thumbnails: dict[str, dict] = snippet.get("thumbnails", {})
        for key in ("high", "medium", "default"):
            thumbnail = thumbnails.get(key, {}).get("url")
            if thumbnail is not None:
                break
        else:
            thumbnail = None

        return cls(user=user, title=title, url=url, channel=channel, channel_url=channel_url, thumbnail=thumbnail)

    async def download(self) -> YouTubeDLPTrack:
        if self.url is None:
            raise utils.InvalidAttributeError(f"{self.__class__.__name__}.url")
        track = await YouTubeDLPTrack.download(self.user, self.url)
        return track.set_default_info(self)


class MusicQueue(asyncio.Queue):
    def __init__(self) -> None:
        super().__init__()
        self._current: Track | None = None
        self._queue_loop = False
        self._auto_play: str | None = None
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

    async def put(self, item: Track) -> None:
        return await super().put(item)

    async def get(self) -> Track:
        return await super().get()

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
    def auto_play(self) -> str | None:
        return self._auto_play

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

    def enable_auto_play(self, word: str) -> None:
        self._auto_play = word

    def disable_auto_play(self) -> None:
        self._auto_play = None

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

    def __init__(self, bot: CielType, guild: Guild) -> None:
        self._bot = bot
        self._guild = guild
        self._message: Message | None = None
        self._voice: VoiceClient | None = None
        self._timeout: asyncio.Timeout | None = None
        self.queue = MusicQueue()

    def __del__(self) -> None:
        self.cancel()

    @property
    def guild(self) -> Guild:
        return self._guild

    @property
    def message(self) -> Message:
        if self._message is None:
            raise utils.InvalidAttributeError(f"{self.__class__.__name__}.message") from errors.NotConnectedError
        return self._message

    @message.setter
    def message(self, message: Message) -> None:
        if not isinstance(message, Message):
            raise TypeError(f"Requires Message instance, not {message.__class__.__name__}")
        self._message = message

    @property
    def voice(self) -> VoiceClient:
        if not self.is_connected():
            raise utils.InvalidAttributeError(f"{self.__class__.__name__}.voice") from errors.NotConnectedError
        return self._voice  # pyright: ignore[reportReturnType]

    def get_session_info(self) -> tuple[str, str]:
        return str(self.guild.id), str(self.voice.channel.id)

    def is_connected(self) -> bool:
        return self._voice is not None and self._voice.is_connected()

    async def is_session_active(self) -> bool:
        if not self.is_connected():
            return False
        user_id, session_id = self.get_session_info()
        return await utils.is_session_active(
            SESSION_SERVICE,
            app_name=APP_NAME,
            user_id=user_id,
            session_id=session_id,
        )

    async def is_valid(self) -> bool:
        if not self.is_connected():
            return False
        if not self.audio_loop.is_running():
            return False
        return await self.is_session_active()

    async def set_status(self, status: str | None) -> None:
        if isinstance(self.voice.channel, VoiceChannel):
            await self.voice.channel.edit(status=status)

    async def connect(self, interaction: Interaction) -> None:
        channel = self.get_voice_channel(interaction)
        if channel is None:
            raise errors.UserNotInVoiceChannelError
        if channel.guild != interaction.guild:
            raise errors.UserNotInSameGuildError
        utils.logger.debug(f"Connecting (Guild: {self.guild.name}, Channel: {channel.name})")

        if self.is_connected():
            raise errors.AlreadyConnectedError

        self._voice = await channel.connect(self_deaf=True)
        user_id, session_id = self.get_session_info()
        await SESSION_SERVICE.create_session(app_name=APP_NAME, user_id=user_id, session_id=session_id)
        self.audio_loop.start()

    async def move(self, interaction: Interaction) -> None:
        channel = self.get_voice_channel(interaction)
        if channel is None:
            raise errors.UserNotInVoiceChannelError
        if channel.guild != interaction.guild:
            raise errors.UserNotInSameGuildError
        if not self.is_connected():
            raise errors.NotConnectedError
        if self.voice.channel == channel:
            raise errors.AlreadyConnectedError
        utils.logger.debug(f"Moving (Guild: {self.guild.name}, Channel: {self.voice.channel.name} -> {channel.name})")

        self.cancel()
        await self.set_status(None)
        user_id, session_id = self.get_session_info()
        await SESSION_SERVICE.delete_session(app_name=APP_NAME, user_id=user_id, session_id=session_id)
        await self.voice.move_to(channel)

        user_id, session_id = self.get_session_info()
        await SESSION_SERVICE.create_session(app_name=APP_NAME, user_id=user_id, session_id=session_id)
        self.audio_loop.start()

    async def disconnect(self) -> None:
        if not self.is_connected():
            raise errors.NotConnectedError
        utils.logger.debug(f"Disconnecting (Guild: {self.guild.name}, Channel: {self.voice.channel.name})")

        self.cancel()
        await self.set_status(None)
        user_id, session_id = self.get_session_info()
        await SESSION_SERVICE.delete_session(app_name=APP_NAME, user_id=user_id, session_id=session_id)
        await self.voice.disconnect()

    async def skip(self) -> Track:
        if not self.is_connected():
            raise errors.NotConnectedError
        track = self.queue.current
        if track is None:
            raise errors.NoTrackPlayingError

        self.voice.stop()
        await self.set_status(None)
        return track

    async def suggestion(self) -> GoogleSearchTrack:
        if not self.is_connected():
            raise errors.NotConnectedError
        if self.queue.auto_play is None or not self.queue.empty():
            raise errors.InvalidAutoPlayStateError

        user_id, session_id = self.get_session_info()
        info = await utils.run_agent(
            SESSION_SERVICE,
            RUNNER,
            app_name=APP_NAME,
            user_id=user_id,
            session_id=session_id,
            query=self.queue.auto_play,
        )

        try:
            info = json.loads(info)
        except json.JSONDecodeError as e:
            raise utils.GoogleADKError("Failed to parse JSON") from e

        return GoogleSearchTrack(self._bot.user, **info)

    def cancel(self) -> None:
        running = self.audio_loop.is_running()
        utils.logger.debug(f"Cancelling Audio Loop (Guild: {self.guild.name}, Running: {running})")
        if running:
            self.audio_loop.cancel()

    def next(self, error: Exception | None) -> None:
        if error is not None:
            track = self.queue.current.title if self.queue.current is not None else "Unknown Track"
            utils.logger.exception(f"Error in Playing (Track: {track})", exc_info=error)
        self.queue.finish()

    def when_timeout(self) -> float:
        return self._bot.loop.time() + TIMEOUT

    def reset_timer(self) -> None:
        utils.logger.debug(f"Resetting Timeout Timer (Guild: {self.guild.name})")
        if self._timeout is not None and not self._timeout.expired():
            self._timeout.reschedule(self.when_timeout())

    @tasks.loop()
    async def audio_loop(self) -> None:
        try:
            async with asyncio.timeout_at(self.when_timeout()) as self._timeout:
                track = await self.queue.get()
        except TimeoutError:
            self._bot.dispatch("music_timeout", self)
            self.audio_loop.stop()
            return
        finally:
            self._timeout = None

        utils.logger.info(f"Start Playing (Guild: {self.guild.name}, Track: {track.title or 'Unknown Track'})")
        await self.set_status(f"🎵 Now Playing {track.title or 'Unknown Track'}")
        self.voice.play(track.get_audio_source(), after=self.next)
        if self.queue.auto_play is not None and self.queue.empty():
            self._bot.dispatch("music_auto_play", self)

        await self.queue.wait()
        await self.set_status(None)

        if self.queue.queue_loop:
            await self.queue.put(track)

    @audio_loop.before_loop
    async def before_audio_loop(self) -> None:
        await self._bot.wait_until_ready()
        utils.logger.debug(f"Starting Audio Loop (Guild: {self.guild.name})")

    @audio_loop.after_loop
    async def after_audio_loop(self) -> None:
        canceled = self.audio_loop.is_being_cancelled()
        utils.logger.debug(f"Ending Audio Loop (Guild: {self.guild.name}, Canceled: {canceled})")

        self.queue.clear()
        if canceled and self.is_connected() and self.voice.is_playing():
            self.voice.stop()
