import os
from collections.abc import Iterable, Iterator, Mapping
from pathlib import Path
from types import MappingProxyType

from discord import DiscordException, Intents, Message, app_commands
from discord.abc import Snowflake
from discord.app_commands import AppCommand, AppCommandGroup, Argument, Command, Group
from discord.enums import AppCommandType
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
        await self.map_commands(guild=guild)
        return app_cmds

    async def sync_all(self) -> dict[int | None, list[AppCommand]]:
        self.clear_command_map()
        app_cmds_map = {}
        if self.get_commands(guild=None):
            app_cmds_map[None] = await self.sync(guild=None)
        for guild_id in self._guild_commands:
            guild = await self.client.fetch_guild(guild_id)
            if self.get_commands(guild=guild):
                app_cmds_map[guild_id] = await self.sync(guild=guild)
        return app_cmds_map

    @property
    def command_map(self) -> Mapping[Command, AppCommand | AppCommandGroup]:
        return MappingProxyType(self._command_map)

    def _mapping(
        self,
        cmds: Iterable[Command | Group],
        app_cmds: Iterable[AppCommand | AppCommandGroup | Argument],
    ) -> None:
        for cmd in cmds:
            for app_cmd in app_cmds:
                if isinstance(app_cmd, Argument):
                    continue
                if app_cmd.type in (AppCommandType.user, AppCommandType.message):
                    continue
                if cmd.name == app_cmd.name:
                    break
            else:
                continue
            if isinstance(cmd, Group):
                self._mapping(cmd.commands, app_cmd.options)
                continue

            self._command_map[cmd] = app_cmd

    async def map_commands(self, guild: Snowflake | None = None) -> None:
        utils.logger.debug(f"Mapping Commands (Guild: {guild})")
        cmds = self.get_commands(guild=guild, type=AppCommandType.chat_input)
        app_cmds = await self.fetch_commands(guild=guild)
        self._mapping(cmds, app_cmds)

    async def map_all_commands(self) -> None:
        self.clear_command_map()
        await self.map_commands(guild=None)
        for guild_id in self._guild_commands:
            guild = await self.client.fetch_guild(guild_id)
            await self.map_commands(guild=guild)

    def clear_command_map(self) -> None:
        utils.logger.debug("Clearing Command Map")
        self._command_map.clear()

    def get_app_command(self, command: Command) -> AppCommand | AppCommandGroup | None:
        return self._command_map.get(command)


class Ciel(commands.Bot):
    tree: CielTree  # pyright: ignore[reportIncompatibleMethodOverride]

    def __init__(self, intents: Intents | None = None, sync: bool = False, develop: bool = False, **options) -> None:  # noqa: ANN003, ARG002
        if intents is None:
            intents = Intents.default()
        super().__init__(command_prefix="", help_command=None, tree_cls=CielTree, intents=intents)
        self.sync = sync
        self.develop = develop
        self.develop_guild = None

    def run(self, token: str = "", **options) -> None:  # noqa: ANN003, ARG002
        if not token:
            token = os.getenv("DISCORD_TOKEN", "")
            if self.develop:
                token = os.getenv("DEVELOP_DISCORD_TOKEN", token)

        utils.setup_logging(self.develop)
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

    async def command_map(self) -> None:
        if self.develop and self.develop_guild:
            self.tree.copy_global_to(guild=self.develop_guild)
            self.tree.clear_commands(guild=None)
        await self.tree.map_all_commands()

    async def command_sync(self) -> None:
        if self.develop and self.develop_guild:
            self.tree.copy_global_to(guild=self.develop_guild)
            self.tree.clear_commands(guild=None)
            await self.tree.sync(guild=self.develop_guild)
            return
        await self.tree.sync_all()

    async def setup_hook(self) -> None:
        await self.load_all_extensions()
        if self.develop:
            develop_guild_id = os.getenv("DEVELOP_GUILD_ID")
            try:
                self.develop_guild = await self.fetch_guild(int(develop_guild_id))  # pyright: ignore[reportArgumentType]
            except (ValueError, DiscordException):
                utils.logger.exception(f"Couldn't Fetch Guild (ID: {develop_guild_id})")
                raise
        if self.sync:  # Develop Mode でも Global Command ごと Sync する
            await self.tree.sync_all()
            return

        await self.command_map()

    async def on_ready(self) -> None:
        user = self.user.name if self.user else "Unknown"
        develop_status = "Enabled" if self.develop else "Disabled"
        utils.logger.info(f"Ciel Start-up (User: {user}, Develop Mode: {develop_status})")

    async def on_message(self, message: Message) -> None:
        pass  # process_commands 関数を無効化
