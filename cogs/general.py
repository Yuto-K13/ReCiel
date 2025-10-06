from discord import Color, Interaction, app_commands
from discord.enums import AppCommandType
from discord.ext import commands

import utils
from utils.types import CielType


class GeneralCog(commands.Cog, name="General"):
    def __init__(self, bot: CielType) -> None:
        self.bot = bot

    @app_commands.command()
    async def ping(self, interaction: Interaction) -> None:
        """応答速度の表示"""
        latency = self.bot.latency * 1000
        embed = utils.CustomEmbed(interaction.user, title="Pong!", color=Color.blue())
        embed.add_field(name="Latency", value=f"{latency:.2f} ms", inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command()
    async def help(self, interaction: Interaction) -> None:
        """コマンドの詳細説明"""
        embed = utils.CustomEmbed(interaction.user, title="Help for Ciel", color=Color.blue())
        for cog_name in self.bot.cogs:
            cog = self.bot.get_cog(cog_name)
            if cog is None:
                continue
            lines = []
            for cmd in utils.expand_commands(cog.get_app_commands()):
                if not await utils.can_run_command(cmd, interaction):
                    continue
                app_command = self.bot.tree.get_app_command(cmd)
                if app_command is None:
                    continue

                lines.append(app_command.mention)
                lines.append(f"> {cmd.description}")
                lines.extend([f"> ・ {param.name}: {param.description}" for param in cmd.parameters])
            if lines:
                embed.add_field(name=cog_name, value="\n".join(lines))

        guild = interaction.guild
        for t in (AppCommandType.user, AppCommandType.message):
            ctxs = [f" - {cmd.name}" for cmd in self.bot.tree.get_commands(type=t)]
            guild_ctxs = [f" - {cmd.name}" for cmd in self.bot.tree.get_commands(type=t, guild=guild)]
            ctxs, guild_ctxs = sorted(ctxs), sorted(guild_ctxs)
            if guild is not None and guild_ctxs:
                ctxs.append(f"--- {guild.name} Guild Only ---")
                ctxs.extend(guild_ctxs)
            embed.add_field(name=f"{t.name.title()} Context Menu", value="\n".join(ctxs) or "No Commands")

        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: CielType) -> None:
    await bot.add_cog(GeneralCog(bot))
