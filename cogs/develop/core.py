from discord import Color, Embed, Interaction, app_commands
from discord.enums import AppCommandType
from discord.ext import commands

import utils
from utils.types import CielType

from .embed import CommandMapEmbed, ExtensionEmbed


class DevelopCog(commands.Cog, name="Develop"):
    def __init__(self, bot: CielType) -> None:
        self.bot = bot

    @app_commands.command()
    @utils.developer_only()
    async def extensions(self, interaction: Interaction) -> None:
        """Show All Extensions."""
        embed = ExtensionEmbed(client=self.bot, title="Extensions", color=Color.dark_grey())
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command()
    @app_commands.describe(extension="Extension name to Reload.")
    @app_commands.describe(sync="Sync Commands after Reloading Extensions.")
    @utils.developer_only()
    async def reload(self, interaction: Interaction, extension: str | None = None, sync: bool = True) -> None:
        """Reload the Specified or All Extensions."""
        embed = ExtensionEmbed(client=self.bot, title="Reloading...", color=Color.light_grey())
        await interaction.response.send_message(embed=embed, ephemeral=True)

        if extension is None:
            await self.bot.unload_all_extensions()
            await self.bot.load_all_extensions()
        elif f"cogs.{extension}" in self.bot.extensions:
            await self.bot.reload_extension(f"cogs.{extension}")
        elif f"cogs.{extension}" in self.bot.extension_files():
            await self.bot.load_extension(f"cogs.{extension}")
        else:
            raise utils.ExtensionNotFoundError(extension)

        if not sync:
            await self.bot.command_map()
            embed = ExtensionEmbed(client=self.bot, title="Reloaded!", color=Color.green())
            await interaction.edit_original_response(embed=embed)
            return

        embed = ExtensionEmbed(client=self.bot, title="Syncing...", color=Color.light_grey())
        await interaction.edit_original_response(embed=embed)
        await self.bot.command_sync()

        embed = ExtensionEmbed(client=self.bot, title="Reloaded and Synced!", color=Color.green())
        await interaction.edit_original_response(embed=embed)

    @app_commands.command()
    @app_commands.describe(force="Sync All Global/Guild Commands Forcefully while running in Develop Mode.")
    @utils.developer_only()
    async def sync(self, interaction: Interaction, force: bool = False) -> None:
        """Sync All Commands."""
        embed = CommandMapEmbed(client=self.bot, title="Syncing...", color=Color.light_grey())
        await interaction.response.send_message(embed=embed, ephemeral=True)
        await self.bot.command_sync(force=force)

        embed = CommandMapEmbed(client=self.bot, title="Synced!", color=Color.green())
        await interaction.edit_original_response(embed=embed)

    @app_commands.command()
    @utils.developer_only()
    async def register(self, interaction: Interaction) -> None:
        """Register All Commands for Command Map."""
        embed = CommandMapEmbed(client=self.bot, title="Registering...", color=Color.light_grey())
        await interaction.response.send_message(embed=embed, ephemeral=True)
        await self.bot.command_map()

        embed = CommandMapEmbed(client=self.bot, title="Registered!", color=Color.green())
        await interaction.edit_original_response(embed=embed)

    @app_commands.command()
    @utils.developer_only()
    async def map(self, interaction: Interaction) -> None:
        """Show Command Map."""
        embed = CommandMapEmbed(client=self.bot, title="Command Map", color=Color.dark_grey())
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command()
    @utils.developer_only()
    async def commands(self, interaction: Interaction) -> None:
        """Show All Commands for each Guild."""
        embed = Embed(title="Command List", color=Color.dark_grey())
        for guild in (None, *self.bot.guilds):
            app_cmds = utils.expand_commands(await self.bot.tree.fetch_commands(guild=guild))
            app_cmds = {app_cmd for app_cmd in app_cmds if app_cmd.type == AppCommandType.chat_input}
            cmds = self.bot.tree.get_commands(guild=guild, type=AppCommandType.chat_input)

            lines = []
            for cmd in utils.expand_commands(cmds):
                app_cmd = self.bot.tree.get_app_command(cmd)
                if app_cmd is not None:
                    lines.append(f"`{cmd.qualified_name}` -> {app_cmd.mention}")
                    app_cmds.discard(app_cmd)
                else:
                    lines.append(f"`{cmd.qualified_name}` -> None")
            if app_cmds:
                lines.append("--- Unknown AppCommands ---")
                lines.extend([app_cmd.mention for app_cmd in sorted(app_cmds, key=lambda c: c.name)])

            if lines:
                guild_name = guild.name if guild is not None else "Global"
                embed.add_field(name=guild_name, value="\n".join(lines))

        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: CielType) -> None:
    await bot.add_cog(DevelopCog(bot))
