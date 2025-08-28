from discord import Color, Embed, Interaction, app_commands
from discord.app_commands import AppCommandError
from discord.ext import commands

from ciel import Ciel
from utils import decorators


class Error(commands.Cog):
    def __init__(self, bot: Ciel):
        self.bot = bot

    async def on_tree_error(self, interaction: Interaction, error: AppCommandError):
        embed = Embed(
            title=error.__class__.__name__,
            description=f"{error}",
            colour=Color.red(),
        )
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=True)
            await interaction.delete_original_response()
            return
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def cog_load(self):
        self._prev_on_error = self.bot.tree.on_error
        self.bot.tree.on_error = self.on_tree_error

    async def cog_unload(self):
        self.bot.tree.on_error = self._prev_on_error

    @app_commands.command(name="raise")
    @decorators.developer_only()
    async def raise_error(self, interaction: Interaction):
        """Raise a test error."""
        embed = Embed(title="Raising AppCommandError", color=Color.blue())
        await interaction.response.send_message(embed=embed, ephemeral=True)
        raise AppCommandError("Test Error")


async def setup(bot: Ciel):
    await bot.add_cog(Error(bot))
