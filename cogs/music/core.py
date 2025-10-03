from discord import Color, Embed, Interaction, Member, VoiceState, app_commands
from discord.ext import commands

import utils
from utils.types import CielType

from . import errors
from .embed import QueueEmbed, TrackEmbed, VoiceChannelEmbed
from .model import GoogleSearchTrack, MusicState, YouTubeDLPTrack
from .view import GoogleSearchView, QueueTracksView, QueueView

RETRY_SUGGESTION = 3


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

    @commands.Cog.listener()
    async def on_music_auto_play(self, state: MusicState) -> None:
        for _ in range(RETRY_SUGGESTION):
            if not await state.is_valid():
                return

            state.reset_timer()
            try:
                track = await state.suggestion()
            except utils.GoogleADKError:
                utils.logger.exception("Auto Play Suggestion Error")
                continue
            if not track.url:
                utils.logger.error("Auto Play Suggestion has Invalid Url")
                continue

            if not await state.is_valid():
                embed = TrackEmbed(track=track, title="Cancelled Adding Track (Auto Play)", color=Color.red())
                await state.message.channel.send(embed=embed)
                return

            embed = TrackEmbed(track=track, title="Fetching the Track... (Auto Play)", color=Color.light_grey())
            message = await state.message.channel.send(embed=embed)

            state.reset_timer()
            try:
                track = await track.download()
            except (utils.InvalidAttributeError, errors.YouTubeDLPError):
                utils.logger.exception("Auto Play Download Error")
                continue

            if not await state.is_valid():
                embed = TrackEmbed(track=track, title="Cancelled Adding Track (Auto Play)", color=Color.red())
                await message.edit(embed=embed)
                return

            embed = TrackEmbed(track=track, title="Added to the Queue (Auto Play)", color=Color.green())
            await state.queue.put(track)
            await message.edit(embed=embed)
            return

        state.queue.disable_auto_play()
        embed = Embed(
            title="Failed Adding Track (Auto Play)",
            description="Failed to get a track for auto play.",
            color=Color.red(),
        )
        await state.message.channel.send(embed=embed)

    async def get_connected_state(
        self,
        interaction: Interaction,
        *,
        allow_different_channel: bool = False,
    ) -> MusicState:
        if interaction.guild is None:
            raise errors.UserNotInGuildError

        state = self.states.get(interaction.guild.id)
        if state is None or not state.is_connected():
            raise errors.NotConnectedError
        if not state.audio_loop.is_running():
            raise errors.NotRunningAudioLoopError
        if not await state.is_session_active():
            raise utils.MissingSessionError
        if not allow_different_channel and state.get_voice_channel(interaction) != state.voice.channel:
            raise errors.UserNotInSameChannelError

        return state

    async def get_or_connect_state(
        self,
        interaction: Interaction,
        *,
        allow_same_channel: bool = True,
        allow_edit_message: bool = False,
    ) -> MusicState:
        if interaction.guild is None:
            raise errors.UserNotInGuildError

        state = self.states.get(interaction.guild.id)
        if state is None:
            state = MusicState(self.bot, interaction.guild)
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
        await self.get_or_connect_state(interaction, allow_same_channel=False, allow_edit_message=True)

    @app_commands.command()
    @app_commands.guild_only()
    async def disconnect(self, interaction: Interaction) -> None:
        """Voice Channelから切断"""
        state = await self.get_connected_state(interaction)

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

        state = await self.get_or_connect_state(interaction)
        state.reset_timer()

        track = await YouTubeDLPTrack.download(interaction.user, url)
        if not await state.is_valid():
            embed = TrackEmbed(track=track, title="Cancelled Adding Track", color=Color.red())
            await interaction.followup.send(embed=embed, ephemeral=True)
            await interaction.delete_original_response()
            return

        embed = TrackEmbed(track=track, title="Added to the Queue", color=Color.green())
        await state.queue.put(track)
        await interaction.edit_original_response(embed=embed)

    @app_commands.command(name="search-top")
    @app_commands.describe(word="検索ワード")
    @app_commands.guild_only()
    async def search_top(self, interaction: Interaction, word: str) -> None:
        """YouTubeで曲を検索してキューに追加"""
        embed = Embed(title="Searching...", color=Color.light_grey())
        await interaction.response.send_message(embed=embed)

        state = await self.get_or_connect_state(interaction)
        state.reset_timer()
        track = await GoogleSearchTrack.search_top(interaction.user, word)
        if not await state.is_valid():
            embed = TrackEmbed(track=track, title="Cancelled Adding Track", color=Color.red())
            await interaction.followup.send(embed=embed, ephemeral=True)
            await interaction.delete_original_response()
            return

        embed = TrackEmbed(track=track, title="Fetching the Track...", color=Color.light_grey())
        await interaction.edit_original_response(embed=embed)

        state.reset_timer()
        track = await track.download()
        if not await state.is_valid():
            embed = TrackEmbed(track=track, title="Cancelled Adding Track", color=Color.red())
            await interaction.followup.send(embed=embed, ephemeral=True)
            await interaction.delete_original_response()
            return

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
        state = await self.get_or_connect_state(interaction)
        state.reset_timer()

        view = await GoogleSearchView(interaction, state, word).search()
        embed = view.set_embed(title=f'Search Results for "{word}"', color=Color.light_grey())
        await interaction.edit_original_response(embed=embed, view=view)

    @app_commands.command()
    @app_commands.guild_only()
    async def skip(self, interaction: Interaction) -> None:
        """再生中の曲をスキップ"""
        state = await self.get_connected_state(interaction)

        track = await state.skip()
        embed = TrackEmbed(track=track, title="Skipped Now Playing", color=Color.green())
        await interaction.response.send_message(embed=embed)

    @app_commands.command()
    @app_commands.guild_only()
    async def loop(self, interaction: Interaction) -> None:
        """キューのループ再生を切り替え"""
        state = await self.get_connected_state(interaction)

        if state.queue.toggle():
            embed = QueueEmbed(state.queue, title="Loop Enabled", color=Color.green())
        else:
            embed = QueueEmbed(state.queue, title="Loop Disabled", color=Color.red())
        await interaction.response.send_message(embed=embed)

    @app_commands.command()
    @app_commands.guild_only()
    async def queue(self, interaction: Interaction) -> None:
        """キューの情報を表示"""
        state = await self.get_connected_state(interaction, allow_different_channel=True)

        view = QueueView(interaction, state)
        embed = view.set_embed(title=f"Queue for {interaction.guild.name}", color=Color.blue())  # pyright: ignore[reportOptionalMemberAccess]
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command()
    @app_commands.guild_only()
    async def track(self, interaction: Interaction) -> None:
        """キューの詳細情報を表示"""
        state = await self.get_connected_state(interaction, allow_different_channel=True)

        view = QueueTracksView(interaction, state)
        embed = view.set_embed(color=Color.blue())
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @app_commands.command()
    @app_commands.guild_only()
    @app_commands.describe(word="自動再生のキーワード (未指定で無効化)")
    async def autoplay(self, interaction: Interaction, word: str = "") -> None:
        """自動再生のキーワードを設定"""
        embed = Embed(title="Setting Auto Play...", color=Color.light_grey())
        await interaction.response.send_message(embed=embed)
        state = await self.get_or_connect_state(interaction)

        if word:
            state.queue.enable_auto_play(word)
            self.bot.dispatch("music_auto_play", state)
            embed = QueueEmbed(state.queue, title="Auto Play Enabled", color=Color.green())
        else:
            state.queue.disable_auto_play()
            embed = QueueEmbed(state.queue, title="Auto Play Disabled", color=Color.red())
        await interaction.edit_original_response(embed=embed)


async def setup(bot: CielType) -> None:
    await bot.add_cog(MusicCog(bot))
