from discord import Color, Interaction, app_commands
from discord.ext import commands

import utils
from utils.types import CielType


class Develop(commands.Cog):
    def __init__(self, bot: CielType) -> None:
        self.bot = bot

    @app_commands.command()
    @utils.developer_only()
    async def extensions(self, interaction: Interaction) -> None:
        """Show All Extensions"""
        embed = utils.ExtensionEmbed.from_client(client=self.bot, title="Extensions", color=Color.blue())
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command()
    @app_commands.describe(extension="Extension name to Reload.")
    @app_commands.describe(sync="Sync Commands after Reloading Extensions.")
    @utils.developer_only()
    async def reload(self, interaction: Interaction, extension: str | None = None, sync: bool = True) -> None:
        """Reload the Specified or All Extensions."""
        embed = utils.ExtensionEmbed.from_client(client=self.bot, title="Reloading...", color=Color.blue())
        await interaction.response.send_message(embed=embed, ephemeral=True)

        if extension is None:
            await self.bot.unload_all_extensions()
            await self.bot.load_all_extensions()
        elif f"cogs.{extension}" in self.bot.extensions:
            await self.bot.reload_extension(f"cogs.{extension}")
        elif f"cogs.{extension}" in self.bot.extension_files():
            await self.bot.load_extension(f"cogs.{extension}")
        else:
            raise commands.ExtensionNotFound(extension)

        if not sync:
            embed = utils.ExtensionEmbed.from_client(client=self.bot, title="Reloaded!", color=Color.green())
            await interaction.edit_original_response(embed=embed)
            return

        embed = utils.ExtensionEmbed.from_client(client=self.bot, title="Syncing...", color=Color.blue())
        await interaction.edit_original_response(embed=embed)
        await self.bot.command_sync()

        embed = utils.ExtensionEmbed.from_client(client=self.bot, title="Reloaded and Synced!", color=Color.green())
        await interaction.edit_original_response(embed=embed)

    @app_commands.command()
    @utils.developer_only()
    async def sync(self, interaction: Interaction) -> None:
        """Sync All Commands"""
        embed = utils.ExtensionEmbed.from_client(client=self.bot, title="Syncing...", color=Color.blue())
        await interaction.response.send_message(embed=embed, ephemeral=True)
        await self.bot.command_sync()

        embed = utils.ExtensionEmbed.from_client(client=self.bot, title="Synced!", color=Color.green())
        await interaction.edit_original_response(embed=embed)


async def setup(bot: CielType) -> None:
    await bot.add_cog(Develop(bot))
