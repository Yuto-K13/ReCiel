import os
from argparse import ArgumentParser
from typing import Iterator, Optional

import discord
import dotenv
from discord.ext import commands

import utils


class Ciel(commands.Bot):
    IGNORE_EXTENSION_FILES = ["__init__"]

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("command_prefix", "")
        kwargs.setdefault("intents", discord.Intents.default())
        kwargs.setdefault("help_command", None)

        self.debug = kwargs.pop("debug", False)
        super().__init__(*args, **kwargs)

    def run(self, *args, **kwargs):
        token = os.getenv("DISCORD_TOKEN")
        if self.debug:
            token = os.getenv("DEBUG_DISCORD_TOKEN", token)
        kwargs.setdefault("token", token)
        kwargs.setdefault("log_handler", None)
        utils.setup_logging(self.debug)

        super().run(*args, **kwargs)

    async def load_extension(self, name: str, *, package: Optional[str] = None):
        utils.logger.debug(f"Loading Extension: {name}")
        try:
            await super().load_extension(name, package=package)
        except discord.DiscordException:
            utils.logger.exception(f"Error while Loading Extension: {name}")

    async def unload_extension(self, name: str, *, package: Optional[str] = None):
        utils.logger.debug(f"Unloading Extension: {name}")
        try:
            await super().unload_extension(name, package=package)
        except discord.DiscordException:
            utils.logger.exception(f"Error while Unloading Extension: {name}")

    async def reload_extension(self, name: str, *, package: Optional[str] = None):
        utils.logger.debug(f"Reloading Extension: {name}")
        try:
            await super().reload_extension(name, package=package)
        except discord.DiscordException:
            utils.logger.exception(f"Error while Reloading Extension: {name}")

    def extension_files(self) -> Iterator[str]:
        for f in os.listdir("./cogs"):
            name, ext = os.path.splitext(f)
            if name in self.IGNORE_EXTENSION_FILES:
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
            debug_guild = discord.Object(id=int(debug_guild_id))
            self.tree.copy_global_to(guild=debug_guild)
            await self.tree.sync(guild=debug_guild)
        else:
            await self.tree.sync()

    async def setup_hook(self):
        await self.load_all_extensions()
        await self.command_sync()

    async def on_ready(self):
        user = self.user.name if self.user else "Unknown"
        debug_status = "Enabled" if self.debug else "Disabled"
        utils.logger.info(f"Ciel Start-up (User: {user}, Debug Mode: {debug_status})")


if __name__ == "__main__":
    parser = ArgumentParser(description="Generic Discord Bot built with discord.py.")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode.")
    args = parser.parse_args()

    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    dotenv.load_dotenv()

    intents = discord.Intents.default()
    intents.message_content = True
    bot = Ciel(intents=intents, debug=args.debug)
    bot.run()
