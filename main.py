import os

import discord
import dotenv
from discord.ext import commands


class Ciel(commands.Bot):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("command_prefix", "")
        kwargs.setdefault("intents", discord.Intents.default())
        kwargs.setdefault("help_command", None)
        super().__init__(*args, **kwargs)

    def run(self, *args, **kwargs):
        kwargs["token"] = os.getenv("DISCORD_TOKEN")
        super().run(*args, **kwargs)

    async def on_ready(self):
        print("Ciel Start-up")


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    dotenv.load_dotenv()
    bot = Ciel()
    bot.run()
