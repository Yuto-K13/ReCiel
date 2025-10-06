from datetime import datetime
from typing import Any, Self

from discord import ButtonStyle, Color, Embed, Interaction
from discord.types.embed import EmbedType
from discord.ui import Button, Item

import utils

from . import errors
from .embed import QueueEmbed, QueueStatusEmbed, TrackEmbed
from .model import GoogleSearchTrack, MusicState, Track


class QueueView(utils.CustomView):
    def __init__(self, interaction: Interaction, state: MusicState) -> None:
        super().__init__(interaction)
        self.state = state
        self.hash = hash(self.state.queue)
        self.items_setup()

    def items_setup(self) -> None:
        self.button_update = Button(label="Update", emoji="🔄", style=ButtonStyle.success)
        self.button_update.callback = self.update
        self.add_item(self.button_update)

        self.button_toggle_loop = Button(label="Toggle Loop", emoji="🔁", style=ButtonStyle.primary)
        self.button_toggle_loop.callback = self.toggle_loop
        self.add_item(self.button_toggle_loop)

        self.button_skip = Button(label="Skip", emoji="❌", style=ButtonStyle.danger)
        self.button_skip.callback = self.skip
        self.add_item(self.button_skip)

        self.button_tracks = Button(label="Show Tracks", emoji="🎵", style=ButtonStyle.secondary, row=1)
        self.button_tracks.callback = self.tracks
        self.add_item(self.button_tracks)

    async def on_error(self, interaction: Interaction, error: Exception, item: Item) -> None:
        self.button_toggle_loop.disabled = True
        self.button_skip.disabled = True
        self.button_tracks.disabled = True
        await self.interaction.edit_original_response(view=self)

        await super().on_error(interaction, error, item)

    @property
    def embed(self) -> Embed:
        return QueueEmbed(self.interaction.user, self.state.queue, **self.embed_kwargs)

    async def update(self, interaction: Interaction) -> None:
        if not self.state.is_connected():
            raise errors.NotConnectedError

        if not interaction.response.is_done():
            await interaction.response.defer()

        if self.hash == hash(self.state.queue):
            return

        self.hash = hash(self.state.queue)

        self.button_toggle_loop.disabled = False
        self.button_tracks.disabled = False

        if not self.state.queue:
            self.button_skip.disabled = True
        else:
            self.button_skip.disabled = False

        await self.interaction.edit_original_response(embed=self.embed, view=self)

    async def toggle_loop(self, interaction: Interaction) -> None:
        if not self.state.is_connected():
            raise errors.NotConnectedError
        if self.hash != hash(self.state.queue):
            raise errors.QueueChangedError

        if self.state.queue.toggle():
            embed = QueueStatusEmbed(
                self.interaction.user,
                self.state.queue,
                title="Queue Loop Enabled",
                color=Color.green(),
            )
        else:
            embed = QueueStatusEmbed(
                self.interaction.user,
                self.state.queue,
                title="Queue Loop Disabled",
                color=Color.red(),
            )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        await self.update(interaction)

    async def skip(self, interaction: Interaction) -> None:
        if not self.state.is_connected():
            raise errors.NotConnectedError
        if self.hash != hash(self.state.queue):
            raise errors.QueueChangedError

        track = await self.state.skip()
        embed = TrackEmbed(track=track, title="Skipped Now Playing", color=Color.green())
        await interaction.response.send_message(embed=embed)
        await self.update(interaction)

    async def tracks(self, interaction: Interaction) -> None:
        if not self.state.is_connected():
            raise errors.NotConnectedError
        if self.hash != hash(self.state.queue):
            raise errors.QueueChangedError

        view = QueueTracksView(interaction, self.state)
        embed = view.set_embed(color=Color.blue())
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


class QueueTracksView(utils.CustomView):
    def __init__(self, interaction: Interaction, state: MusicState) -> None:
        super().__init__(interaction)
        self.user = interaction.user
        self.state = state
        self.hash = hash(self.state.queue)
        self.queue = tuple(self.state.queue.all())
        self.length = len(self.queue)
        self.index = 0
        self.items_setup()

    def items_setup(self) -> None:
        self.button_update = Button(label="Update", emoji="🔄", style=ButtonStyle.success)
        self.button_update.callback = self.update
        self.add_item(self.button_update)

        disabled = self.length == 0
        self.button_remove = Button(label="Skip", emoji="❌", style=ButtonStyle.danger, disabled=disabled)
        self.button_remove.callback = self.remove
        self.add_item(self.button_remove)

        self.button_first = Button(label="First", emoji="⏮️", style=ButtonStyle.primary, disabled=True, row=1)
        self.button_first.callback = self.first
        self.add_item(self.button_first)

        self.button_back = Button(label="Back", emoji="◀️", style=ButtonStyle.primary, disabled=True, row=1)
        self.button_back.callback = self.back
        self.add_item(self.button_back)

        disabled = self.length <= 1
        self.button_next = Button(label="Next", emoji="▶️", style=ButtonStyle.primary, disabled=disabled, row=1)
        self.button_next.callback = self.next
        self.add_item(self.button_next)

        self.button_last = Button(label="Last", emoji="⏭️", style=ButtonStyle.primary, disabled=disabled, row=1)
        self.button_last.callback = self.last
        self.add_item(self.button_last)

    async def on_error(self, interaction: Interaction, error: Exception, item: Item) -> None:
        if isinstance(error, utils.MissingPermissionsError):
            await super().on_error(interaction, error, item)
            return

        self.button_remove.disabled = True
        self.button_first.disabled = True
        self.button_back.disabled = True
        self.button_next.disabled = True
        self.button_last.disabled = True
        await self.interaction.edit_original_response(view=self)

        await super().on_error(interaction, error, item)

    @property
    def track(self) -> Track:
        return self.queue[self.index]

    @property
    def embed(self) -> Embed:
        if not self.queue:
            self.embed_kwargs["title"] = "No Tracks in the Queue"
            return utils.CustomEmbed(self.interaction.user, **self.embed_kwargs)

        if self.index == 0:
            self.embed_kwargs["title"] = "Now Playing"
        else:
            self.embed_kwargs["title"] = f"Tracks in the Queue ({self.index}/{self.length - 1})"
        return TrackEmbed(self.track, **self.embed_kwargs)

    async def update(self, interaction: Interaction) -> None:
        if not self.state.is_connected():
            raise errors.NotConnectedError

        if not interaction.response.is_done():
            await interaction.response.defer()

        if self.hash != hash(self.state.queue):
            self.hash = hash(self.state.queue)
            self.queue = list(self.state.queue.all())
            self.length = len(self.queue)
            self.index = 0

        if self.index <= 0:
            self.button_remove.label = "Skip"
            self.button_remove.emoji = "❌"
            self.button_remove.disabled = self.length == 0

            self.button_first.disabled = True
            self.button_back.disabled = True
        else:
            user = self.track.user
            self.button_remove.label = "Remove"
            self.button_remove.emoji = "🗑️"
            self.button_remove.disabled = not (user is None or user.bot or user == self.user)

            self.button_first.disabled = False
            self.button_back.disabled = False

        if self.index >= self.length - 1:
            self.button_next.disabled = True
            self.button_last.disabled = True
        else:
            self.button_next.disabled = False
            self.button_last.disabled = False

        await self.interaction.edit_original_response(embed=self.embed, view=self)

    def check_validity(self, interaction: Interaction) -> None:
        if not self.state.is_connected():
            raise errors.NotConnectedError
        if self.hash != hash(self.state.queue):
            raise errors.QueueChangedError
        if interaction.user != self.user:
            raise utils.MissingPermissionsError

    async def remove(self, interaction: Interaction) -> None:
        self.check_validity(interaction)

        if self.index == 0:
            track = await self.state.skip()
            embed = TrackEmbed(track=track, title="Skipped Now Playing", color=Color.green())
        else:
            del self.state.queue[self.index - 1]
            utils.logger.info(f"Removed Track (Guild: {self.state.guild.name}, Track: {self.track.title})")
            embed = TrackEmbed(track=self.track, title="Removed from the Queue", color=Color.green())
        await interaction.response.send_message(embed=embed)
        await self.update(interaction)

    async def first(self, interaction: Interaction) -> None:
        self.check_validity(interaction)
        self.index = 0
        await self.update(interaction)

    async def back(self, interaction: Interaction) -> None:
        self.check_validity(interaction)
        self.index -= 1
        await self.update(interaction)

    async def next(self, interaction: Interaction) -> None:
        self.check_validity(interaction)
        self.index += 1
        await self.update(interaction)

    async def last(self, interaction: Interaction) -> None:
        self.check_validity(interaction)
        self.index = self.length - 1
        await self.update(interaction)


class GoogleSearchView(utils.CustomView):
    MAX_RESULTS = 20
    RESULTS = 5

    def __init__(self, interaction: Interaction, state: MusicState, word: str) -> None:
        super().__init__(interaction)
        self.user = interaction.user
        self.state = state
        self.word = word

        self.tracks: list[GoogleSearchTrack] = []
        self.token = ""
        self.length = 0
        self.index = 0
        self.items_setup()

    def items_setup(self) -> None:
        self.button_add = Button(label="Add to Queue", emoji="🎵", style=ButtonStyle.primary)
        self.button_add.callback = self.add
        self.add_item(self.button_add)

        self.button_search = Button(label="Search More", emoji="🔍", style=ButtonStyle.secondary)
        self.button_search.callback = self.search_more
        self.add_item(self.button_search)

        self.button_first = Button(label="First", emoji="⏮️", style=ButtonStyle.primary, disabled=True, row=1)
        self.button_first.callback = self.first
        self.add_item(self.button_first)

        self.button_back = Button(label="Back", emoji="◀️", style=ButtonStyle.primary, disabled=True, row=1)
        self.button_back.callback = self.back
        self.add_item(self.button_back)

        self.button_next = Button(label="Next", emoji="▶️", style=ButtonStyle.primary, row=1)
        self.button_next.callback = self.next
        self.add_item(self.button_next)

        self.button_last = Button(label="Last", emoji="⏭️", style=ButtonStyle.primary, row=1)
        self.button_last.callback = self.last
        self.add_item(self.button_last)

    async def on_error(self, interaction: Interaction, error: Exception, item: Item) -> None:
        if isinstance(error, utils.MissingPermissionsError):
            await super().on_error(interaction, error, item)
            return

        self.button_search.disabled = True
        if not isinstance(error, errors.GoogleAPIError):
            self.button_add.disabled = True
            self.button_first.disabled = True
            self.button_back.disabled = True
            self.button_next.disabled = True
            self.button_last.disabled = True
        await self.interaction.edit_original_response(view=self)

        await super().on_error(interaction, error, item)

    async def search(self) -> Self:
        results = min(self.RESULTS, self.MAX_RESULTS - self.length)
        tracks, token = await GoogleSearchTrack.search(self.user, self.word, results=results, token=self.token)

        self.tracks.extend(tracks)
        self.token = token
        self.length = len(self.tracks)

        if len(tracks) != results:
            raise errors.SearchCountError(len(tracks), results)
        if self.length >= self.MAX_RESULTS:
            self.button_search.disabled = True
        return self

    @property
    def track(self) -> GoogleSearchTrack:
        return self.tracks[self.index]

    @property
    def embed(self) -> Embed:
        self.embed_kwargs["title"] = f"{self.title} ({self.index + 1}/{self.length})"
        return TrackEmbed(self.track, **self.embed_kwargs)

    def set_embed(
        self,
        *,
        colour: int | Color | None = None,
        color: int | Color | None = None,
        title: Any | None = None,  # noqa: ANN401
        type: EmbedType = "rich",  # noqa: A002
        url: Any | None = None,  # noqa: ANN401
        description: Any | None = None,  # noqa: ANN401
        timestamp: datetime | None = None,
    ) -> Embed:
        self.title = title or "Search Results"
        return super().set_embed(
            colour=colour,
            color=color,
            title=title,
            type=type,
            url=url,
            description=description,
            timestamp=timestamp,
        )

    async def update(self, interaction: Interaction) -> None:
        if not self.state.is_connected():
            raise errors.NotConnectedError

        if not interaction.response.is_done():
            await interaction.response.defer()

        if self.index <= 0:
            self.button_first.disabled = True
            self.button_back.disabled = True
        else:
            self.button_first.disabled = False
            self.button_back.disabled = False

        if self.index >= self.length - 1:
            self.button_next.disabled = True
            self.button_last.disabled = True
        else:
            self.button_next.disabled = False
            self.button_last.disabled = False

        await self.interaction.edit_original_response(embed=self.embed, view=self)

    def check_validity(self, interaction: Interaction) -> None:
        if not self.state.is_connected():
            raise errors.NotConnectedError
        if interaction.user != self.user:
            raise utils.MissingPermissionsError

    async def add(self, interaction: Interaction) -> None:
        self.check_validity(interaction)

        embed = TrackEmbed(self.track, title="Fetching the Track...", color=Color.light_grey())
        await interaction.response.send_message(embed=embed)

        self.state.reset_timer()
        track = await self.track.download()
        embed = TrackEmbed(track=track, title="Added to the Queue", color=Color.green())

        await self.state.add_track(track)
        await interaction.edit_original_response(embed=embed)

    async def search_more(self, interaction: Interaction) -> None:
        self.check_validity(interaction)
        await interaction.response.defer()

        await self.search()
        await self.update(interaction)

    async def first(self, interaction: Interaction) -> None:
        self.check_validity(interaction)
        self.index = 0
        await self.update(interaction)

    async def back(self, interaction: Interaction) -> None:
        self.check_validity(interaction)
        self.index -= 1
        await self.update(interaction)

    async def next(self, interaction: Interaction) -> None:
        self.check_validity(interaction)
        self.index += 1
        await self.update(interaction)

    async def last(self, interaction: Interaction) -> None:
        self.check_validity(interaction)
        self.index = self.length - 1
        await self.update(interaction)
