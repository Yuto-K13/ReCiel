from discord import ButtonStyle, Color, Embed, Interaction
from discord.ui import Button, Item

import utils

from . import error
from .embed import QueueEmbed, TrackEmbed
from .model import MusicState, Track


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
        return QueueEmbed(self.state.queue, **self.embed_kwargs)

    async def update(self, interaction: Interaction) -> None:
        if not self.state.is_connected():
            raise error.NotConnectedError

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
            raise error.NotConnectedError
        if self.hash != hash(self.state.queue):
            raise error.QueueChangedError

        if self.state.queue.toggle():
            embed = Embed(title="Loop Enabled", color=Color.green())
        else:
            embed = Embed(title="Loop Disabled", color=Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=True)
        await self.update(interaction)

    async def skip(self, interaction: Interaction) -> None:
        if not self.state.is_connected():
            raise error.NotConnectedError
        if self.hash != hash(self.state.queue):
            raise error.QueueChangedError

        track = self.state.skip()
        embed = TrackEmbed(track=track, title="Skipped Now Playing", color=Color.green())
        await interaction.response.send_message(embed=embed)
        await self.update(interaction)

    async def tracks(self, interaction: Interaction) -> None:
        if not self.state.is_connected():
            raise error.NotConnectedError
        if self.hash != hash(self.state.queue):
            raise error.QueueChangedError

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
            return Embed(**self.embed_kwargs)

        if self.index == 0:
            self.embed_kwargs["title"] = "Now Playing"
        else:
            self.embed_kwargs["title"] = f"Tracks in the Queue ({self.index}/{self.length - 1})"
        return TrackEmbed(self.track, **self.embed_kwargs)

    async def update(self, interaction: Interaction) -> None:
        if not self.state.is_connected():
            raise error.NotConnectedError

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
            self.button_remove.label = "Remove"
            self.button_remove.emoji = "🗑️"
            self.button_remove.disabled = self.track.user != self.user

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
            raise error.NotConnectedError
        if self.hash != hash(self.state.queue):
            raise error.QueueChangedError
        if interaction.user != self.user:
            raise utils.MissingPermissionsError

    async def remove(self, interaction: Interaction) -> None:
        self.check_validity(interaction)

        if self.index == 0:
            track = self.state.skip()
            embed = TrackEmbed(track=track, title="Skipped Now Playing", color=Color.green())
        else:
            del self.state.queue[self.index - 1]
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
        self.index = len(self.queue) - 1
        await self.update(interaction)
