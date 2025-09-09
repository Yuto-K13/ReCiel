from discord import Color, Embed, Interaction, app_commands
from discord.ext import commands

import utils
from utils.types import CielType


class General(commands.Cog):
    def __init__(self, bot: CielType) -> None:
        self.bot = bot

    @app_commands.command()
    async def ping(self, interaction: Interaction) -> None:
        """応答速度の表示"""
        latency = self.bot.latency * 1000
        embed = Embed(title="Pong!", color=Color.blue())
        embed.add_field(name="Latency", value=f"{latency:.2f} ms", inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command()
    async def help(self, interaction: Interaction) -> None:
        """コマンドの詳細説明"""
        embed = Embed(title="Help for Ciel", color=Color.blue())
        for cog_name in self.bot.cogs:
            cog = self.bot.get_cog(cog_name)
            if cog is None:
                continue
            lines = []
            for cmd in utils.expand_commands(cog.get_app_commands()):
                if not await utils.check_can_run(cmd, interaction):
                    continue
                app_command = self.bot.tree.get_app_command(cmd)
                if app_command is None:
                    continue

                lines.append(app_command.mention)
                lines.append(f"> {cmd.description}")
                lines.extend([f"> ・ {param.name}: {param.description}" for param in cmd.parameters])
            if lines:
                embed.add_field(name=cog_name, value="\n".join(lines))

        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: CielType) -> None:
    await bot.add_cog(General(bot))
