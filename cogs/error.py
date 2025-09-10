from discord import Color, Embed, Interaction, app_commands
from discord.app_commands import AppCommandError
from discord.ext import commands

import utils
from utils.types import CielType


class Error(commands.Cog):
    def __init__(self, bot: CielType) -> None:
        self.bot = bot

    async def on_tree_error(self, interaction: Interaction, error: AppCommandError) -> None:
        embed = utils.ErrorEmbed.from_interaction(client=self.bot, error=error, interaction=interaction)
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=True)
            await interaction.delete_original_response()
            return
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def cog_load(self) -> None:
        self._prev_on_error = self.bot.tree.on_error
        self.bot.tree.on_error = self.on_tree_error

    async def cog_unload(self) -> None:
        self.bot.tree.on_error = self._prev_on_error

    @app_commands.command(name="raise")
    @utils.developer_only()
    async def raise_error(self, interaction: Interaction) -> None:
        """Raise a test error."""
        embed = Embed(title="Raising TestError", color=Color.blue())
        await interaction.response.send_message(embed=embed, ephemeral=True)
        raise utils.CustomError(name="TestError")


async def setup(bot: CielType) -> None:
    await bot.add_cog(Error(bot))
