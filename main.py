import os
from argparse import ArgumentParser
from pathlib import Path

import dotenv
from discord import Intents

from ciel import Ciel

if __name__ == "__main__":
    os.chdir(Path(__file__).parent)
    dotenv.load_dotenv()

    parser = ArgumentParser(description="Generic Discord Bot built with discord.py.")
    parser.add_argument("--sync", action="store_true", help="Sync Commands on Start-up.")
    parser.add_argument("--develop", action="store_true", help="Enable develop mode.")
    args = parser.parse_args()

    intents = Intents.default()
    intents.message_content = True
    bot = Ciel(intents=intents, sync=getattr(args, "sync", False), develop=getattr(args, "develop", False))
    bot.run()
