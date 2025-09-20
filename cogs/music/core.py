from typing import Literal, overload

from discord import Color, Embed, Interaction, Member, VoiceState, app_commands
from discord.ext import commands

from utils.types import CielType

from . import error
from .embed import QueueEmbed, TrackEmbed, VoiceChannelEmbed
from .model import MusicState, YouTubeDLPTrack


class MusicCog(commands.Cog, name="Music"):
    def __init__(self, bot: CielType) -> None:
        self.bot = bot
        self.states: dict[int, MusicState] = {}

    async def cog_unload(self) -> None:
        for state in self.states.values():
            if not state.is_connected():
                continue

            embed = VoiceChannelEmbed(
                before=state.voice_channel,
                user=self.bot.user,
                reason="Unload Cog.",
                color=Color.green(),
            )
            await state.disconnect()
            await state.interaction.followup.send(embed=embed)

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
        for user in state.voice_channel.members:
            if not user.bot:
                return

        embed = VoiceChannelEmbed(
            before=state.voice_channel,
            user=self.bot.user,
            reason="All Users have Left.",
            color=Color.green(),
        )
        await state.disconnect()
        await state.interaction.followup.send(embed=embed)

    @commands.Cog.listener()
    async def on_music_timeout(self, state: MusicState) -> None:
        if not state.is_connected():
            return

        embed = VoiceChannelEmbed(
            before=state.voice_channel,
            user=self.bot.user,
            reason="Timeout.",
            color=Color.green(),
        )
        await state.disconnect()
        await state.interaction.followup.send(embed=embed)

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
            raise error.UserNotInGuildError
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
                after=state.voice_channel,
                user=interaction.user,
                color=Color.green(),
            )
        elif state.get_voice_channel(interaction) != state.voice_channel:
            before = state.voice_channel
            await state.move(interaction)
            embed = VoiceChannelEmbed(
                before=before,
                after=state.voice_channel,
                user=interaction.user,
                color=Color.green(),
            )
        elif not allow_same_channel:
            raise error.AlreadyConnectedError
        else:
            return state

        if not interaction.response.is_done():
            await interaction.response.send_message(embed=embed)
        elif allow_edit_message:
            await interaction.edit_original_response(embed=embed)
        else:
            await interaction.followup.send(embed=embed)
        return state

    @app_commands.command()
    async def connect(self, interaction: Interaction) -> None:
        """Voice Channelに接続"""
        embed = Embed(title="Connecting...", color=Color.light_grey())
        await interaction.response.send_message(embed=embed)
        await self.get_state(interaction, allow_same_channel=False, allow_edit_message=True)

    @app_commands.command()
    async def disconnect(self, interaction: Interaction) -> None:
        """Voice Channelから切断"""
        state = await self.get_state(interaction, allow_connect=False)
        if state is None or not state.is_connected():
            raise error.NotConnectedError
        if state.get_voice_channel(interaction) != state.voice_channel:
            raise error.UserNotInSameChannelError

        channel = state.voice_channel
        await state.disconnect()
        embed = VoiceChannelEmbed(before=channel, user=interaction.user, color=Color.green())
        await interaction.response.send_message(embed=embed)

    @app_commands.command()
    @app_commands.describe(url="再生したい動画のURL")
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
    async def skip(self, interaction: Interaction) -> None:
        """再生中の曲をスキップ"""
        state = await self.get_state(interaction, allow_connect=False)
        if state is None or not state.is_connected():
            raise error.NotConnectedError
        if state.get_voice_channel(interaction) != state.voice_channel:
            raise error.UserNotInSameChannelError

        track = state.skip()
        embed = TrackEmbed(track=track, title="Skipped Now Playing", color=Color.green())
        await interaction.response.send_message(embed=embed)

    @app_commands.command()
    async def loop(self, interaction: Interaction) -> None:
        """キューのループ再生を切り替え"""
        state = await self.get_state(interaction, allow_connect=False)
        if state is None or not state.is_connected():
            raise error.NotConnectedError
        if state.get_voice_channel(interaction) != state.voice_channel:
            raise error.UserNotInSameChannelError

        if state.queue.toggle():
            embed = QueueEmbed(state.queue, title="Loop Enabled", color=Color.green())
        else:
            embed = QueueEmbed(state.queue, title="Loop Disabled", color=Color.red())
        await interaction.response.send_message(embed=embed)

    @app_commands.command()
    async def queue(self, interaction: Interaction) -> None:
        """キューの詳細情報を表示"""
        state = await self.get_state(interaction, allow_connect=False)
        if state is None or not state.is_connected():
            raise error.NotConnectedError
        embed = QueueEmbed(queue=state.queue, title=f"Queue for {state.guild.name}", color=Color.blue())
        await interaction.response.send_message(embed=embed)


async def setup(bot: CielType) -> None:
    await bot.add_cog(MusicCog(bot))
