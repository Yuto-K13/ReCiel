from datetime import datetime
from typing import Any

from discord import ClientUser, Color, Embed, Member, User
from discord.channel import VocalGuildChannel
from discord.types.embed import EmbedType

from . import errors
from .model import MusicQueue, Track


class VoiceChannelEmbed(Embed):
    def __init__(
        self,
        before: VocalGuildChannel | None = None,
        after: VocalGuildChannel | None = None,
        reason: str | None = None,
        user: ClientUser | User | Member | None = None,
        *,
        colour: int | Color | None = None,
        color: int | Color | None = None,
        title: Any | None = None,  # noqa: ANN401
        type: EmbedType = "rich",  # noqa: A002
        url: Any | None = None,  # noqa: ANN401
        description: Any | None = None,  # noqa: ANN401
        timestamp: datetime | None = None,
    ) -> None:
        self.before = before
        self.after = after
        self.user = user
        self.reason = reason
        super().__init__(
            title=title,
            colour=colour,
            color=color,
            type=type,
            url=url,
            description=description,
            timestamp=timestamp,
        )
        self.format()

    def format(self) -> None:
        if self.before is not None and self.after is not None:
            title = "Moved between the Voice Channels"
            channel = f"{self.before.mention} -> {self.after.mention}"
        elif self.before is not None:
            title = "Disconnected from the Voice Channel"
            channel = self.before.mention
        elif self.after is not None:
            title = "Connected to the Voice Channel"
            channel = self.after.mention
        else:
            raise errors.MusicError("Before and After are both None.")

        if self.title is None:
            self.title = title
        self.add_field(name="channel", value=channel)

        if self.reason is not None:
            self.add_field(name="Reason", value=self.reason)
        if self.user is not None:
            self.set_footer(text=f"Requested by {self.user.display_name}", icon_url=self.user.display_avatar.url)


class TrackEmbed(Embed):
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
            title=title,
            colour=colour,
            color=color,
            type=type,
            url=url,
            description=description,
            timestamp=timestamp,
        )
        self.format()

    def format(self) -> None:
        if self.description is None:
            self.description = self.track.title_markdown
        self.add_field(name="Channel", value=self.track.channel_markdown)
        if self.track.duration is not None:
            self.add_field(name="Duration", value=self.track.duration)
        if self.track.thumbnail is not None:
            self.set_thumbnail(url=self.track.thumbnail)

        self.set_footer(
            text=f"Requested by {self.track.user.display_name}",
            icon_url=self.track.user.display_avatar.url,
        )


class QueueEmbed(Embed):
    def __init__(
        self,
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
            title=title,
            colour=colour,
            color=color,
            type=type,
            url=url,
            description=description,
            timestamp=timestamp,
        )
        self.format()

    def format(self) -> None:
        text = "No Track"
        if self.queue.current is not None:
            self.set_thumbnail(url=self.queue.current.thumbnail)
            text = f"{self.queue.current.title_markdown}\nRequested by **{self.queue.current.user.display_name}**"
        self.add_field(name="Now Playing", value=text, inline=False)

        lines = [
            f"{track.title_markdown} | Requested by **{track.user.display_name}**"
            for track in self.queue.all(current=False)
            if track is not None
        ]
        if not lines:
            lines.append("No Track")
        self.add_field(name="Tracks in the Queue", value="\n".join(lines), inline=False)

        queue_loop = "✔️" if self.queue.queue_loop else "❌"
        self.set_footer(text=f"Loop: {queue_loop}")
