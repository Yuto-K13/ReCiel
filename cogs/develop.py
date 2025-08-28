from typing import Optional

from discord import Color, Embed, Interaction, app_commands
from discord.ext import commands

from ciel import Ciel
from utils import decorators


class Develop(commands.Cog):
    def __init__(self, bot: Ciel):
        self.bot = bot

    @app_commands.command()
    @decorators.developer_only()
    async def extensions(self, interaction: Interaction):
        """Show All Extensions"""
        extension_files = set(self.bot.extension_files())
        extension_loaded = set(self.bot.extensions)

        embed = Embed(title="Extension Status", colour=Color.blue())
        embed.add_field(
            name="Loaded Extensions",
            value="\n".join(extension_loaded) or "No Extensions",
        )
        embed.add_field(
            name="Not Loaded Extensions",
            value="\n".join(extension_files - extension_loaded) or "No Extensions",
        )
        embed.add_field(
            name="Missing File Extensions",
            value="\n".join(extension_loaded - extension_files) or "No Extensions",
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command()
    @decorators.developer_only()
    async def reload(self, interaction: Interaction, extension: Optional[str] = None):
        """Reload the Specified or All Extensions."""
        embed = Embed(title="Reloading...", colour=Color.blue())
        await interaction.response.send_message(embed=embed, ephemeral=True)

        if extension is None:
            await self.bot.unload_all_extensions()
            await self.bot.load_all_extensions()
        elif f"cogs.{extension}" in self.bot.extensions:
            await self.bot.reload_extension(f"cogs.{extension}")
        elif f"cogs.{extension}" not in self.bot.extension_files():
            await self.bot.load_extension(f"cogs.{extension}")
        else:
            embed = Embed(
                title="Error",
                description=f"Extension 'cogs.{extension}' not found.",
                colour=Color.red(),
            )
            await interaction.edit_original_response(embed=embed)
            return
        await self.bot.command_sync()

        embed = Embed(title="Reloaded!", colour=Color.green())
        await interaction.edit_original_response(embed=embed)


async def setup(bot: Ciel):
    await bot.add_cog(Develop(bot))
