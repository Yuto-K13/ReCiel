from datetime import datetime
from typing import Any

from discord import ClientUser, Color, Member, User
from discord.channel import VocalGuildChannel
from discord.types.embed import EmbedType

import utils

from . import errors
from .model import MusicQueue, Track


class VoiceChannelEmbed(utils.CustomEmbed):
    def __init__(
        self,
        user: User | Member | ClientUser | None,
        before: VocalGuildChannel | None = None,
        after: VocalGuildChannel | None = None,
        reason: str | None = None,
        *,
        colour: int | Color | None = None,
        color: int | Color | None = None,
        title: Any | None = None,  # noqa: ANN401
        type: EmbedType = "rich",  # noqa: A002
        url: Any | None = None,  # noqa: ANN401
        description: Any | None = None,  # noqa: ANN401
        timestamp: datetime | None = None,
    ) -> None:
        if before is None and after is None:
            raise errors.MusicError("Before and After are both None.")

        self.before = before
        self.after = after
        self.reason = reason
        super().__init__(
            user=user,
            title=title,
            colour=colour,
            color=color,
            type=type,
            url=url,
            description=description,
            timestamp=timestamp,
        )

    @property
    def default_title(self) -> str | None:
        if self.before is not None and self.after is not None:
            return "Moved between the Voice Channels"
        if self.before is not None:
            return "Disconnected from the Voice Channel"
        if self.after is not None:
            return "Connected to the Voice Channel"
        return None

    def format_fields(self) -> None:
        channel = None
        if self.before is not None and self.after is not None:
            channel = f"{self.before.mention} -> {self.after.mention}"
        if self.before is not None:
            channel = self.before.mention
        if self.after is not None:
            channel = self.after.mention
        self.add_field(name="Channel", value=channel)

        if self.reason is not None:
            self.add_field(name="Reason", value=self.reason)


class TrackEmbed(utils.CustomEmbed):
    def __init__(
        self,
        track: Track,
        *,
        colour: int | Color | None = None,
        color: int | Color | None = None,
        title: Any | None = None,  # noqa: ANN401
        type: EmbedType = "rich",  # noqa: A002
        url: Any | None = None,  # noqa: ANN401
        description: Any | None = None,  # noqa: ANN401
        timestamp: datetime | None = None,
    ) -> None:
        self.track = track
        super().__init__(
            user=track.user,
            title=title,
            colour=colour,
            color=color,
            type=type,
            url=url,
            description=description,
            timestamp=timestamp,
        )

    @property
    def default_description(self) -> str:
        return self.track.title_markdown

    def format_fields(self) -> None:
        self.add_field(name="Channel", value=self.track.channel_markdown)
        if self.track.duration is not None:
            self.add_field(name="Duration", value=self.track.duration)
        if self.track.thumbnail is not None:
            self.set_thumbnail(url=self.track.thumbnail)

    def format_footer(self) -> None:
        self.set_footer(text=f"Requested by {self.track.user_name}", icon_url=self.track.user_icon)


class QueueEmbed(utils.CustomEmbed):
    def __init__(
        self,
        user: User | Member | ClientUser | None,
        queue: MusicQueue,
        *,
        colour: int | Color | None = None,
        color: int | Color | None = None,
        title: Any | None = None,  # noqa: ANN401
        type: EmbedType = "rich",  # noqa: A002
        url: Any | None = None,  # noqa: ANN401
        description: Any | None = None,  # noqa: ANN401
        timestamp: datetime | None = None,
    ) -> None:
        self.queue = queue
        super().__init__(
            user=user,
            title=title,
            colour=colour,
            color=color,
            type=type,
            url=url,
            description=description,
            timestamp=timestamp,
        )

    def format_fields(self) -> None:
        text = "No Track"
        if self.queue.current is not None:
            self.set_thumbnail(url=self.queue.current.thumbnail)
            text = f"{self.queue.current.title_markdown}\nRequested by **{self.queue.current.user_name}**"
        self.add_field(name="Now Playing", value=text, inline=False)

        lines = [
            f"{track.title_markdown} | Requested by **{track.user_name}**"
            for track in self.queue.all(current=False)
            if track is not None
        ]
        if not lines:
            lines.append("No Track")
        self.add_field(name="Tracks in the Queue", value="\n".join(lines), inline=False)

        queue_loop = "🟢" if self.queue.queue_loop else "🔴"
        auto_play = f"🟢 `{self.queue.auto_play}`" if self.queue.auto_play is not None else "🔴"
        self.add_field(
            name="Queue Status",
            value=f"**Queue Loop**: {queue_loop}, **Auto Play**: {auto_play}",
            inline=False,
        )


class QueueStatusEmbed(utils.CustomEmbed):
    def __init__(
        self,
        user: User | Member | ClientUser | None,
        queue: MusicQueue,
        *,
        colour: int | Color | None = None,
        color: int | Color | None = None,
        title: Any | None = None,  # noqa: ANN401
        type: EmbedType = "rich",  # noqa: A002
        url: Any | None = None,  # noqa: ANN401
        description: Any | None = None,  # noqa: ANN401
        timestamp: datetime | None = None,
    ) -> None:
        self.queue = queue
        super().__init__(
            user=user,
            title=title,
            colour=colour,
            color=color,
            type=type,
            url=url,
            description=description,
            timestamp=timestamp,
        )

    def format_fields(self) -> None:
        queue_loop = "🟢 Enabled" if self.queue.queue_loop else "🔴 Disabled"
        self.add_field(name="Queue Loop", value=queue_loop, inline=False)
        auto_play = f"🟢 Enabled `{self.queue.auto_play}`" if self.queue.auto_play is not None else "🔴 Disabled"
        self.add_field(name="Auto Play", value=auto_play, inline=False)
