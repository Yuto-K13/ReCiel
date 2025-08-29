import os
from typing import Iterator, Optional

from discord import DiscordException, Intents, Message
from discord.ext import commands

from utils import logging

IGNORE_EXTENSION_FILES = ["__init__"]


class Ciel(commands.Bot):
    def __init__(self, intents=Intents.default(), debug: bool = False, **options):
        self.debug = debug
        self.debug_guild = None
        super().__init__(command_prefix="", help_command=None, intents=intents)

    def run(self, token: str = "", **options):
        if not token:
            token = os.getenv("DISCORD_TOKEN", "")
            if self.debug:
                token = os.getenv("DEBUG_DISCORD_TOKEN", token)

        logging.setup_logging(self.debug)
        super().run(token=token, log_handler=None)

    async def load_extension(self, name: str, *, package: Optional[str] = None):
        logging.logger.debug(f"Loading Extension: {name}")
        try:
            await super().load_extension(name, package=package)
        except DiscordException:
            logging.logger.exception(f"Error while Loading Extension: {name}")

    async def unload_extension(self, name: str, *, package: Optional[str] = None):
        logging.logger.debug(f"Unloading Extension: {name}")
        try:
            await super().unload_extension(name, package=package)
        except DiscordException:
            logging.logger.exception(f"Error while Unloading Extension: {name}")

    async def reload_extension(self, name: str, *, package: Optional[str] = None):
        logging.logger.debug(f"Reloading Extension: {name}")
        try:
            await super().reload_extension(name, package=package)
        except DiscordException:
            logging.logger.exception(f"Error while Reloading Extension: {name}")

    def extension_files(self) -> Iterator[str]:
        for f in os.listdir("./cogs"):
            name, ext = os.path.splitext(f)
            if name in IGNORE_EXTENSION_FILES:
                continue
            if ext.lower() == ".py":
                yield f"cogs.{name}"

    async def load_all_extensions(self):
        for name in self.extension_files():
            await self.load_extension(name)

    async def unload_all_extensions(self):
        for name in tuple(self.extensions):
            await self.unload_extension(name)

    async def command_sync(self):
        debug_guild_id = os.getenv("DEBUG_GUILD_ID")
        if self.debug and debug_guild_id:
            try:
                self.debug_guild = await self.fetch_guild(int(debug_guild_id))
            except (ValueError, DiscordException):
                logging.logger.error(f"Invalid DEBUG_GUILD_ID: {debug_guild_id}")
        if self.debug_guild:
            self.tree.copy_global_to(guild=self.debug_guild)
        await self.tree.sync(guild=self.debug_guild)

    async def setup_hook(self):
        await self.load_all_extensions()
        await self.command_sync()

    async def on_ready(self):
        user = self.user.name if self.user else "Unknown"
        debug_status = "Enabled" if self.debug else "Disabled"
        logging.logger.info(f"Ciel Start-up (User: {user}, Debug Mode: {debug_status})")

    async def on_message(self, message: Message):
        pass  # process_commands 関数を無効化
