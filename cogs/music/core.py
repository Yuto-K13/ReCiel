from typing import Literal, overload

from discord import Color, Embed, Interaction, Member, VoiceState, app_commands
from discord.ext import commands

from utils.types import CielType

from . import errors
from .embed import QueueEmbed, TrackEmbed, VoiceChannelEmbed
from .model import GoogleSearchTrack, MusicState, YouTubeDLPTrack
from .view import GoogleSearchView, QueueTracksView, QueueView


class MusicCog(commands.Cog, name="Music"):
    def __init__(self, bot: CielType) -> None:
        self.bot = bot
        self.states: dict[int, MusicState] = {}

    async def cog_unload(self) -> None:
        for state in self.states.values():
            if not state.is_connected():
                continue

            embed = VoiceChannelEmbed(
                before=state.voice.channel,
                user=self.bot.user,
                reason="Unload Cog.",
                color=Color.green(),
            )
            await state.disconnect()
            await state.message.reply(embed=embed)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: Member, before: VoiceState, after: VoiceState) -> None:  # noqa: ARG002
        if before.channel is None:
            return

        state = self.states.get(before.channel.guild.id)
        if state is None:
            return
        if not state.is_connected():
            state.cancel()
            return
        for user in state.voice.channel.members:
            if not user.bot:
                return

        embed = VoiceChannelEmbed(
            before=state.voice.channel,
            user=self.bot.user,
            reason="All Users have Left.",
            color=Color.green(),
        )
        await state.disconnect()
        await state.message.reply(embed=embed)

    @commands.Cog.listener()
    async def on_music_timeout(self, state: MusicState) -> None:
        if not state.is_connected():
            return

        embed = VoiceChannelEmbed(
            before=state.voice.channel,
            user=self.bot.user,
            reason="Timeout.",
            color=Color.green(),
        )
        await state.disconnect()
        await state.message.reply(embed=embed)

    @overload
    async def get_state(
        self,
        interaction: Interaction,
        *,
        allow_connect: Literal[True] = ...,
        allow_same_channel: bool = ...,
        allow_edit_message: bool = ...,
    ) -> MusicState: ...

    @overload
    async def get_state(
        self,
        interaction: Interaction,
        *,
        allow_connect: Literal[False] = ...,
        allow_same_channel: bool = ...,
        allow_edit_message: bool = ...,
    ) -> MusicState | None: ...

    async def get_state(
        self,
        interaction: Interaction,
        *,
        allow_connect: bool = True,
        allow_same_channel: bool = True,
        allow_edit_message: bool = False,
    ) -> MusicState | None:
        if interaction.guild is None:
            raise errors.UserNotInGuildError
        state = self.states.get(interaction.guild.id)
        if not allow_connect:
            return state

        embed = None
        if state is None:
            state = MusicState(self.bot)
            self.states[interaction.guild.id] = state

        if not state.is_connected():
            await state.connect(interaction)
            embed = VoiceChannelEmbed(
                after=state.voice.channel,
                user=interaction.user,
                color=Color.green(),
            )
        elif state.get_voice_channel(interaction) != state.voice.channel:
            before = state.voice.channel
            await state.move(interaction)
            embed = VoiceChannelEmbed(
                before=before,
                after=state.voice.channel,
                user=interaction.user,
                color=Color.green(),
            )
        elif not allow_same_channel:
            raise errors.AlreadyConnectedError
        else:
            return state

        if not interaction.response.is_done():
            await interaction.response.send_message(embed=embed)
            message = await interaction.original_response()
        elif allow_edit_message:
            message = await interaction.edit_original_response(embed=embed)
        else:
            message = await interaction.followup.send(embed=embed, wait=True)
        state.message = message
        return state

    @app_commands.command()
    @app_commands.guild_only()
    async def connect(self, interaction: Interaction) -> None:
        """Voice Channelに接続"""
        embed = Embed(title="Connecting...", color=Color.light_grey())
        await interaction.response.send_message(embed=embed)
        await self.get_state(interaction, allow_same_channel=False, allow_edit_message=True)

    @app_commands.command()
    @app_commands.guild_only()
    async def disconnect(self, interaction: Interaction) -> None:
        """Voice Channelから切断"""
        state = await self.get_state(interaction, allow_connect=False)
        if state is None or not state.is_connected():
            raise errors.NotConnectedError
        if state.get_voice_channel(interaction) != state.voice.channel:
            raise errors.UserNotInSameChannelError

        channel = state.voice.channel
        await state.disconnect()
        embed = VoiceChannelEmbed(before=channel, user=interaction.user, color=Color.green())
        await interaction.response.send_message(embed=embed)

    @app_commands.command()
    @app_commands.describe(url="再生したい動画のURL")
    @app_commands.guild_only()
    async def play(self, interaction: Interaction, url: str) -> None:
        """URLから曲をキューに追加"""
        embed = Embed(title="Fetching...", color=Color.light_grey())
        await interaction.response.send_message(embed=embed)

        state = await self.get_state(interaction)
        await state.reset_timer()

        track = await YouTubeDLPTrack.download(interaction.user, url)
        embed = TrackEmbed(track=track, title="Added to the Queue", color=Color.green())
        await state.queue.put(track)
        await interaction.edit_original_response(embed=embed)

    @app_commands.command()
    @app_commands.describe(word="検索ワード")
    @app_commands.guild_only()
    async def search(self, interaction: Interaction, word: str) -> None:
        """YouTubeで曲を検索してキューに追加"""
        embed = Embed(title="Searching...", color=Color.light_grey())
        await interaction.response.send_message(embed=embed)

        state = await self.get_state(interaction)
        await state.reset_timer()

        track = await GoogleSearchTrack.search(interaction.user, word)
        embed = TrackEmbed(track=track, title="Fetching the Track...", color=Color.light_grey())
        await interaction.edit_original_response(embed=embed)
        await state.reset_timer()

        track = await track.download()
        embed = TrackEmbed(track=track, title="Added to the Queue", color=Color.green())
        await state.queue.put(track)
        await interaction.edit_original_response(embed=embed)

    @app_commands.command(name="search-all")
    @app_commands.describe(word="検索ワード")
    @app_commands.guild_only()
    async def search_all(self, interaction: Interaction, word: str) -> None:
        """YouTubeで曲を検索した結果を選択してキューに追加"""
        embed = Embed(title="Searching...", color=Color.light_grey())
        await interaction.response.send_message(embed=embed, ephemeral=True)
        state = await self.get_state(interaction)
        await state.reset_timer()

        view = await GoogleSearchView(interaction, state, word).search()
        embed = view.set_embed(title=f'Search Results for "{word}"', color=Color.light_grey())
        await interaction.edit_original_response(embed=embed, view=view)

    @app_commands.command()
    @app_commands.guild_only()
    async def skip(self, interaction: Interaction) -> None:
        """再生中の曲をスキップ"""
        state = await self.get_state(interaction, allow_connect=False)
        if state is None or not state.is_connected():
            raise errors.NotConnectedError
        if state.get_voice_channel(interaction) != state.voice.channel:
            raise errors.UserNotInSameChannelError

        track = state.skip()
        embed = TrackEmbed(track=track, title="Skipped Now Playing", color=Color.green())
        await interaction.response.send_message(embed=embed)

    @app_commands.command()
    @app_commands.guild_only()
    async def loop(self, interaction: Interaction) -> None:
        """キューのループ再生を切り替え"""
        state = await self.get_state(interaction, allow_connect=False)
        if state is None or not state.is_connected():
            raise errors.NotConnectedError
        if state.get_voice_channel(interaction) != state.voice.channel:
            raise errors.UserNotInSameChannelError

        if state.queue.toggle():
            embed = QueueEmbed(state.queue, title="Loop Enabled", color=Color.green())
        else:
            embed = QueueEmbed(state.queue, title="Loop Disabled", color=Color.red())
        await interaction.response.send_message(embed=embed)

    @app_commands.command()
    @app_commands.guild_only()
    async def queue(self, interaction: Interaction) -> None:
        """キューの情報を表示"""
        state = await self.get_state(interaction, allow_connect=False)
        if state is None or not state.is_connected():
            raise errors.NotConnectedError

        view = QueueView(interaction, state)
        embed = view.set_embed(title=f"Queue for {interaction.guild.name}", color=Color.blue())  # pyright: ignore[reportOptionalMemberAccess]
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command()
    @app_commands.guild_only()
    async def track(self, interaction: Interaction) -> None:
        """キューの詳細情報を表示"""
        state = await self.get_state(interaction, allow_connect=False)
        if state is None or not state.is_connected():
            raise errors.NotConnectedError

        view = QueueTracksView(interaction, state)
        embed = view.set_embed(color=Color.blue())
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


async def setup(bot: CielType) -> None:
    await bot.add_cog(MusicCog(bot))
