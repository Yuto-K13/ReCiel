import os
from typing import Iterator

import discord
import dotenv
from discord.ext import commands


class Ciel(commands.Bot):
    IGNORE_EXTENSION_FILES = ["__init__"]

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("command_prefix", "")
        kwargs.setdefault("intents", discord.Intents.default())
        kwargs.setdefault("help_command", None)
        super().__init__(*args, **kwargs)

    def run(self, *args, **kwargs):
        kwargs["token"] = os.getenv("DISCORD_TOKEN")
        super().run(*args, **kwargs)

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

    async def setup_hook(self):
        await self.load_all_extensions()

    async def on_ready(self):
        print("Ciel Start-up")


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    dotenv.load_dotenv()
    bot = Ciel()
    bot.run()
