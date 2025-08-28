import os
from argparse import ArgumentParser

import dotenv
from discord import Intents

from ciel import Ciel

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    dotenv.load_dotenv()

    parser = ArgumentParser(description="Generic Discord Bot built with discord.py.")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode.")
    args = parser.parse_args()

    intents = Intents.default()
    intents.message_content = True
    bot = Ciel(intents=intents, debug=getattr(args, "debug", False))
    bot.run()
