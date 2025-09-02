from typing import Optional

from discord import Color, Embed, Interaction, app_commands
from discord.ext import commands

import utils
from ciel import Ciel


class Develop(commands.Cog):
    def __init__(self, bot: Ciel):
        self.bot = bot

    @app_commands.command()
    @utils.developer_only()
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
    @app_commands.describe(extension="Extension name to Reload.")
    @app_commands.describe(sync="Sync Commands after Reloading Extensions.")
    @utils.developer_only()
    async def reload(
        self,
        interaction: Interaction,
        extension: Optional[str] = None,
        sync: bool = True,
    ):
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

        extension_files = set(self.bot.extension_files())
        extension_loaded = set(self.bot.extensions)

        embed = Embed()
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

        if not sync:
            embed.title = "Reloaded!"
            embed.color = Color.green()
            await interaction.edit_original_response(embed=embed)
            return

        embed.title = "Syncing..."
        embed.color = Color.blue()
        await interaction.edit_original_response(embed=embed)
        await self.bot.command_sync()

        embed.title = "Reloaded and Synced!"
        embed.color = Color.green()
        await interaction.edit_original_response(embed=embed)

    @app_commands.command()
    @utils.developer_only()
    async def sync(self, interaction: Interaction):
        """Sync All Commands"""
        embed = Embed(title="Syncing...", colour=Color.blue())
        await interaction.response.send_message(embed=embed, ephemeral=True)
        await self.bot.command_sync()
        extension_files = set(self.bot.extension_files())
        extension_loaded = set(self.bot.extensions)

        embed = Embed(title="Synced!", colour=Color.green())
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
        await interaction.edit_original_response(embed=embed)


async def setup(bot: Ciel):
    await bot.add_cog(Develop(bot))
