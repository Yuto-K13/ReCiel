import inspect
import os
from collections.abc import Iterator
from pathlib import Path

from discord import DiscordException, Intents, Interaction, Message, app_commands
from discord.abc import Snowflake
from discord.app_commands import AppCommand, AppCommandGroup, Argument, Command, Group
from discord.ext import commands

import utils

IGNORE_EXTENSION_FILES = ["__init__"]


class CielTree(app_commands.CommandTree):
    def __init__(self, *args, **kwargs) -> None:  # noqa: ANN002, ANN003
        super().__init__(*args, **kwargs)
        self._command_map: dict[Command, AppCommand | AppCommandGroup] = {}

    async def sync(self, *, guild: Snowflake | None = None) -> list[AppCommand]:
        utils.logger.debug(f"Syncing Commands (Guild: {guild})")
        app_cmds = await super().sync(guild=guild)
        cmds = self.get_commands(guild=guild)
        self._map_commands(cmds, app_cmds)
        return app_cmds

    async def sync_all(self) -> dict[int | None, list[AppCommand]]:
        self._command_map.clear()
        app_cmds_map = {}
        if self.get_commands(guild=None):
            app_cmds_map[None] = await self.sync(guild=None)
        for guild_id in self._guild_commands:
            guild = await self.client.fetch_guild(guild_id)
            if self.get_commands(guild=guild):
                app_cmds_map[guild_id] = await self.sync(guild=guild)
        return app_cmds_map

    def _map_commands(self, commands: list[Command | Group], app_commands: list[AppCommand | AppCommandGroup]) -> None:
        for command in commands:
            for app_command in app_commands:
                if isinstance(app_command, Argument):
                    continue
                if command.name == app_command.name:
                    break
            else:
                continue
            if isinstance(command, Group):
                self._map_commands(command.commands, app_command.options)
                continue

            self._command_map[command] = app_command

    async def map_commands(self, guild: Snowflake | None = None) -> None:
        commands = self.get_commands(guild=guild)
        app_commands = await self.fetch_commands(guild=guild)
        self._map_commands(commands, app_commands)

    async def map_all_commands(self) -> None:
        await self.map_commands(guild=None)
        for guild_id in self._guild_commands:
            guild = await self.client.fetch_guild(guild_id)
            await self.map_commands(guild=guild)

    def get_app_command(self, command: Command) -> AppCommand | AppCommandGroup | None:
        return self._command_map.get(command)

    async def check_can_run(self, command: Command, interaction: Interaction) -> bool:
        for check in command.checks:
            try:
                result = check(interaction)
                if inspect.isawaitable(result):
                    result = await result
            except app_commands.AppCommandError:
                return False
            if not result:
                return False
        return True


class Ciel(commands.Bot):
    tree: CielTree  # pyright: ignore[reportIncompatibleMethodOverride]

    def __init__(self, intents: Intents | None = None, debug: bool = False, **options) -> None:  # noqa: ANN003, ARG002
        if intents is None:
            intents = Intents.default()
        super().__init__(command_prefix="", help_command=None, tree_cls=CielTree, intents=intents)
        self.debug = debug
        self.debug_guild = None

    def run(self, token: str = "", **options) -> None:  # noqa: ANN003, ARG002
        if not token:
            token = os.getenv("DISCORD_TOKEN", "")
            if self.debug:
                token = os.getenv("DEBUG_DISCORD_TOKEN", token)

        utils.setup_logging(self.debug)
        super().run(token=token, log_handler=None)

    async def load_extension(self, name: str, *, package: str | None = None) -> None:
        utils.logger.debug(f"Loading Extension: {name}")
        try:
            await super().load_extension(name, package=package)
        except DiscordException:
            utils.logger.exception(f"Error while Loading Extension: {name}")

    async def unload_extension(self, name: str, *, package: str | None = None) -> None:
        utils.logger.debug(f"Unloading Extension: {name}")
        try:
            await super().unload_extension(name, package=package)
        except DiscordException:
            utils.logger.exception(f"Error while Unloading Extension: {name}")

    async def reload_extension(self, name: str, *, package: str | None = None) -> None:
        utils.logger.debug(f"Reloading Extension: {name}")
        try:
            await super().reload_extension(name, package=package)
        except DiscordException:
            utils.logger.exception(f"Error while Reloading Extension: {name}")

    def extension_files(self) -> Iterator[str]:
        cogs_path = Path("./cogs")
        for file_path in cogs_path.iterdir():
            if not file_path.is_file():
                continue
            name, ext = file_path.stem, file_path.suffix
            if name in IGNORE_EXTENSION_FILES:
                continue
            if ext.lower() == ".py":
                yield f"cogs.{name}"

    async def load_all_extensions(self) -> None:
        for name in self.extension_files():
            await self.load_extension(name)

    async def unload_all_extensions(self) -> None:
        for name in tuple(self.extensions):
            await self.unload_extension(name)

    async def command_sync(self) -> None:
        if self.debug and self.debug_guild:
            self.tree.copy_global_to(guild=self.debug_guild)
            self.tree.clear_commands(guild=None)
            await self.tree.sync(guild=self.debug_guild)
            return
        await self.tree.sync_all()

    async def setup_hook(self) -> None:
        await self.load_all_extensions()
        if self.debug:
            debug_guild_id = os.getenv("DEBUG_GUILD_ID")
            try:
                self.debug_guild = await self.fetch_guild(int(debug_guild_id))  # pyright: ignore[reportArgumentType]
            except (ValueError, DiscordException):
                utils.logger.exception(f"Couldn't Fetch Guild (ID: {debug_guild_id})")
                raise
            self.tree.copy_global_to(guild=self.debug_guild)
            self.tree.clear_commands(guild=None)

        await self.tree.map_all_commands()

    async def on_ready(self) -> None:
        user = self.user.name if self.user else "Unknown"
        debug_status = "Enabled" if self.debug else "Disabled"
        utils.logger.info(f"Ciel Start-up (User: {user}, Debug Mode: {debug_status})")

    async def on_message(self, message: Message) -> None:
        pass  # process_commands 関数を無効化
