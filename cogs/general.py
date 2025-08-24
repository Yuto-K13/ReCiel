import discord
from discord import Color, Embed, Interaction, app_commands
from discord.ext import commands

from main import Ciel


class General(commands.Cog):
    def __init__(self, bot: Ciel):
        self.bot = bot

    @app_commands.command()
    async def ping(self, interaction: Interaction):
        """応答速度の表示"""
        latency = self.bot.latency * 1000
        embed = Embed(title="Pong!", color=Color.blue())
        embed.add_field(name="Latency", value=f"{latency:.2f} ms", inline=False)
        await interaction.response.send_message(embed=embed)


async def setup(bot: Ciel):
    await bot.add_cog(General(bot))
