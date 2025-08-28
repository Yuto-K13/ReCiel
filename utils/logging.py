import logging
import os

from discord import utils

logger = logging.getLogger("discord.ciel")


def setup_logging(debug=False):
    level = logging.DEBUG if debug else logging.INFO
    log_folder = os.getenv("LOG_FOLDER")
    if log_folder and os.path.isdir(log_folder):
        log_path = os.path.join(log_folder, "discord.log")
        handler = logging.FileHandler(log_path, encoding="utf-8")
        handler.setLevel(level)
        utils.setup_logging(handler=handler, level=logging.DEBUG)
        level = logging.INFO

    handler = logging.StreamHandler()
    handler.setLevel(level)
    utils.setup_logging(handler=handler, level=logging.DEBUG)
